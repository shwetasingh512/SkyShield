from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_REPORTER = 'REPORTER'
    ROLE_INVESTIGATOR = 'INVESTIGATOR'
    ROLE_SAFETY_MANAGER = 'SAFETY_MANAGER'
    ROLE_ADMINISTRATOR = 'ADMINISTRATOR'

    ROLE_CHOICES = [
        (ROLE_REPORTER, 'Reporter'),
        (ROLE_INVESTIGATOR, 'Investigator'),
        (ROLE_SAFETY_MANAGER, 'Safety Manager'),
        (ROLE_ADMINISTRATOR, 'Administrator'),
    ]

    DEPARTMENT_CHOICES = [
        ('FLIGHT_OPS', 'Flight Operations'),
        ('GROUND_OPS', 'Ground Operations / Ramp'),
        ('MAINTENANCE', 'Maintenance & Engineering (MRO)'),
        ('CABIN_SAFETY', 'Cabin Safety & In-Flight'),
        ('ATC_DISPATCH', 'Air Traffic & Flight Dispatch'),
        ('SAFETY_ASSURANCE', 'Safety & Quality Assurance'),
        ('EXECUTIVE', 'Executive Management / Legal'),
        ('OTHER', 'General / Other'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_REPORTER,
        db_index=True,
        help_text="Designated functional role within the SkyShield safety workflow."
    )
    department = models.CharField(
        max_length=50,
        choices=DEPARTMENT_CHOICES,
        default='FLIGHT_OPS',
        blank=True
    )
    phone_number = models.CharField(max_length=30, blank=True, default='')
    employee_id = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique airline or aerodrome employee identification code."
    )

    class Meta:
        ordering = ['username']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        full_name = self.get_full_name()
        if full_name:
            return f"{full_name} ({self.username}) - {self.get_role_display()}"
        return f"{self.username} - {self.get_role_display()}"

    @property
    def is_reporter(self):
        return self.role == self.ROLE_REPORTER

    @property
    def is_investigator(self):
        return self.role == self.ROLE_INVESTIGATOR

    @property
    def is_safety_manager(self):
        return self.role == self.ROLE_SAFETY_MANAGER

    @property
    def is_administrator(self):
        return self.role == self.ROLE_ADMINISTRATOR or self.is_superuser

    @property
    def can_view_all_incidents(self):
        return self.role in [self.ROLE_SAFETY_MANAGER, self.ROLE_ADMINISTRATOR] or self.is_superuser

    @property
    def can_assign_investigators(self):
        return self.role in [self.ROLE_SAFETY_MANAGER, self.ROLE_ADMINISTRATOR] or self.is_superuser

    @property
    def can_assess_risk(self):
        return self.role in [self.ROLE_SAFETY_MANAGER, self.ROLE_ADMINISTRATOR, self.ROLE_INVESTIGATOR] or self.is_superuser

    @property
    def can_manage_capa(self):
        return self.role in [self.ROLE_SAFETY_MANAGER, self.ROLE_ADMINISTRATOR, self.ROLE_INVESTIGATOR] or self.is_superuser

    @property
    def can_approve_closure(self):
        return self.role in [self.ROLE_SAFETY_MANAGER, self.ROLE_ADMINISTRATOR] or self.is_superuser

    @property
    def role_badge_class(self):
        badges = {
            self.ROLE_REPORTER: 'bg-secondary',
            self.ROLE_INVESTIGATOR: 'bg-primary',
            self.ROLE_SAFETY_MANAGER: 'bg-warning text-dark',
            self.ROLE_ADMINISTRATOR: 'bg-danger',
        }
        return badges.get(self.role, 'bg-info')
