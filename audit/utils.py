from .models import AuditLog

def get_client_ip(request):
    """Safely extracts real client IP address from HTTP headers."""
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_audit_action(user, action, entity_type, entity_id='', summary='', details='', request=None):
    """
    Standard utility to record a structured, immutable audit log entry.
    """
    ip = get_client_ip(request) if request else None
    try:
        return AuditLog.objects.create(
            user=user if user and user.is_authenticated else None,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            summary=summary[:255],
            details=str(details),
            ip_address=ip
        )
    except Exception as e:
        # Fallback to prevent breaking primary workflow if audit logging fails
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to record audit log: {e}")
        return None
