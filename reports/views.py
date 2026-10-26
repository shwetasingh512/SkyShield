import csv
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import Q
from accounts.decorators import role_required, safety_manager_required
from incidents.models import Incident
from corrective_actions.models import CorrectiveAction
from audit.models import AuditLog
from audit.utils import log_audit_action
from .pdf_generator import generate_incident_pdf_report

@login_required
def reports_index_view(request):
    """
    Reporting center for generating compliance dossiers, analytical exports, and audit trails.
    """
    total_incidents = Incident.objects.count() if request.user.can_view_all_incidents else Incident.objects.filter(reporter=request.user).count()
    total_capas = CorrectiveAction.objects.count() if request.user.can_view_all_incidents else CorrectiveAction.objects.filter(responsible_user=request.user).count()

    return render(request, 'reports/reports_index.html', {
        'total_incidents': total_incidents,
        'total_capas': total_capas,
    })

@login_required
def export_incidents_csv(request):
    """
    Exports incidents into standard CSV format applying user-selected filters and role permissions.
    """
    user = request.user
    if user.can_view_all_incidents:
        queryset = Incident.objects.select_related('reporter', 'assigned_investigator').all()
    elif user.is_investigator:
        queryset = Incident.objects.select_related('reporter', 'assigned_investigator').filter(
            Q(assigned_investigator=user) | Q(reporter=user)
        )
    else:
        queryset = Incident.objects.select_related('reporter').filter(reporter=user)

    # Optional category/status filter
    cat = request.GET.get('category')
    status = request.GET.get('status')
    if cat:
        queryset = queryset.filter(incident_type=cat)
    if status:
        queryset = queryset.filter(status=status)

    response = HttpResponse(content_type='text/csv')
    timestamp_str = timezone.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'attachment; filename="SkyShield_Incidents_{timestamp_str}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Reference Number', 'Title', 'Category', 'Status',
        'Occurrence Date (UTC)', 'Reported Date (UTC)', 'Location',
        'Aircraft Reg', 'Flight No', 'Severity (1-5)', 'Likelihood (1-5)',
        'Risk Score', 'Risk Level', 'Reporter', 'Investigator',
        'Description', 'Immediate Actions', 'Actual Consequences'
    ])

    for inc in queryset:
        writer.writerow([
            inc.reference_number,
            inc.title,
            inc.get_incident_type_display(),
            inc.get_status_display(),
            inc.occurrence_date.strftime('%Y-%m-%d %H:%M:%S'),
            inc.reported_at.strftime('%Y-%m-%d %H:%M:%S'),
            inc.location,
            inc.aircraft_registration or '',
            inc.flight_number or '',
            inc.initial_severity,
            inc.initial_likelihood,
            inc.risk_score,
            inc.risk_level,
            inc.reporter.username,
            inc.assigned_investigator.username if inc.assigned_investigator else 'Unassigned',
            inc.description,
            inc.immediate_actions_taken,
            inc.actual_consequences,
        ])

    log_audit_action(
        user=user,
        action='EXPORT',
        entity_type='Incident',
        summary=f"User {user.username} exported {queryset.count()} incidents to CSV",
        request=request
    )
    return response

@login_required
def export_capa_csv(request):
    """
    Exports Corrective and Preventive Actions into CSV.
    """
    user = request.user
    if user.can_view_all_incidents or user.is_investigator:
        queryset = CorrectiveAction.objects.select_related('incident', 'responsible_user', 'verified_by').all()
    else:
        queryset = CorrectiveAction.objects.select_related('incident', 'responsible_user').filter(responsible_user=user)

    response = HttpResponse(content_type='text/csv')
    timestamp_str = timezone.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'attachment; filename="SkyShield_CAPA_{timestamp_str}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Action ID', 'Incident Ref', 'Action Type', 'Title', 'Priority',
        'Due Date', 'Status', 'Is Overdue', 'Responsible User', 'Completion Evidence',
        'Completed At', 'Verified By', 'Created At'
    ])

    for c in queryset:
        writer.writerow([
            c.id,
            c.incident.reference_number,
            c.get_action_type_display(),
            c.title,
            c.get_priority_display(),
            str(c.due_date),
            c.get_status_display(),
            'YES' if c.is_overdue else 'NO',
            c.responsible_user.username,
            c.completion_evidence,
            c.completed_at.strftime('%Y-%m-%d %H:%M:%S') if c.completed_at else '',
            c.verified_by.username if c.verified_by else '',
            c.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])

    log_audit_action(
        user=user,
        action='EXPORT',
        entity_type='CorrectiveAction',
        summary=f"User {user.username} exported {queryset.count()} CAPA items to CSV",
        request=request
    )
    return response

@login_required
@safety_manager_required
def export_audit_csv(request):
    """
    Exports system audit log for compliance review.
    """
    queryset = AuditLog.objects.select_related('user').all()[:1000]

    response = HttpResponse(content_type='text/csv')
    timestamp_str = timezone.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'attachment; filename="SkyShield_AuditLog_{timestamp_str}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Timestamp (UTC)', 'User', 'Action', 'Entity Type', 'Entity ID', 'Summary', 'IP Address'])

    for log in queryset:
        writer.writerow([
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.user.username if log.user else 'System',
            log.action,
            log.entity_type,
            log.entity_id,
            log.summary,
            log.ip_address or '',
        ])

    log_audit_action(
        user=request.user,
        action='EXPORT',
        entity_type='AuditLog',
        summary=f"Audit log CSV export executed by {request.user.username}",
        request=request
    )
    return response

@login_required
def export_incident_pdf(request, incident_id):
    """
    Generates and downloads formal incident dossier PDF.
    """
    incident = get_object_or_404(
        Incident.objects.select_related('reporter', 'assigned_investigator', 'closed_by'),
        id=incident_id
    )

    # Permission check
    if not request.user.can_view_all_incidents:
        if request.user.is_reporter and incident.reporter != request.user:
            raise PermissionDenied("You are not authorized to export this incident dossier.")
        if request.user.is_investigator and incident.assigned_investigator != request.user and incident.reporter != request.user:
            raise PermissionDenied("You are not authorized to export this incident dossier.")

    pdf_bytes = generate_incident_pdf_report(incident)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="SkyShield_Report_{incident.reference_number}.pdf"'

    log_audit_action(
        user=request.user,
        action='EXPORT',
        entity_type='Incident',
        entity_id=str(incident.id),
        summary=f"PDF Dossier generated for {incident.reference_number} by {request.user.username}",
        request=request
    )
    return response
