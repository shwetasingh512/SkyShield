from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.decorators import role_required, admin_required
from audit.utils import log_audit_action
from incidents.models import Incident
from .models import RiskAssessment, RiskThresholdConfig
from .forms import RiskAssessmentForm, RiskThresholdConfigForm
from .services import get_risk_matrix

@login_required
@role_required(['SAFETY_MANAGER', 'INVESTIGATOR', 'ADMINISTRATOR'])
def risk_assessment_create_view(request, incident_id):
    incident = get_object_or_404(Incident, id=incident_id)

    # Permission check for investigator: can only assess if assigned to incident or manager
    if request.user.is_investigator and incident.assigned_investigator != request.user and not request.user.is_safety_manager:
        messages.error(request, "Permission Denied: You may only perform risk assessments on incidents assigned to you.")
        return redirect('incidents:detail', incident_id=incident.id)

    if request.method == 'POST':
        form = RiskAssessmentForm(request.POST)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.incident = incident
            assessment.assessor = request.user
            assessment.save()

            # Synchronize latest risk metrics to Incident record
            incident.risk_score = assessment.calculated_score
            incident.risk_level = assessment.risk_level
            incident.save(update_fields=['risk_score', 'risk_level', 'updated_at'])

            messages.success(
                request,
                f"Risk assessment recorded. Calculated Risk Score: {assessment.calculated_score} ({assessment.risk_level})."
            )
            log_audit_action(
                user=request.user,
                action='RISK_ASSESS',
                entity_type='Incident',
                entity_id=str(incident.id),
                summary=f"Risk assessed for {incident.reference_number}: Score {assessment.calculated_score} ({assessment.risk_level})",
                request=request
            )
            return redirect('incidents:detail', incident_id=incident.id)
    else:
        form = RiskAssessmentForm(initial={
            'likelihood': incident.initial_likelihood,
            'severity': incident.initial_severity,
            'assessment_type': 'REVIEW' if request.user.is_safety_manager else 'INVESTIGATION',
        })

    matrix_data = get_risk_matrix()
    return render(request, 'risk_assessments/risk_assessment_form.html', {
        'form': form,
        'incident': incident,
        'matrix_data': matrix_data,
    })

@login_required
def risk_matrix_view(request):
    matrix_data = get_risk_matrix()
    thresholds = RiskThresholdConfig.objects.all().order_by('min_score')
    return render(request, 'risk_assessments/matrix_view.html', {
        'matrix_data': matrix_data,
        'thresholds': thresholds,
    })

@login_required
@admin_required
def threshold_list_view(request):
    thresholds = RiskThresholdConfig.objects.all().order_by('min_score')
    return render(request, 'risk_assessments/threshold_list.html', {
        'thresholds': thresholds,
    })

@login_required
@admin_required
def threshold_edit_view(request, pk):
    config = get_object_or_404(RiskThresholdConfig, pk=pk)
    if request.method == 'POST':
        form = RiskThresholdConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, f"Risk band '{config.get_band_name_display()}' updated successfully.")
            log_audit_action(
                user=request.user,
                action='UPDATE',
                entity_type='RiskThresholdConfig',
                entity_id=str(config.id),
                summary=f"Admin updated risk threshold {config.band_name} to ({config.min_score}-{config.max_score})",
                request=request
            )
            return redirect('risk_assessments:threshold_list')
    else:
        form = RiskThresholdConfigForm(instance=config)

    return render(request, 'risk_assessments/threshold_form.html', {
        'form': form,
        'config': config,
    })
