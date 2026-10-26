import os
import secrets
import string
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from risk_assessments.services import calculate_score_and_level

class Incident(models.Model):
    # Incident Categories
    TYPE_RUNWAY_INCURSION = 'RUNWAY_INCURSION'
    TYPE_BIRD_STRIKE = 'BIRD_STRIKE'
    TYPE_MAINTENANCE_ISSUE = 'MAINTENANCE_ISSUE'
    TYPE_EQUIPMENT_FAILURE = 'EQUIPMENT_FAILURE'
    TYPE_GROUND_HANDLING = 'GROUND_HANDLING'
    TYPE_HUMAN_FACTORS = 'HUMAN_FACTORS'
    TYPE_NEAR_MISS = 'NEAR_MISS'
    TYPE_HAZARD_REPORT = 'HAZARD_REPORT'
    TYPE_PROCEDURE_DEVIATION = 'PROCEDURE_DEVIATION'
    TYPE_OTHER = 'OTHER'

    TYPE_CHOICES = [
        (TYPE_RUNWAY_INCURSION, 'Runway Incursion'),
        (TYPE_BIRD_STRIKE, 'Bird Strike / Wildlife Hazard'),
        (TYPE_MAINTENANCE_ISSUE, 'Maintenance & Tech Discrepancy'),
        (TYPE_EQUIPMENT_FAILURE, 'Avionics / Ground Equipment Failure'),
        (TYPE_GROUND_HANDLING, 'Ground Handling & Ramp Incident'),
        (TYPE_HUMAN_FACTORS, 'Human Factors & Fatigue'),
        (TYPE_NEAR_MISS, 'Airborne Near Miss / TCAS Alert'),
        (TYPE_HAZARD_REPORT, 'Proactive Safety Hazard Report'),
        (TYPE_PROCEDURE_DEVIATION, 'Operational SOP Deviation'),
        (TYPE_OTHER, 'Other Operational Occurrence'),
    ]

    # Workflow Statuses
    STATUS_REPORTED = 'REPORTED'
    STATUS_UNDER_REVIEW = 'UNDER_REVIEW'
    STATUS_INVESTIGATING = 'INVESTIGATING'
    STATUS_ACTION_REQUIRED = 'ACTION_REQUIRED'
    STATUS_PENDING_VERIFICATION = 'PENDING_VERIFICATION'
    STATUS_CLOSED = 'CLOSED'
    STATUS_REOPENED = 'REOPENED'

    STATUS_CHOICES = [
        (STATUS_REPORTED, 'Reported'),
        (STATUS_UNDER_REVIEW, 'Under Review'),
        (STATUS_INVESTIGATING, 'Investigating'),
        (STATUS_ACTION_REQUIRED, 'Action Required'),
        (STATUS_PENDING_VERIFICATION, 'Pending Verification'),
        (STATUS_CLOSED, 'Closed'),
        (STATUS_REOPENED, 'Reopened'),
    ]

    SEVERITY_CHOICES = [
        (1, '1 - Negligible'),
        (2, '2 - Minor'),
        (3, '3 - Moderate'),
        (4, '4 - Major'),
        (5, '5 - Catastrophic'),
    ]

    LIKELIHOOD_CHOICES = [
        (1, '1 - Extremely Improbable'),
        (2, '2 - Improbable'),
        (3, '3 - Remote'),
        (4, '4 - Occasional'),
        (5, '5 - Frequent'),
    ]

    # Primary Incident Identifiers
    reference_number = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
        editable=False,
        help_text="Unique SkyShield aviation tracking reference (e.g. SKY-2026-X8Y9Z)"
    )
    title = models.CharField(max_length=200, help_text="Concise descriptive title of the occurrence.")
    incident_type = models.CharField(max_length=30, choices=TYPE_CHOICES, db_index=True)
    occurrence_date = models.DateTimeField(
        help_text="Exact local timestamp when the event transpired.",
        db_index=True
    )
    reported_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Operational Context
    location = models.CharField(
        max_length=150,
        help_text="ICAO/IATA code, facility, ramp, or runway (e.g. KJFK / Taxiway Bravo)."
    )
    aircraft_registration = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Tail registration number (e.g. N102AA, G-EZTK)."
    )
    flight_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Commercial/Military flight number (e.g. AA482, BA011)."
    )

    # Narrative Details
    description = models.TextField(help_text="Full objective narrative of facts, conditions, and sequence of events.")
    immediate_actions_taken = models.TextField(
        blank=True,
        default='',
        help_text="Immediate containment or emergency response performed by crew."
    )
    potential_consequences = models.TextField(
        blank=True,
        default='',
        help_text="Worst-case realistic potential outcome had containment failed."
    )
    actual_consequences = models.TextField(
        blank=True,
        default='',
        help_text="Actual observed operational delays, damage, or injuries."
    )

    # Risk Metrics (Calculated Server-Side)
    initial_severity = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        choices=SEVERITY_CHOICES
    )
    initial_likelihood = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        choices=LIKELIHOOD_CHOICES
    )
    risk_score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(25)],
        editable=False,
        db_index=True
    )
    risk_level = models.CharField(max_length=20, editable=False, db_index=True)

    # Workflow & Assignments
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_REPORTED,
        db_index=True
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='reported_incidents'
    )
    assigned_investigator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_incidents'
    )

    # Closure Record
    closure_notes = models.TextField(blank=True, default='')
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='closed_incidents'
    )

    class Meta:
        ordering = ['-occurrence_date']
        verbose_name = 'Incident Report'
        verbose_name_plural = 'Incident Reports'
        indexes = [
            models.Index(fields=['status', 'occurrence_date']),
            models.Index(fields=['incident_type', 'risk_level']),
        ]

    def __str__(self):
        return f"[{self.reference_number}] {self.title} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        # 1. Guarantee unique reference number generation
        if not self.reference_number:
            self.reference_number = self.generate_unique_reference()

        # 2. Strict server-side risk calculation
        calc = calculate_score_and_level(self.initial_likelihood, self.initial_severity)
        self.risk_score = calc['score']
        self.risk_level = calc['level']

        super().save(*args, **kwargs)

    @classmethod
    def generate_unique_reference(cls):
        """
        Generates reference format SKY-YYYY-XXXXX where XXXXX is a cryptographically
        secure uppercase alphanumeric token. Re-checks DB uniqueness in a loop.
        """
        year = timezone.now().year
        alphabet = string.ascii_uppercase + string.digits
        # Exclude confusing characters 0, O, 1, I
        clean_alphabet = ''.join(c for c in alphabet if c not in ('0', 'O', '1', 'I'))
        
        while True:
            token = ''.join(secrets.choice(clean_alphabet) for _ in range(5))
            candidate = f"SKY-{year}-{token}"
            if not cls.objects.filter(reference_number=candidate).exists():
                return candidate

    @property
    def status_badge_class(self):
        badges = {
            self.STATUS_REPORTED: 'bg-secondary',
            self.STATUS_UNDER_REVIEW: 'bg-info text-dark',
            self.STATUS_INVESTIGATING: 'bg-primary',
            self.STATUS_ACTION_REQUIRED: 'bg-warning text-dark',
            self.STATUS_PENDING_VERIFICATION: 'bg-purple text-white',
            self.STATUS_CLOSED: 'bg-success',
            self.STATUS_REOPENED: 'bg-danger',
        }
        return badges.get(self.status, 'bg-secondary')

    @property
    def risk_badge_class(self):
        badges = {
            'LOW': 'bg-success',
            'MODERATE': 'bg-warning text-dark',
            'HIGH': 'bg-orange text-white',
            'CRITICAL': 'bg-danger text-white',
        }
        return badges.get(self.risk_level, 'bg-secondary')

    @property
    def is_closed(self):
        return self.status == self.STATUS_CLOSED

    @property
    def has_investigation(self):
        return hasattr(self, 'investigation')

    @property
    def can_be_closed_safely(self):
        """
        Returns (can_close: bool, reasons: list[str])
        Verifies all business rules before closure.
        """
        reasons = []
        # Rule 1: If investigation exists, must be approved
        if hasattr(self, 'investigation'):
            if self.investigation.status != 'APPROVED':
                reasons.append("Investigation is still active and has not been approved by Safety Management.")

        # Rule 2: All corrective actions must be completed
        open_capas = self.corrective_actions.exclude(status='COMPLETED').count()
        if open_capas > 0:
            reasons.append(f"{open_capas} corrective action(s) remain open or pending verification.")

        return (len(reasons) == 0, reasons)


class IncidentStatusHistory(models.Model):
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    from_status = models.CharField(max_length=30)
    to_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Status History Record'
        verbose_name_plural = 'Status History Records'

    def __str__(self):
        return f"{self.incident.reference_number}: {self.from_status} -> {self.to_status} at {self.timestamp}"


class IncidentAttachment(models.Model):
    ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.txt', '.doc', '.docx', '.csv', '.xlsx']
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='incident_evidence/%Y/%m/')
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    file_type = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True, help_text="e.g. Flight Recorder graph, photo of ramp FOD")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Evidence Attachment'
        verbose_name_plural = 'Evidence Attachments'

    def __str__(self):
        return f"{self.filename} ({self.incident.reference_number})"

    @property
    def file_size_display(self):
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.2f} MB"
