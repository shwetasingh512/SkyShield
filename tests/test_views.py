from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import CustomUser
from incidents.models import Incident
from corrective_actions.models import CorrectiveAction

class ViewsAndExportsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.reporter = CustomUser.objects.create_user(
            username='reporter_v',
            password='Password123!',
            role=CustomUser.ROLE_REPORTER
        )
        self.manager = CustomUser.objects.create_user(
            username='manager_v',
            password='Password123!',
            role=CustomUser.ROLE_SAFETY_MANAGER
        )
        self.incident = Incident.objects.create(
            title='Bird strike on approach',
            incident_type=Incident.TYPE_BIRD_STRIKE,
            occurrence_date=timezone.now(),
            location='KJFK 22L',
            description='Strike on radome.',
            initial_severity=2,
            initial_likelihood=3,
            reporter=self.reporter
        )

    def test_unauthenticated_redirects_to_login(self):
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)

    def test_dashboard_authenticated(self):
        self.client.login(username='reporter_v', password='Password123!')
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Operational Safety Overview')
        self.assertEqual(response.context['total_incidents'], 1)

    def test_incident_create_view(self):
        self.client.login(username='reporter_v', password='Password123!')
        url = reverse('incidents:report')
        payload = {
            'title': 'Ramp fuel spill near gate 14',
            'incident_type': Incident.TYPE_GROUND_HANDLING,
            'occurrence_date': '2026-10-25T14:30',
            'location': 'KORD Terminal 3 Gate 14',
            'description': 'Fuel bowser overfilled fuel tank spilling approximately 15 liters of Jet-A.',
            'immediate_actions_taken': 'Emergency fuel shutoff activated, ramp absorbent pads applied.',
            'initial_severity': 3,
            'initial_likelihood': 2,
        }
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Incident.objects.filter(title='Ramp fuel spill near gate 14').exists())

    def test_incident_csv_export(self):
        self.client.login(username='manager_v', password='Password123!')
        response = self.client.get(reverse('reports:incidents_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn(self.incident.reference_number, response.content.decode('utf-8'))

    def test_incident_pdf_export(self):
        self.client.login(username='manager_v', password='Password123!')
        url = reverse('reports:incident_pdf', kwargs={'incident_id': self.incident.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF'))
