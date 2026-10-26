from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Created Record'),
        ('UPDATE', 'Updated Record'),
        ('STATUS_CHANGE', 'Status Transition'),
        ('DELETE_ATTEMPT', 'Deletion Attempt'),
        ('RISK_ASSESS', 'Risk Assessment Recorded'),
        ('INVESTIGATION', 'Investigation Updated'),
        ('RCA_ANALYSIS', '5-Whys RCA Completed'),
        ('CAPA_ASSIGN', 'CAPA Assigned'),
        ('CAPA_STATUS', 'CAPA Status Change'),
        ('CAPA_VERIFY', 'CAPA Verified'),
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('EXPORT', 'Data Export / Report Generated'),
        ('SECURITY_VIOLATION', 'Security / Permission Violation'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_entries'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, db_index=True)
    entity_type = models.CharField(max_length=50, db_index=True)
    entity_id = models.CharField(max_length=50, blank=True, db_index=True)
    summary = models.CharField(max_length=255)
    details = models.TextField(blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log Entry'
        verbose_name_plural = 'Audit Log Entries'
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['action', 'timestamp']),
        ]

    def __str__(self):
        actor = self.user.username if self.user else 'System'
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {actor} - {self.action}: {self.summary}"
