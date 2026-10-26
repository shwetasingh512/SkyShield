from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from accounts.decorators import role_required, safety_manager_required
from audit.utils import log_audit_action
from incidents.models import Incident
from .models import Investigation, RootCauseAnalysis, ContributingFactor
from .forms import (
    InvestigationStartForm,
    InvestigationForm,
    InvestigationReviewForm,
    RootCauseAnalysisForm,
    ContributingFactorForm
)

@login_required
def investigation_workspace_view(request, incident_id):
    """
    Primary investigative workspace for documenting findings, 5-Whys, and contributing factors.
    """
    incident = get_object_or_404(
        Incident.objects.select_related('reporter', 'assigned_investigator'),
        id=incident_id
    )

    # Permission check: Reporter cannot access internal investigation workspace
    if request.user.is_reporter and not request.user.can_view_all_incidents:
        raise PermissionDenied("Reporters are not authorized to access internal investigation workspaces.")

    investigation = getattr(incident, 'investigation', None)

    # Check if user has permission to edit this investigation
    can_edit = False
    if investigation:
        if request.user.can_view_all_incidents or investigation.investigator == request.user:
            if investigation.status != Investigation.STATUS_APPROVED or request.user.is_safety_manager:
                can_edit = True

    # Forms
    start_form = InvestigationStartForm() if not investigation else None
    investigation_form = InvestigationForm(instance=investigation) if investigation else None
    review_form = InvestigationReviewForm(instance=investigation) if investigation else None
    factor_form = ContributingFactorForm()

    rca = getattr(investigation, 'root_cause_analysis', None) if investigation else None
    factors = investigation.contributing_factors.all() if investigation else []

    return render(request, 'investigations/investigation_workspace.html', {
        'incident': incident,
        'investigation': investigation,
        'rca': rca,
        'factors': factors,
        'can_edit': can_edit,
        'start_form': start_form,
        'investigation_form': investigation_form,
        'review_form': review_form,
        'factor_form': factor_form,
    })

@login_required
@role_required(['INVESTIGATOR', 'SAFETY_MANAGER', 'ADMINISTRATOR'])
def investigation_start_view(request, incident_id):
    """
    Initializes a new formal investigation workspace for an incident.
    """
    incident = get_object_or_404(Incident, id=incident_id)

    if hasattr(incident, 'investigation'):
        messages.info(request, "Investigation already initialized for this incident.")
        return redirect('investigations:workspace', incident_id=incident.id)

    if request.method == 'POST':
        form = InvestigationStartForm(request.POST)
        if form.is_valid():
            investigation = form.save(commit=False)
            investigation.incident = incident
            investigation.investigator = incident.assigned_investigator or request.user
            investigation.status = Investigation.STATUS_DRAFT
            investigation.save()

            # Transition incident to INVESTIGATING if not already
            if incident.status in [Incident.STATUS_REPORTED, Incident.STATUS_UNDER_REVIEW]:
                incident.status = Incident.STATUS_INVESTIGATING
                if not incident.assigned_investigator:
                    incident.assigned_investigator = investigation.investigator
                incident.save(update_fields=['status', 'assigned_investigator', 'updated_at'])

            messages.success(request, f"Investigation workspace created for incident #{incident.reference_number}.")
            log_audit_action(
                user=request.user,
                action='INVESTIGATION',
                entity_type='Investigation',
                entity_id=str(investigation.id),
                summary=f"Investigation opened for {incident.reference_number} by {request.user.username}",
                request=request
            )
            return redirect('investigations:workspace', incident_id=incident.id)
    else:
        form = InvestigationStartForm()

    return render(request, 'investigations/investigation_start.html', {
        'form': form,
        'incident': incident,
    })

@login_required
@role_required(['INVESTIGATOR', 'SAFETY_MANAGER', 'ADMINISTRATOR'])
def investigation_edit_view(request, incident_id):
    """
    Updates investigation findings, evidence reviewed, and proposed root causes.
    """
    incident = get_object_or_404(Incident, id=incident_id)
    investigation = get_object_or_404(Investigation, incident=incident)

    if not (request.user.can_view_all_incidents or investigation.investigator == request.user):
        raise PermissionDenied("You are not assigned to edit this investigation.")

    if request.method == 'POST':
        form = InvestigationForm(request.POST, instance=investigation)
        if form.is_valid():
            form.save()
            messages.success(request, "Investigation findings updated successfully.")
            log_audit_action(
                user=request.user,
                action='INVESTIGATION',
                entity_type='Investigation',
                entity_id=str(investigation.id),
                summary=f"Investigation findings updated for {incident.reference_number}",
                request=request
            )
            return redirect('investigations:workspace', incident_id=incident.id)
    else:
        form = InvestigationForm(instance=investigation)

    return render(request, 'investigations/investigation_edit.html', {
        'form': form,
        'incident': incident,
        'investigation': investigation,
    })

@login_required
@role_required(['INVESTIGATOR', 'SAFETY_MANAGER', 'ADMINISTRATOR'])
def investigation_submit_view(request, incident_id):
    """
    Investigator submits investigation for Safety Manager review.
    """
    if request.method != 'POST':
        return redirect('investigations:workspace', incident_id=incident_id)

    incident = get_object_or_404(Incident, id=incident_id)
    investigation = get_object_or_404(Investigation, incident=incident)

    investigation.status = Investigation.STATUS_SUBMITTED
    investigation.save(update_fields=['status', 'updated_at'])

    messages.success(request, "Investigation has been submitted for Safety Manager review.")
    log_audit_action(
        user=request.user,
        action='INVESTIGATION',
        entity_type='Investigation',
        entity_id=str(investigation.id),
        summary=f"Investigation for {incident.reference_number} submitted for review",
        request=request
    )

    return redirect('investigations:workspace', incident_id=incident.id)

@login_required
@safety_manager_required
def investigation_review_view(request, incident_id):
    """
    Safety Manager formal review: approves or returns investigation.
    """
    if request.method != 'POST':
        return redirect('investigations:workspace', incident_id=incident_id)

    incident = get_object_or_404(Incident, id=incident_id)
    investigation = get_object_or_404(Investigation, incident=incident)

    form = InvestigationReviewForm(request.POST, instance=investigation)
    if form.is_valid():
        inv = form.save(commit=False)
        inv.reviewed_by = request.user
        inv.reviewed_at = timezone.now()
        if inv.status == Investigation.STATUS_APPROVED:
            inv.completion_date = timezone.now().date()
            # If approved and CAPAs exist, transition incident to ACTION_REQUIRED
            if incident.corrective_actions.exists():
                incident.status = Incident.STATUS_ACTION_REQUIRED
            else:
                incident.status = Incident.STATUS_PENDING_VERIFICATION
            incident.save(update_fields=['status', 'updated_at'])
        inv.save()

        status_text = "Approved" if inv.status == Investigation.STATUS_APPROVED else "Returned for revisions"
        messages.success(request, f"Investigation has been {status_text}.")
        log_audit_action(
            user=request.user,
            action='INVESTIGATION',
            entity_type='Investigation',
            entity_id=str(inv.id),
            summary=f"Investigation review completed for {incident.reference_number}: {inv.status}",
            details=inv.review_comments,
            request=request
        )
    else:
        messages.error(request, "Error processing investigation review form.")

    return redirect('investigations:workspace', incident_id=incident.id)

@login_required
@role_required(['INVESTIGATOR', 'SAFETY_MANAGER', 'ADMINISTRATOR'])
def rca_edit_view(request, incident_id):
    """
    Creates or updates the 5 Whys Root Cause Analysis.
    """
    incident = get_object_or_404(Incident, id=incident_id)
    investigation = get_object_or_404(Investigation, incident=incident)

    rca = getattr(investigation, 'root_cause_analysis', None)

    if request.method == 'POST':
        form = RootCauseAnalysisForm(request.POST, instance=rca)
        if form.is_valid():
            rca_instance = form.save(commit=False)
            rca_instance.investigation = investigation
            rca_instance.save()

            messages.success(request, "5-Whys Root Cause Analysis saved successfully.")
            log_audit_action(
                user=request.user,
                action='RCA_ANALYSIS',
                entity_type='RootCauseAnalysis',
                entity_id=str(rca_instance.id),
                summary=f"5-Whys RCA updated for {incident.reference_number}",
                request=request
            )
            return redirect('investigations:workspace', incident_id=incident.id)
    else:
        initial_data = {}
        if not rca:
            initial_data['problem_statement'] = f"Safety incident #{incident.reference_number}: {incident.title} ({incident.location})"
        form = RootCauseAnalysisForm(instance=rca, initial=initial_data)

    return render(request, 'investigations/root_cause_analysis.html', {
        'form': form,
        'incident': incident,
        'investigation': investigation,
        'rca': rca,
    })

@login_required
@role_required(['INVESTIGATOR', 'SAFETY_MANAGER', 'ADMINISTRATOR'])
def contributing_factor_create_view(request, incident_id):
    """
    Adds a contributing factor to the investigation.
    """
    if request.method != 'POST':
        return redirect('investigations:workspace', incident_id=incident_id)

    incident = get_object_or_404(Incident, id=incident_id)
    investigation = get_object_or_404(Investigation, incident=incident)

    form = ContributingFactorForm(request.POST)
    if form.is_valid():
        factor = form.save(commit=False)
        factor.investigation = investigation
        factor.save()

        messages.success(request, f"Contributing factor '{factor.get_category_display()}' added.")
        log_audit_action(
            user=request.user,
            action='INVESTIGATION',
            entity_type='ContributingFactor',
            entity_id=str(factor.id),
            summary=f"Added contributing factor to {incident.reference_number} ({factor.category})",
            request=request
        )
    else:
        messages.error(request, "Could not add contributing factor. Please check inputs.")

    return redirect('investigations:workspace', incident_id=incident.id)

@login_required
@role_required(['INVESTIGATOR', 'SAFETY_MANAGER', 'ADMINISTRATOR'])
def contributing_factor_delete_view(request, factor_id):
    """
    Deletes a contributing factor.
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('dashboard:index')

    factor = get_object_or_404(ContributingFactor.objects.select_related('investigation__incident'), id=factor_id)
    incident_id = factor.investigation.incident.id

    factor.delete()
    messages.success(request, "Contributing factor deleted.")
    return redirect('investigations:workspace', incident_id=incident_id)
