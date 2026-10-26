from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from accounts.decorators import role_required
from .models import AuditLog

@login_required
@role_required(['SAFETY_MANAGER', 'ADMINISTRATOR'])
def audit_log_list_view(request):
    search_query = request.GET.get('q', '').strip()
    action_filter = request.GET.get('action', '').strip()
    entity_filter = request.GET.get('entity', '').strip()

    logs = AuditLog.objects.select_related('user').all()

    if search_query:
        logs = logs.filter(
            Q(summary__icontains=search_query) |
            Q(details__icontains=search_query) |
            Q(entity_id__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )

    if action_filter:
        logs = logs.filter(action=action_filter)

    if entity_filter:
        logs = logs.filter(entity_type=entity_filter)

    paginator = Paginator(logs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'audit/audit_log.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'action_filter': action_filter,
        'entity_filter': entity_filter,
        'action_choices': AuditLog.ACTION_CHOICES,
    })
