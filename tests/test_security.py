from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import CustomUser
from incidents.models import Incident

class SecurityAndAuthorizationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.reporter_a = CustomUser.objects.create_user(
            username='reporter_alice',
            password='Password123!',
            role=CustomUser.ROLE_REPORTER
        )
        self.reporter_b = CustomUser.objects.create_user(
            username='reporter_bob',
            password='Password123!',
            role=CustomUser.ROLE_REPORTER
        )
        self.manager = CustomUser.objects.create_user(
            username='manager_mary',
            password='Password123!',
            role=CustomUser.ROLE_SAFETY_MANAGER
        )
        self.incident_a = Incident.objects.create(
            title='Confidential Flight Crew Hazard Report',
            incident_type=Incident.TYPE_HAZARD_REPORT,
            occurrence_date=timezone.now(),
            location='KJFK Flight Deck',
            description='Confidential crew report on pilot fatigue during red-eye turnaround.',
            initial_severity=2,
            initial_likelihood=3,
            reporter=self.reporter_a
        )

    def test_idor_reporter_cannot_view_other_reporter_incident(self):
        # Bob logs in and attempts to access Alice's private incident
        self.client.login(username='reporter_bob', password='Password123!')
        url = reverse('incidents:detail', kwargs={'incident_id': self.incident_a.id})
        response = self.client.get(url)
        # Should raise PermissionDenied -> 403
        self.assertEqual(response.status_code, 403)

    def test_manager_can_view_any_incident(self):
        # Safety Manager logs in and accesses incident
        self.client.login(username='manager_mary', password='Password123!')
        url = reverse('incidents:detail', kwargs={'incident_id': self.incident_a.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.incident_a.reference_number)

    def test_reporter_cannot_access_user_management(self):
        self.client.login(username='reporter_alice', password='Password123!')
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 403)

    def test_reporter_cannot_access_audit_log(self):
        self.client.login(username='reporter_alice', password='Password123!')
        response = self.client.get(reverse('audit:audit_log'))
        self.assertEqual(response.status_code, 403)

    def test_manager_can_access_audit_log(self):
        self.client.login(username='manager_mary', password='Password123!')
        response = self.client.get(reverse('audit:audit_log'))
        self.assertEqual(response.status_code, 200)
