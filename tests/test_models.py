from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from accounts.models import CustomUser
from incidents.models import Incident, IncidentAttachment
from risk_assessments.models import RiskAssessment, RiskThresholdConfig
from investigations.models import Investigation, RootCauseAnalysis, ContributingFactor
from corrective_actions.models import CorrectiveAction

class ModelCreationAndLogicTestCase(TestCase):
    def setUp(self):
        self.reporter = CustomUser.objects.create_user(
            username='reporter_test',
            password='Password123!',
            role=CustomUser.ROLE_REPORTER,
            department='FLIGHT_OPS'
        )
        self.manager = CustomUser.objects.create_user(
            username='manager_test',
            password='Password123!',
            role=CustomUser.ROLE_SAFETY_MANAGER,
            department='SAFETY_ASSURANCE'
        )
        self.investigator = CustomUser.objects.create_user(
            username='investigator_test',
            password='Password123!',
            role=CustomUser.ROLE_INVESTIGATOR,
            department='MAINTENANCE'
        )

        # Create thresholds
        RiskThresholdConfig.objects.create(band_name='LOW', min_score=1, max_score=4, color_code='#198754')
        RiskThresholdConfig.objects.create(band_name='MODERATE', min_score=5, max_score=9, color_code='#ffc107')
        RiskThresholdConfig.objects.create(band_name='HIGH', min_score=10, max_score=15, color_code='#fd7e14')
        RiskThresholdConfig.objects.create(band_name='CRITICAL', min_score=16, max_score=25, color_code='#dc3545')

    def test_custom_user_roles(self):
        self.assertTrue(self.reporter.is_reporter)
        self.assertFalse(self.reporter.is_safety_manager)
        self.assertTrue(self.manager.is_safety_manager)
        self.assertTrue(self.investigator.is_investigator)
        self.assertTrue(self.manager.can_view_all_incidents)
        self.assertFalse(self.reporter.can_view_all_incidents)

    def test_incident_unique_reference_and_risk_calculation(self):
        incident = Incident.objects.create(
            title='Engine surge during climb',
            incident_type=Incident.TYPE_MAINTENANCE_ISSUE,
            occurrence_date=timezone.now(),
            location='KJFK 31L',
            description='Compressor stall during climb at 2000ft.',
            initial_severity=4,
            initial_likelihood=3,
            reporter=self.reporter
        )
        # Check reference generated
        self.assertTrue(incident.reference_number.startswith('SKY-'))
        # Check server risk calculation: 4 * 3 = 12 (HIGH)
        self.assertEqual(incident.risk_score, 12)
        self.assertEqual(incident.risk_level, 'HIGH')

        # Test another incident gets a different unique reference
        incident2 = Incident.objects.create(
            title='Bird strike on wing',
            incident_type=Incident.TYPE_BIRD_STRIKE,
            occurrence_date=timezone.now(),
            location='EGLL',
            description='Small bird struck leading edge slat.',
            initial_severity=2,
            initial_likelihood=2,
            reporter=self.reporter
        )
        self.assertNotEqual(incident.reference_number, incident2.reference_number)
        self.assertEqual(incident2.risk_score, 4)
        self.assertEqual(incident2.risk_level, 'LOW')

    def test_risk_assessment_server_calculation(self):
        incident = Incident.objects.create(
            title='Hydraulic warning',
            incident_type=Incident.TYPE_EQUIPMENT_FAILURE,
            occurrence_date=timezone.now(),
            location='KLAX',
            description='Low pressure warning light.',
            initial_severity=3,
            initial_likelihood=2,
            reporter=self.reporter
        )
        assessment = RiskAssessment.objects.create(
            incident=incident,
            assessment_type='REVIEW',
            likelihood=5,
            severity=4,
            rationale='Reassessed based on telemetry.',
            assessor=self.manager
        )
        # 5 * 4 = 20 (CRITICAL)
        self.assertEqual(assessment.calculated_score, 20)
        self.assertEqual(assessment.risk_level, 'CRITICAL')

    def test_capa_overdue_detection(self):
        incident = Incident.objects.create(
            title='FOD on ramp',
            incident_type=Incident.TYPE_GROUND_HANDLING,
            occurrence_date=timezone.now(),
            location='OMDB',
            description='Metal bolt found on stand.',
            initial_severity=2,
            initial_likelihood=3,
            reporter=self.reporter
        )
        # Action past due date
        overdue_capa = CorrectiveAction.objects.create(
            incident=incident,
            title='Ramp magnetic sweep',
            description='Run sweeper truck.',
            responsible_user=self.investigator,
            priority='HIGH',
            due_date=timezone.now().date() - timedelta(days=5),
            status=CorrectiveAction.STATUS_OPEN,
            created_by=self.manager
        )
        self.assertTrue(overdue_capa.is_overdue)

        # Completed action past due date is not overdue
        completed_capa = CorrectiveAction.objects.create(
            incident=incident,
            title='Brief ramp workers',
            description='Hold safety stand-down.',
            responsible_user=self.investigator,
            priority='MEDIUM',
            due_date=timezone.now().date() - timedelta(days=2),
            status=CorrectiveAction.STATUS_COMPLETED,
            created_by=self.manager
        )
        self.assertFalse(completed_capa.is_overdue)
