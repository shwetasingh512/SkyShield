from django.db import models
from django.conf import settings
from django.utils import timezone

class Investigation(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_SUBMITTED = 'SUBMITTED'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'In Progress / Active Inquiry'),
        (STATUS_SUBMITTED, 'Submitted for Manager Review'),
        (STATUS_APPROVED, 'Approved by Safety Management'),
        (STATUS_REJECTED, 'Returned for Additional Investigation'),
    ]

    incident = models.OneToOneField(
        'incidents.Incident',
        on_delete=models.CASCADE,
        related_name='investigation'
    )
    investigator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='investigations'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        db_index=True
    )
    start_date = models.DateField(default=timezone.now)
    completion_date = models.DateField(null=True, blank=True)

    objectives = models.TextField(
        help_text="Investigation scope, objectives, and regulatory/operational boundaries."
    )
    findings = models.TextField(
        blank=True,
        default='',
        help_text="Key established factual findings and chronological analysis."
    )
    evidence_reviewed = models.TextField(
        blank=True,
        default='',
        help_text="Telemetry, voice recordings, maintenance logs, weather reports examined."
    )
    proposed_root_causes = models.TextField(
        blank=True,
        default='',
        help_text="Primary systemic or immediate root causes deduced by the investigator."
    )
    investigator_notes = models.TextField(
        blank=True,
        default='',
        help_text="Working notes, witness interview observations, and preliminary hypotheses."
    )

    # Management Review & Approval
    review_comments = models.TextField(
        blank=True,
        default='',
        help_text="Safety Manager critique, concurrence, or required follow-ups."
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_investigations'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Investigation Workspace'
        verbose_name_plural = 'Investigation Workspaces'

    def __str__(self):
        return f"Investigation for {self.incident.reference_number} ({self.get_status_display()})"

    @property
    def is_approved(self):
        return self.status == self.STATUS_APPROVED

    @property
    def status_badge_class(self):
        badges = {
            self.STATUS_DRAFT: 'bg-primary',
            self.STATUS_SUBMITTED: 'bg-warning text-dark',
            self.STATUS_APPROVED: 'bg-success',
            self.STATUS_REJECTED: 'bg-danger',
        }
        return badges.get(self.status, 'bg-secondary')


class RootCauseAnalysis(models.Model):
    """
    Structured 5 Whys Root Cause Analysis (RCA) methodology.
    Drills down from the immediate problem symptom to underlying latent organizational faults.
    """
    investigation = models.OneToOneField(
        Investigation,
        on_delete=models.CASCADE,
        related_name='root_cause_analysis'
    )
    problem_statement = models.TextField(
        help_text="Problem Statement: What specific event or deviation occurred?"
    )
    why_1 = models.TextField(help_text="Why did this occur? (Direct trigger)")
    why_2 = models.TextField(help_text="Why did the condition in Why #1 exist?")
    why_3 = models.TextField(help_text="Why did the condition in Why #2 occur?")
    why_4 = models.TextField(help_text="Why did the barrier or defense in Why #3 fail?")
    why_5 = models.TextField(help_text="Why did the systemic/organizational process allow Why #4? (Root systemic cause)")
    root_cause_summary = models.TextField(
        help_text="Synthesized underlying root cause statement."
    )
    preventive_recommendation = models.TextField(
        help_text="Core recommendation to eliminate this systemic failure mode."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '5-Whys Root Cause Analysis'
        verbose_name_plural = '5-Whys Root Cause Analyses'

    def __str__(self):
        return f"5 Whys RCA: {self.investigation.incident.reference_number}"


class ContributingFactor(models.Model):
    CATEGORY_HUMAN = 'HUMAN'
    CATEGORY_ENVIRONMENT = 'ENVIRONMENT'
    CATEGORY_ORGANIZATIONAL = 'ORGANIZATIONAL'
    CATEGORY_TECHNICAL = 'TECHNICAL'
    CATEGORY_AIRPORT = 'AIRPORT'

    CATEGORY_CHOICES = [
        (CATEGORY_HUMAN, 'Human Performance / CRM / Fatigue / Workload'),
        (CATEGORY_ENVIRONMENT, 'Environmental / Weather / Turbulence / Visibility'),
        (CATEGORY_ORGANIZATIONAL, 'Organizational / Policy / Training / Procedures'),
        (CATEGORY_TECHNICAL, 'Technical / Airframe / Powerplant / Avionics / Software'),
        (CATEGORY_AIRPORT, 'Aerodrome / Surface Marking / Lighting / ATC Infrastructure'),
    ]

    IMPACT_PRIMARY = 'PRIMARY'
    IMPACT_SECONDARY = 'SECONDARY'
    IMPACT_LATENT = 'LATENT'

    IMPACT_CHOICES = [
        (IMPACT_PRIMARY, 'Primary Causal Factor'),
        (IMPACT_SECONDARY, 'Secondary Contributing Factor'),
        (IMPACT_LATENT, 'Latent Safety Hazard'),
    ]

    investigation = models.ForeignKey(
        Investigation,
        on_delete=models.CASCADE,
        related_name='contributing_factors'
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    impact_level = models.CharField(max_length=20, choices=IMPACT_CHOICES, default=IMPACT_SECONDARY)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['impact_level', 'category']
        verbose_name = 'Contributing Factor'
        verbose_name_plural = 'Contributing Factors'

    def __str__(self):
        return f"[{self.get_impact_level_display()}] {self.get_category_display()}"
