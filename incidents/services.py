from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Incident, IncidentStatusHistory
from audit.utils import log_audit_action

VALID_TRANSITIONS = {
    Incident.STATUS_REPORTED: [Incident.STATUS_UNDER_REVIEW, Incident.STATUS_CLOSED],
    Incident.STATUS_UNDER_REVIEW: [Incident.STATUS_INVESTIGATING, Incident.STATUS_ACTION_REQUIRED, Incident.STATUS_CLOSED],
    Incident.STATUS_INVESTIGATING: [Incident.STATUS_ACTION_REQUIRED, Incident.STATUS_PENDING_VERIFICATION, Incident.STATUS_UNDER_REVIEW],
    Incident.STATUS_ACTION_REQUIRED: [Incident.STATUS_PENDING_VERIFICATION, Incident.STATUS_INVESTIGATING],
    Incident.STATUS_PENDING_VERIFICATION: [Incident.STATUS_CLOSED, Incident.STATUS_ACTION_REQUIRED],
    Incident.STATUS_CLOSED: [Incident.STATUS_REOPENED],
    Incident.STATUS_REOPENED: [Incident.STATUS_UNDER_REVIEW, Incident.STATUS_INVESTIGATING],
}

def transition_incident_status(incident, to_status, user, notes='', force_override=False, request=None):
    """
    Executes a formal, audited state transition on an Incident record.
    Enforces business logic, permission gates, and closure integrity rules.
    """
    if to_status == incident.status:
        return incident

    # Role permission check: only Safety Managers and Admins can transition workflow states
    if not (user.is_safety_manager or user.is_administrator or user.is_superuser):
        raise ValidationError("Unauthorized: Only Safety Managers and Administrators can transition incident workflow status.")

    allowed_targets = VALID_TRANSITIONS.get(incident.status, [])
    if to_status not in allowed_targets and not user.is_administrator:
        raise ValidationError(
            f"Invalid state transition: Cannot change status directly from '{incident.get_status_display()}' to '{to_status}'."
        )

    # Closure Integrity Check
    if to_status == Incident.STATUS_CLOSED:
        can_close, reasons = incident.can_be_closed_safely
        if not can_close:
            if not force_override:
                raise ValidationError(
                    f"Closure Blocked: Cannot close incident while open requirements exist: {'; '.join(reasons)}"
                )
            else:
                notes = f"[MANAGEMENT OVERRIDE] {notes} | Justification required. Closure bypass executed by {user.username}."

    old_status = incident.status
    incident.status = to_status

    if to_status == Incident.STATUS_CLOSED:
        incident.closed_at = timezone.now()
        incident.closed_by = user
        incident.closure_notes = notes
    elif old_status == Incident.STATUS_CLOSED and to_status != Incident.STATUS_CLOSED:
        incident.closed_at = None
        incident.closed_by = None

    incident.save(update_fields=['status', 'closed_at', 'closed_by', 'closure_notes', 'updated_at'])

    # Record historical status change
    IncidentStatusHistory.objects.create(
        incident=incident,
        from_status=old_status,
        to_status=to_status,
        changed_by=user,
        notes=notes
    )

    # Audit logging
    log_audit_action(
        user=user,
        action='STATUS_CHANGE',
        entity_type='Incident',
        entity_id=str(incident.id),
        summary=f"Incident {incident.reference_number} status changed from {old_status} to {to_status}",
        details=notes,
        request=request
    )

    return incident
