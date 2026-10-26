import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import FileResponse, Http404
from django.utils.dateparse import parse_date

from .models import Incident, IncidentAttachment, IncidentStatusHistory
from .forms import (
    IncidentReportForm,
    IncidentEditForm,
    IncidentAssignInvestigatorForm,
    IncidentTransitionForm,
    IncidentAttachmentForm
)
from .services import transition_incident_status
from risk_assessments.services import get_risk_matrix
from audit.utils import log_audit_action

@login_required
def incident_list_view(request):
    """
    Searchable, filterable, and paginated incident register.
    Applies server-side role scoping.
    """
    user = request.user

    # Base Queryset scoped by role
    if user.can_view_all_incidents:
        queryset = Incident.objects.select_related('reporter', 'assigned_investigator').all()
    elif user.is_investigator:
        # Investigator sees assigned incidents or open investigations
        queryset = Incident.objects.select_related('reporter', 'assigned_investigator').filter(
            Q(assigned_investigator=user) | Q(reporter=user) | Q(status__in=[Incident.STATUS_INVESTIGATING, Incident.STATUS_UNDER_REVIEW])
        ).distinct()
    else:
        # Reporter only views submissions they created
        queryset = Incident.objects.select_related('reporter', 'assigned_investigator').filter(reporter=user)

    # Search query
    q = request.GET.get('q', '').strip()
    if q:
        queryset = queryset.filter(
            Q(reference_number__icontains=q) |
            Q(title__icontains=q) |
            Q(location__icontains=q) |
            Q(description__icontains=q) |
            Q(aircraft_registration__icontains=q) |
            Q(flight_number__icontains=q)
        )

    # Filters
    category_filter = request.GET.get('category', '').strip()
    if category_filter:
        queryset = queryset.filter(incident_type=category_filter)

    severity_filter = request.GET.get('severity', '').strip()
    if severity_filter:
        queryset = queryset.filter(initial_severity=severity_filter)

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    risk_filter = request.GET.get('risk_level', '').strip()
    if risk_filter:
        queryset = queryset.filter(risk_level=risk_filter)

    date_from = request.GET.get('date_from', '').strip()
    if date_from:
        d_from = parse_date(date_from)
        if d_from:
            queryset = queryset.filter(occurrence_date__date__gte=d_from)

    date_to = request.GET.get('date_to', '').strip()
    if date_to:
        d_to = parse_date(date_to)
        if d_to:
            queryset = queryset.filter(occurrence_date__date__lte=d_to)

    # Sorting
    sort_by = request.GET.get('sort', '-occurrence_date').strip()
    allowed_sorts = ['-occurrence_date', 'occurrence_date', '-risk_score', 'risk_score', '-reported_at', 'status']
    if sort_by in allowed_sorts:
        queryset = queryset.order_by(sort_by)
    else:
        queryset = queryset.order_by('-occurrence_date')

    # Pagination
    paginator = Paginator(queryset, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'incidents/incident_list.html', {
        'page_obj': page_obj,
        'search_query': q,
        'category_filter': category_filter,
        'severity_filter': severity_filter,
        'status_filter': status_filter,
        'risk_filter': risk_filter,
        'date_from': date_from,
        'date_to': date_to,
        'sort_by': sort_by,
        'type_choices': Incident.TYPE_CHOICES,
        'severity_choices': Incident.SEVERITY_CHOICES,
        'status_choices': Incident.STATUS_CHOICES,
        'total_count': queryset.count(),
    })

@login_required
def incident_create_view(request):
    """
    Submits a new aviation incident or hazard report.
    Available to all authenticated users.
    """
    if request.method == 'POST':
        form = IncidentReportForm(request.POST)
        attachment_form = IncidentAttachmentForm(request.POST, request.FILES)

        if form.is_valid():
            incident = form.save(commit=False)
            incident.reporter = request.user
            incident.save()

            # Handle optional initial attachment
            if 'file' in request.FILES and attachment_form.is_valid():
                uploaded_file = request.FILES['file']
                IncidentAttachment.objects.create(
                    incident=incident,
                    file=uploaded_file,
                    filename=uploaded_file.name,
                    file_size=uploaded_file.size,
                    file_type=uploaded_file.content_type,
                    description=attachment_form.cleaned_data.get('description', 'Initial submission attachment'),
                    uploaded_by=request.user
                )

            # Record initial status history
            IncidentStatusHistory.objects.create(
                incident=incident,
                from_status='NONE',
                to_status=incident.status,
                changed_by=request.user,
                notes="Initial incident report submission into SkyShield."
            )

            log_audit_action(
                user=request.user,
                action='CREATE',
                entity_type='Incident',
                entity_id=str(incident.id),
                summary=f"Incident {incident.reference_number} reported: '{incident.title}' (Risk: {incident.risk_level})",
                request=request
            )

            messages.success(
                request,
                f"Incident successfully reported with Reference #{incident.reference_number}. "
                f"Initial Risk: {incident.risk_level} (Score: {incident.risk_score})."
            )
            return redirect('incidents:detail', incident_id=incident.id)
        else:
            messages.error(request, "Please correct the highlighted validation errors below.")
    else:
        form = IncidentReportForm()
        attachment_form = IncidentAttachmentForm()

    return render(request, 'incidents/incident_form.html', {
        'form': form,
        'attachment_form': attachment_form,
        'is_create': True,
    })

@login_required
def incident_detail_view(request, incident_id):
    """
    Comprehensive dossier view of an incident, including risk matrix,
    investigation status, CAPA actions, evidence attachments, and audit timeline.
    """
    incident = get_object_or_404(
        Incident.objects.select_related('reporter', 'assigned_investigator', 'closed_by'),
        id=incident_id
    )

    # Permission check
    if not request.user.can_view_all_incidents:
        if request.user.is_reporter and incident.reporter != request.user:
            raise PermissionDenied("You are not authorized to view this incident report.")
        if request.user.is_investigator and incident.assigned_investigator != request.user and incident.reporter != request.user:
            raise PermissionDenied("You are not assigned to investigate this incident.")

    attachments = incident.attachments.select_related('uploaded_by').all()
    status_history = incident.status_history.select_related('changed_by').all()
    risk_assessments = incident.risk_assessments.select_related('assessor').all()
    corrective_actions = incident.corrective_actions.select_related('responsible_user', 'verified_by').all()

    # Form for adding attachments
    attachment_form = IncidentAttachmentForm()

    # Form for assigning investigator (Managers/Admins)
    assign_form = IncidentAssignInvestigatorForm(instance=incident)

    # Form for workflow transition
    transition_form = IncidentTransitionForm(initial={'to_status': incident.status})

    # Matrix data for visual risk coordinate display
    matrix_data = get_risk_matrix()
    can_close, closure_reasons = incident.can_be_closed_safely

    return render(request, 'incidents/incident_detail.html', {
        'incident': incident,
        'attachments': attachments,
        'status_history': status_history,
        'risk_assessments': risk_assessments,
        'corrective_actions': corrective_actions,
        'attachment_form': attachment_form,
        'assign_form': assign_form,
        'transition_form': transition_form,
        'matrix_data': matrix_data,
        'can_close': can_close,
        'closure_reasons': closure_reasons,
    })

@login_required
def incident_edit_view(request, incident_id):
    """
    Allows modifying an incident subject to permissions and workflow status.
    """
    incident = get_object_or_404(Incident, id=incident_id)

    # Authorization
    is_owner = (incident.reporter == request.user)
    can_manage = request.user.can_view_all_incidents

    if not (is_owner or can_manage):
        raise PermissionDenied("You do not have permission to edit this incident report.")

    # A reporter can only edit if report is still in early triage
    if is_owner and not can_manage:
        if incident.status not in [Incident.STATUS_REPORTED, Incident.STATUS_UNDER_REVIEW]:
            messages.error(request, "This incident is already actively investigating or processed. Further modifications are locked.")
            return redirect('incidents:detail', incident_id=incident.id)

    if request.method == 'POST':
        form = IncidentEditForm(request.POST, instance=incident)
        if form.is_valid():
            form.save()
            messages.success(request, f"Incident #{incident.reference_number} has been updated successfully.")
            log_audit_action(
                user=request.user,
                action='UPDATE',
                entity_type='Incident',
                entity_id=str(incident.id),
                summary=f"Incident {incident.reference_number} details edited by {request.user.username}",
                request=request
            )
            return redirect('incidents:detail', incident_id=incident.id)
    else:
        form = IncidentEditForm(instance=incident)

    return render(request, 'incidents/incident_form.html', {
        'form': form,
        'incident': incident,
        'is_create': False,
    })

@login_required
def incident_transition_view(request, incident_id):
    """
    Processes workflow status change with server-side validation.
    """
    if request.method != 'POST':
        return redirect('incidents:detail', incident_id=incident_id)

    incident = get_object_or_404(Incident, id=incident_id)
    form = IncidentTransitionForm(request.POST)

    if form.is_valid():
        to_status = form.cleaned_data['to_status']
        notes = form.cleaned_data['notes']
        force_override = form.cleaned_data.get('force_override', False)

        try:
            transition_incident_status(
                incident=incident,
                to_status=to_status,
                user=request.user,
                notes=notes,
                force_override=force_override,
                request=request
            )
            messages.success(request, f"Incident status transitioned to '{incident.get_status_display()}'.")
        except ValidationError as e:
            messages.error(request, str(e.message if hasattr(e, 'message') else e))
    else:
        messages.error(request, "Invalid status transition request.")

    return redirect('incidents:detail', incident_id=incident.id)

@login_required
def incident_assign_investigator_view(request, incident_id):
    """
    Safety Manager or Administrator assigns an investigator to an incident.
    """
    if request.method != 'POST':
        return redirect('incidents:detail', incident_id=incident_id)

    if not request.user.can_assign_investigators:
        raise PermissionDenied("Only Safety Managers and Administrators can assign investigators.")

    incident = get_object_or_404(Incident, id=incident_id)
    form = IncidentAssignInvestigatorForm(request.POST, instance=incident)

    if form.is_valid():
        investigator = form.cleaned_data['assigned_investigator']
        incident.assigned_investigator = investigator
        if incident.status == Incident.STATUS_REPORTED:
            incident.status = Incident.STATUS_UNDER_REVIEW
        incident.save(update_fields=['assigned_investigator', 'status', 'updated_at'])

        messages.success(request, f"Assigned investigator: {investigator.get_full_name() or investigator.username}.")
        log_audit_action(
            user=request.user,
            action='UPDATE',
            entity_type='Incident',
            entity_id=str(incident.id),
            summary=f"Investigator {investigator.username} assigned to {incident.reference_number}",
            request=request
        )
    else:
        messages.error(request, "Failed to assign investigator. Please select an active investigator.")

    return redirect('incidents:detail', incident_id=incident.id)

@login_required
def attachment_upload_view(request, incident_id):
    """
    Uploads supporting evidence attachment to an existing incident.
    """
    incident = get_object_or_404(Incident, id=incident_id)

    # Permission check: must be allowed to view the incident
    if not request.user.can_view_all_incidents:
        if request.user.is_reporter and incident.reporter != request.user:
            raise PermissionDenied("You are not permitted to add evidence to this incident.")
        if request.user.is_investigator and incident.assigned_investigator != request.user:
            raise PermissionDenied("You are not permitted to add evidence to this incident.")

    if request.method == 'POST':
        form = IncidentAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['file']
            attachment = form.save(commit=False)
            attachment.incident = incident
            attachment.filename = uploaded_file.name
            attachment.file_size = uploaded_file.size
            attachment.file_type = getattr(uploaded_file, 'content_type', 'application/octet-stream')
            attachment.uploaded_by = request.user
            attachment.save()

            messages.success(request, f"Evidence file '{attachment.filename}' uploaded successfully.")
            log_audit_action(
                user=request.user,
                action='UPDATE',
                entity_type='IncidentAttachment',
                entity_id=str(attachment.id),
                summary=f"Evidence '{attachment.filename}' uploaded to {incident.reference_number}",
                request=request
            )
        else:
            for error in form.errors.values():
                messages.error(request, error)

    return redirect('incidents:detail', incident_id=incident.id)

@login_required
def attachment_download_view(request, attachment_id):
    """
    Secure download handler ensuring permission checks before serving files.
    """
    attachment = get_object_or_404(IncidentAttachment.objects.select_related('incident'), id=attachment_id)
    incident = attachment.incident

    # Permission check
    if not request.user.can_view_all_incidents:
        if request.user.is_reporter and incident.reporter != request.user:
            raise PermissionDenied("Access denied to requested evidence file.")
        if request.user.is_investigator and incident.assigned_investigator != request.user:
            raise PermissionDenied("Access denied to requested evidence file.")

    if not attachment.file or not os.path.exists(attachment.file.path):
        raise Http404("Requested evidence file could not be found on storage.")

    log_audit_action(
        user=request.user,
        action='EXPORT',
        entity_type='IncidentAttachment',
        entity_id=str(attachment.id),
        summary=f"Evidence '{attachment.filename}' downloaded by {request.user.username}",
        request=request
    )

    return FileResponse(open(attachment.file.path, 'rb'), as_attachment=True, filename=attachment.filename)

@login_required
def attachment_delete_view(request, attachment_id):
    """
    Deletes an attachment (Manager, Admin, or original uploader).
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('incidents:list')

    attachment = get_object_or_404(IncidentAttachment.objects.select_related('incident'), id=attachment_id)
    incident_id = attachment.incident.id

    if not (request.user.can_view_all_incidents or attachment.uploaded_by == request.user):
        raise PermissionDenied("You are not authorized to delete this attachment.")

    filename = attachment.filename
    attachment.file.delete(save=False)
    attachment.delete()

    messages.success(request, f"Evidence attachment '{filename}' deleted.")
    log_audit_action(
        user=request.user,
        action='UPDATE',
        entity_type='IncidentAttachment',
        entity_id=str(attachment_id),
        summary=f"Attachment '{filename}' removed from incident",
        request=request
    )

    return redirect('incidents:detail', incident_id=incident_id)
