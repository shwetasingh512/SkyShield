from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.utils import timezone

from accounts.decorators import role_required, safety_manager_required
from audit.utils import log_audit_action
from incidents.models import Incident
from .models import CorrectiveAction
from .forms import (
    CorrectiveActionCreateForm,
    CorrectiveActionProgressForm,
    CorrectiveActionVerifyForm
)

@login_required
def capa_list_view(request):
    """
    Overview list of all corrective and preventive actions.
    Supports filters for Overdue, Priority, Status, and Assignee.
    """
    user = request.user
    queryset = CorrectiveAction.objects.select_related('incident', 'responsible_user', 'verified_by').all()

    # Scoping: If user is not manager/admin/investigator, show only actions assigned to them
    if not (user.can_view_all_incidents or user.is_investigator):
        queryset = queryset.filter(responsible_user=user)

    # Search
    q = request.GET.get('q', '').strip()
    if q:
        queryset = queryset.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(incident__reference_number__icontains=q) |
            Q(responsible_user__username__icontains=q)
        )

    # Status filter
    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    # Priority filter
    priority_filter = request.GET.get('priority', '').strip()
    if priority_filter:
        queryset = queryset.filter(priority=priority_filter)

    # Overdue filter
    overdue_only = request.GET.get('overdue', '').strip() == '1'
    if overdue_only:
        queryset = queryset.filter(
            due_date__lt=timezone.now().date()
        ).exclude(status__in=[CorrectiveAction.STATUS_COMPLETED, CorrectiveAction.STATUS_CANCELLED])

    # Assignee filter
    assigned_to = request.GET.get('assigned_to', '').strip()
    if assigned_to == 'me':
        queryset = queryset.filter(responsible_user=user)

    paginator = Paginator(queryset, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'corrective_actions/capa_list.html', {
        'page_obj': page_obj,
        'search_query': q,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'overdue_only': overdue_only,
        'assigned_to': assigned_to,
        'status_choices': CorrectiveAction.STATUS_CHOICES,
        'priority_choices': CorrectiveAction.PRIORITY_CHOICES,
        'total_count': queryset.count(),
    })

@login_required
@role_required(['INVESTIGATOR', 'SAFETY_MANAGER', 'ADMINISTRATOR'])
def capa_create_view(request, incident_id):
    """
    Creates a new CAPA tied to an incident.
    """
    incident = get_object_or_404(Incident, id=incident_id)

    if request.method == 'POST':
        form = CorrectiveActionCreateForm(request.POST)
        if form.is_valid():
            action = form.save(commit=False)
            action.incident = incident
            action.investigation = getattr(incident, 'investigation', None)
            action.created_by = request.user
            action.save()

            # Ensure incident status reflects active actions needed
            if incident.status in [Incident.STATUS_REPORTED, Incident.STATUS_UNDER_REVIEW, Incident.STATUS_INVESTIGATING]:
                incident.status = Incident.STATUS_ACTION_REQUIRED
                incident.save(update_fields=['status', 'updated_at'])

            messages.success(request, f"Corrective Action '{action.title}' assigned to {action.responsible_user.username}.")
            log_audit_action(
                user=request.user,
                action='CAPA_ASSIGN',
                entity_type='CorrectiveAction',
                entity_id=str(action.id),
                summary=f"CAPA '{action.title}' created for {incident.reference_number} assigned to {action.responsible_user.username}",
                request=request
            )
            return redirect('incidents:detail', incident_id=incident.id)
    else:
        form = CorrectiveActionCreateForm()

    return render(request, 'corrective_actions/capa_form.html', {
        'form': form,
        'incident': incident,
    })

@login_required
def capa_detail_view(request, action_id):
    """
    Detailed view of a corrective action.
    """
    action = get_object_or_404(
        CorrectiveAction.objects.select_related('incident', 'investigation', 'responsible_user', 'created_by', 'verified_by', 'completed_by'),
        id=action_id
    )

    can_update = (action.responsible_user == request.user or request.user.can_view_all_incidents)
    can_verify = request.user.can_manage_capa and request.user.is_safety_manager

    progress_form = CorrectiveActionProgressForm(instance=action) if can_update else None
    verify_form = CorrectiveActionVerifyForm() if can_verify else None

    return render(request, 'corrective_actions/capa_detail.html', {
        'action': action,
        'incident': action.incident,
        'can_update': can_update,
        'can_verify': can_verify,
        'progress_form': progress_form,
        'verify_form': verify_form,
    })

@login_required
def capa_update_progress_view(request, action_id):
    """
    Responsible assignee updates progress or submits completion evidence.
    """
    if request.method != 'POST':
        return redirect('corrective_actions:detail', action_id=action_id)

    action = get_object_or_404(CorrectiveAction, id=action_id)

    # Permission check: responsible user, investigator, or manager
    if not (action.responsible_user == request.user or request.user.can_manage_capa):
        raise PermissionDenied("You are not assigned to execute this corrective action.")

    form = CorrectiveActionProgressForm(request.POST, instance=action)
    if form.is_valid():
        act = form.save(commit=False)
        if act.status == CorrectiveAction.STATUS_PENDING_VERIFICATION:
            act.completed_at = timezone.now()
            act.completed_by = request.user
        act.save()

        messages.success(request, f"Progress updated for '{action.title}'. Status: {act.get_status_display()}.")
        log_audit_action(
            user=request.user,
            action='CAPA_STATUS',
            entity_type='CorrectiveAction',
            entity_id=str(action.id),
            summary=f"CAPA {action.id} status updated to {act.status} by {request.user.username}",
            request=request
        )
    else:
        messages.error(request, "Failed to update progress. Please check inputs.")

    return redirect('corrective_actions:detail', action_id=action.id)

@login_required
@safety_manager_required
def capa_verify_view(request, action_id):
    """
    Safety Manager verifies completion of action and marks it COMPLETED or returns for rework.
    """
    if request.method != 'POST':
        return redirect('corrective_actions:detail', action_id=action_id)

    action = get_object_or_404(CorrectiveAction, id=action_id)
    form = CorrectiveActionVerifyForm(request.POST)

    if form.is_valid():
        decision = form.cleaned_data['decision']
        notes = form.cleaned_data['verification_notes']

        action.verified_by = request.user
        action.verified_at = timezone.now()
        action.verification_notes = notes

        if decision == 'APPROVE':
            action.status = CorrectiveAction.STATUS_COMPLETED
            messages.success(request, f"Corrective Action '{action.title}' verified and marked COMPLETED.")
        else:
            action.status = CorrectiveAction.STATUS_IN_PROGRESS
            messages.warning(request, f"Corrective Action '{action.title}' rejected and returned for rework.")

        action.save()

        log_audit_action(
            user=request.user,
            action='CAPA_VERIFY',
            entity_type='CorrectiveAction',
            entity_id=str(action.id),
            summary=f"CAPA {action.id} verification completed: {decision}",
            details=notes,
            request=request
        )
    else:
        messages.error(request, "Verification form validation error.")

    return redirect('corrective_actions:detail', action_id=action.id)
