import json
from datetime import timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timezone as datetime_timezone
from django.db.models import Count, Q
from incidents.models import Incident
from investigations.models import Investigation
from corrective_actions.models import CorrectiveAction
from audit.models import AuditLog

@login_required
def dashboard_view(request):
    """
    Main executive safety dashboard presenting real database analytics,
    KPI summary cards, and interactive Chart.js visualizations.
    """
    user = request.user
    now = timezone.now()
    today = now.date()

    # Base querysets respecting user authorization
    if user.can_view_all_incidents:
        incidents_qs = Incident.objects.all()
        investigations_qs = Investigation.objects.all()
        capa_qs = CorrectiveAction.objects.all()
        audit_qs = AuditLog.objects.select_related('user').all()
    elif user.is_investigator:
        incidents_qs = Incident.objects.filter(
            Q(assigned_investigator=user) | Q(reporter=user) | Q(status__in=[Incident.STATUS_INVESTIGATING, Incident.STATUS_UNDER_REVIEW])
        ).distinct()
        investigations_qs = Investigation.objects.filter(investigator=user)
        capa_qs = CorrectiveAction.objects.filter(Q(responsible_user=user) | Q(investigation__investigator=user)).distinct()
        audit_qs = AuditLog.objects.filter(user=user)
    else:
        # Reporter scope
        incidents_qs = Incident.objects.filter(reporter=user)
        investigations_qs = Investigation.objects.none()
        capa_qs = CorrectiveAction.objects.filter(responsible_user=user)
        audit_qs = AuditLog.objects.filter(user=user)

    # Date-range filter (optional for analytics widgets)
    days_param = request.GET.get('days', 'all').strip()
    filtered_incidents = incidents_qs
    if days_param.isdigit():
        num_days = int(days_param)
        cutoff_date = now - timedelta(days=num_days)
        filtered_incidents = incidents_qs.filter(occurrence_date__gte=cutoff_date)

    # KPI Metrics
    total_incidents = incidents_qs.count()
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_incidents = incidents_qs.filter(occurrence_date__gte=current_month_start).count()
    open_incidents = incidents_qs.exclude(status=Incident.STATUS_CLOSED).count()
    high_critical_risk = incidents_qs.filter(risk_level__in=['HIGH', 'CRITICAL']).count()
    investigations_in_progress = investigations_qs.filter(status__in=[Investigation.STATUS_DRAFT, Investigation.STATUS_SUBMITTED]).count()
    
    # Overdue Corrective Actions
    overdue_actions = capa_qs.filter(
        due_date__lt=today
    ).exclude(status__in=[CorrectiveAction.STATUS_COMPLETED, CorrectiveAction.STATUS_CANCELLED]).count()

    total_capas = capa_qs.count()
    completed_capas = capa_qs.filter(status=CorrectiveAction.STATUS_COMPLETED).count()
    capa_completion_rate = int((completed_capas / total_capas * 100)) if total_capas > 0 else 0

    # Recent Records
    recent_incidents = incidents_qs.select_related('reporter', 'assigned_investigator').order_by('-reported_at')[:6]
    recent_activity = audit_qs.order_by('-timestamp')[:6]
    pending_actions = capa_qs.select_related('incident', 'responsible_user').filter(
        status__in=[CorrectiveAction.STATUS_OPEN, CorrectiveAction.STATUS_IN_PROGRESS]
    ).order_by('due_date')[:5]

    # Chart 1: Trend over past 6 months
    trend_labels = []
    trend_data = []
    for i in range(5, -1, -1):
        # Calculate month intervals
        year = now.year
        month = now.month - i
        while month <= 0:
            month += 12
            year -= 1
        label = timezone.datetime(year, month, 1).strftime('%b %Y')
        trend_labels.append(label)

        # Count in month
        if month == 12:
            next_m = 1
            next_y = year + 1
        else:
            next_m = month + 1
            next_y = year
        m_start = timezone.datetime(year, month, 1, tzinfo=datetime_timezone.utc)
        m_end = timezone.datetime(next_y, next_m, 1, tzinfo=datetime_timezone.utc)
        cnt = incidents_qs.filter(occurrence_date__gte=m_start, occurrence_date__lt=m_end).count()
        trend_data.append(cnt)

    # Chart 2: Category Breakdown
    cat_counts = filtered_incidents.values('incident_type').annotate(count=Count('id')).order_by('-count')
    type_display_map = dict(Incident.TYPE_CHOICES)
    cat_labels = [str(type_display_map.get(item['incident_type'], item['incident_type'])) for item in cat_counts]
    cat_data = [item['count'] for item in cat_counts]

    # Chart 3: Severity Breakdown (1 to 5)
    sev_counts = filtered_incidents.values('initial_severity').annotate(count=Count('id')).order_by('initial_severity')
    sev_map = {item['initial_severity']: item['count'] for item in sev_counts}
    sev_labels = ['1-Negligible', '2-Minor', '3-Moderate', '4-Major', '5-Catastrophic']
    sev_data = [sev_map.get(i, 0) for i in range(1, 6)]

    # Chart 4: Workflow Status Breakdown
    status_counts = filtered_incidents.values('status').annotate(count=Count('id'))
    status_display_map = dict(Incident.STATUS_CHOICES)
    status_labels = [str(status_display_map.get(item['status'], item['status'])) for item in status_counts]
    status_data = [item['count'] for item in status_counts]

    context = {
        'total_incidents': total_incidents,
        'month_incidents': month_incidents,
        'open_incidents': open_incidents,
        'high_critical_risk': high_critical_risk,
        'investigations_in_progress': investigations_in_progress,
        'overdue_actions': overdue_actions,
        'total_capas': total_capas,
        'completed_capas': completed_capas,
        'capa_completion_rate': capa_completion_rate,
        'recent_incidents': recent_incidents,
        'recent_activity': recent_activity,
        'pending_actions': pending_actions,
        'days_param': days_param,

        # Chart Data serialized to JSON for Chart.js
        'trend_labels_json': json.dumps(trend_labels),
        'trend_data_json': json.dumps(trend_data),
        'cat_labels_json': json.dumps(cat_labels),
        'cat_data_json': json.dumps(cat_data),
        'sev_labels_json': json.dumps(sev_labels),
        'sev_data_json': json.dumps(sev_data),
        'status_labels_json': json.dumps(status_labels),
        'status_data_json': json.dumps(status_data),
    }

    return render(request, 'dashboard/dashboard.html', context)
