from django.db import models
from django.conf import settings
from django.utils import timezone

class CorrectiveAction(models.Model):
    TYPE_CORRECTIVE = 'CORRECTIVE'
    TYPE_PREVENTIVE = 'PREVENTIVE'

    TYPE_CHOICES = [
        (TYPE_CORRECTIVE, 'Corrective Action (Immediate Hazard Rectification)'),
        (TYPE_PREVENTIVE, 'Preventive Action (Long-Term Systemic Defense)'),
    ]

    PRIORITY_LOW = 'LOW'
    PRIORITY_MEDIUM = 'MEDIUM'
    PRIORITY_HIGH = 'HIGH'
    PRIORITY_CRITICAL = 'CRITICAL'

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low Priority (SOP review within 60 days)'),
        (PRIORITY_MEDIUM, 'Medium Priority (Action required within 30 days)'),
        (PRIORITY_HIGH, 'High Priority (Mitigation required within 14 days)'),
        (PRIORITY_CRITICAL, 'Critical Priority (Immediate containment / 72 hours)'),
    ]

    STATUS_OPEN = 'OPEN'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_PENDING_VERIFICATION = 'PENDING_VERIFICATION'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open / Assigned'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_PENDING_VERIFICATION, 'Pending Verification & Sign-off'),
        (STATUS_COMPLETED, 'Completed & Verified'),
        (STATUS_CANCELLED, 'Cancelled / Supurceded'),
    ]

    incident = models.ForeignKey(
        'incidents.Incident',
        on_delete=models.CASCADE,
        related_name='corrective_actions'
    )
    investigation = models.ForeignKey(
        'investigations.Investigation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='corrective_actions'
    )
    action_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_CORRECTIVE)
    title = models.CharField(max_length=200, help_text="Concise title of corrective or preventive measure.")
    description = models.TextField(help_text="Detailed engineering, operational, or training instruction.")
    responsible_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='assigned_actions'
    )
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM, db_index=True)
    due_date = models.DateField(db_index=True)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default=STATUS_OPEN, db_index=True)

    # Completion Evidence
    completion_evidence = models.TextField(
        blank=True,
        default='',
        help_text="Factual evidence of implementation (e.g. bulletin number, training roster, work order ref)."
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_actions'
    )

    # Verification & Sign-off
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_actions'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(
        blank=True,
        default='',
        help_text="Safety Manager verification notes confirming barrier effectiveness."
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_actions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date', 'priority']
        verbose_name = 'Corrective & Preventive Action'
        verbose_name_plural = 'Corrective & Preventive Actions'
        indexes = [
            models.Index(fields=['status', 'due_date']),
            models.Index(fields=['responsible_user', 'status']),
        ]

    def __str__(self):
        return f"[{self.incident.reference_number}] {self.title} ({self.get_status_display()})"

    @property
    def is_overdue(self):
        """Returns True if action is past due and not finalized."""
        if self.status in [self.STATUS_COMPLETED, self.STATUS_CANCELLED]:
            return False
        return self.due_date < timezone.now().date()

    @property
    def status_badge_class(self):
        if self.is_overdue:
            return 'bg-danger text-white'
        badges = {
            self.STATUS_OPEN: 'bg-secondary',
            self.STATUS_IN_PROGRESS: 'bg-primary',
            self.STATUS_PENDING_VERIFICATION: 'bg-warning text-dark',
            self.STATUS_COMPLETED: 'bg-success',
            self.STATUS_CANCELLED: 'bg-dark',
        }
        return badges.get(self.status, 'bg-secondary')

    @property
    def priority_badge_class(self):
        badges = {
            self.PRIORITY_LOW: 'bg-info text-dark',
            self.PRIORITY_MEDIUM: 'bg-secondary',
            self.PRIORITY_HIGH: 'bg-warning text-dark',
            self.PRIORITY_CRITICAL: 'bg-danger text-white',
        }
        return badges.get(self.priority, 'bg-secondary')
