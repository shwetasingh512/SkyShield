from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class RiskThresholdConfig(models.Model):
    BAND_LOW = 'LOW'
    BAND_MODERATE = 'MODERATE'
    BAND_HIGH = 'HIGH'
    BAND_CRITICAL = 'CRITICAL'

    BAND_CHOICES = [
        (BAND_LOW, 'Low Risk (Acceptable)'),
        (BAND_MODERATE, 'Moderate Risk (Review Required)'),
        (BAND_HIGH, 'High Risk (Mitigation Required)'),
        (BAND_CRITICAL, 'Critical Risk (Immediate Action / Grounding)'),
    ]

    band_name = models.CharField(max_length=20, choices=BAND_CHOICES, unique=True)
    min_score = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(25)])
    max_score = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(25)])
    color_code = models.CharField(max_length=20, default='#28a745', help_text="Hex or CSS color code")
    description = models.TextField(help_text="Operational impact criteria for this risk band.")
    action_required = models.TextField(help_text="Standard mandatory response protocol.")

    class Meta:
        ordering = ['min_score']
        verbose_name = 'Risk Band Configuration'
        verbose_name_plural = 'Risk Band Configurations'

    def __str__(self):
        return f"{self.get_band_name_display()} ({self.min_score} - {self.max_score})"

class RiskAssessment(models.Model):
    ASSESSMENT_TYPES = [
        ('INITIAL', 'Initial Submission Assessment'),
        ('REVIEW', 'Safety Manager Review Assessment'),
        ('INVESTIGATION', 'Post-Investigation Reassessment'),
        ('RESIDUAL', 'Residual Risk After Actions'),
    ]

    LIKELIHOOD_CHOICES = [
        (1, '1 - Extremely Improbable (Almost never occurs in fleet/industry)'),
        (2, '2 - Improbable (Very unlikely to occur; has occurred rarely)'),
        (3, '3 - Remote (Unlikely, but possible to occur in lifecycle)'),
        (4, '4 - Occasional (Likely to occur several times)'),
        (5, '5 - Frequent (Likely to occur frequently in operation)'),
    ]

    SEVERITY_CHOICES = [
        (1, '1 - Negligible (Inconvenience or minor delay; no damage or injury)'),
        (2, '2 - Minor (Minor operating limitations or minor damage)'),
        (3, '3 - Moderate (Significant reduction in safety margins; minor injury)'),
        (4, '4 - Major (Serious incident; injuries; significant structural damage)'),
        (5, '5 - Catastrophic (Aircraft loss, fatal injury, or hull write-off)'),
    ]

    incident = models.ForeignKey(
        'incidents.Incident',
        on_delete=models.CASCADE,
        related_name='risk_assessments'
    )
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_TYPES, default='INITIAL')
    likelihood = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        choices=LIKELIHOOD_CHOICES,
        help_text="Probability of occurrence scale 1-5"
    )
    severity = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        choices=SEVERITY_CHOICES,
        help_text="Consequence severity scale 1-5"
    )
    calculated_score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(25)],
        editable=False,
        help_text="Strictly server-calculated score: Likelihood x Severity"
    )
    risk_level = models.CharField(max_length=20, editable=False, db_index=True)
    rationale = models.TextField(help_text="Detailed justification for assigned likelihood and severity ratings.")
    mitigation_notes = models.TextField(blank=True, default='', help_text="Proposed containment or mitigating factors.")
    assessor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='conducted_risk_assessments'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Risk Assessment'
        verbose_name_plural = 'Risk Assessments'

    def __str__(self):
        return f"{self.incident.reference_number} - {self.get_assessment_type_display()}: {self.risk_level} ({self.calculated_score})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if not (1 <= self.likelihood <= 5):
            raise ValidationError({'likelihood': 'Likelihood must be an integer between 1 and 5.'})
        if not (1 <= self.severity <= 5):
            raise ValidationError({'severity': 'Severity must be an integer between 1 and 5.'})

    def save(self, *args, **kwargs):
        # Enforce server-side score calculation
        self.calculated_score = int(self.likelihood) * int(self.severity)
        
        # Determine risk level based on DB config or standard ICAO/FAA defaults
        score = self.calculated_score
        try:
            config = RiskThresholdConfig.objects.filter(
                min_score__lte=score,
                max_score__gte=score
            ).first()
            if config:
                self.risk_level = config.band_name
            else:
                self.risk_level = self._default_level(score)
        except Exception:
            self.risk_level = self._default_level(score)

        super().save(*args, **kwargs)

    @staticmethod
    def _default_level(score):
        if score <= 4:
            return 'LOW'
        elif score <= 9:
            return 'MODERATE'
        elif score <= 15:
            return 'HIGH'
        else:
            return 'CRITICAL'

    @property
    def badge_class(self):
        badges = {
            'LOW': 'bg-success',
            'MODERATE': 'bg-warning text-dark',
            'HIGH': 'bg-orange text-white',
            'CRITICAL': 'bg-danger text-white',
        }
        return badges.get(self.risk_level, 'bg-secondary')
