from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from accounts.models import CustomUser
from incidents.models import Incident
from investigations.models import Investigation
from corrective_actions.models import CorrectiveAction
from incidents.services import transition_incident_status

class WorkflowTransitionTestCase(TestCase):
    def setUp(self):
        self.reporter = CustomUser.objects.create_user(
            username='reporter_wf',
            password='Password123!',
            role=CustomUser.ROLE_REPORTER
        )
        self.manager = CustomUser.objects.create_user(
            username='manager_wf',
            password='Password123!',
            role=CustomUser.ROLE_SAFETY_MANAGER
        )
        self.investigator = CustomUser.objects.create_user(
            username='investigator_wf',
            password='Password123!',
            role=CustomUser.ROLE_INVESTIGATOR
        )

        self.incident = Incident.objects.create(
            title='Flap asymmetry warning',
            incident_type=Incident.TYPE_EQUIPMENT_FAILURE,
            occurrence_date=timezone.now(),
            location='KATL',
            description='Flap asymmetric extension on final.',
            initial_severity=3,
            initial_likelihood=2,
            reporter=self.reporter,
            status=Incident.STATUS_REPORTED
        )

    def test_reporter_cannot_transition_status(self):
        with self.assertRaises(ValidationError):
            transition_incident_status(
                incident=self.incident,
                to_status=Incident.STATUS_UNDER_REVIEW,
                user=self.reporter
            )

    def test_manager_can_transition_to_under_review(self):
        transition_incident_status(
            incident=self.incident,
            to_status=Incident.STATUS_UNDER_REVIEW,
            user=self.manager,
            notes='Triage accepted.'
        )
        self.incident.refresh_from_db()
        self.assertEqual(self.incident.status, Incident.STATUS_UNDER_REVIEW)
        self.assertEqual(self.incident.status_history.count(), 1)

    def test_closure_blocked_by_open_investigation(self):
        # Move to investigating
        transition_incident_status(
            incident=self.incident,
            to_status=Incident.STATUS_UNDER_REVIEW,
            user=self.manager
        )
        transition_incident_status(
            incident=self.incident,
            to_status=Incident.STATUS_INVESTIGATING,
            user=self.manager
        )
        # Create unapproved investigation
        Investigation.objects.create(
            incident=self.incident,
            investigator=self.investigator,
            status=Investigation.STATUS_DRAFT,
            objectives='Scope flap sensor discrepancy.'
        )

        # Attempt to close without manager override must fail
        with self.assertRaises(ValidationError) as ctx:
            transition_incident_status(
                incident=self.incident,
                to_status=Incident.STATUS_CLOSED,
                user=self.manager
            )
        self.assertIn('Closure Blocked', str(ctx.exception))

    def test_closure_blocked_by_open_capa(self):
        # Simple incident with open CAPA
        CorrectiveAction.objects.create(
            incident=self.incident,
            title='Calibrate flap skew sensor',
            description='Service manual check.',
            responsible_user=self.investigator,
            priority='HIGH',
            due_date=timezone.now().date() + timedelta(days=7),
            status=CorrectiveAction.STATUS_OPEN,
            created_by=self.manager
        )
        with self.assertRaises(ValidationError) as ctx:
            transition_incident_status(
                incident=self.incident,
                to_status=Incident.STATUS_CLOSED,
                user=self.manager
            )
        self.assertIn('corrective action(s) remain open', str(ctx.exception))

    def test_successful_closure_when_capa_completed(self):
        capa = CorrectiveAction.objects.create(
            incident=self.incident,
            title='Calibrate flap skew sensor',
            description='Service manual check.',
            responsible_user=self.investigator,
            priority='HIGH',
            due_date=timezone.now().date() + timedelta(days=7),
            status=CorrectiveAction.STATUS_COMPLETED,
            created_by=self.manager
        )
        transition_incident_status(
            incident=self.incident,
            to_status=Incident.STATUS_CLOSED,
            user=self.manager,
            notes='All tasks completed.'
        )
        self.incident.refresh_from_db()
        self.assertEqual(self.incident.status, Incident.STATUS_CLOSED)
        self.assertIsNotNone(self.incident.closed_at)
        self.assertEqual(self.incident.closed_by, self.manager)
