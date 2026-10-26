from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.models import CustomUser
from incidents.models import Incident, IncidentStatusHistory
from risk_assessments.models import RiskThresholdConfig, RiskAssessment
from investigations.models import Investigation, RootCauseAnalysis, ContributingFactor
from corrective_actions.models import CorrectiveAction
from audit.models import AuditLog

class Command(BaseCommand):
    help = 'Seeds realistic fictional aviation demonstration data for SkyShield.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("--- Starting SkyShield Demo Data Seeding ---"))

        # 1. Create Risk Threshold Configurations
        thresholds = [
            {
                'band_name': RiskThresholdConfig.BAND_LOW,
                'min_score': 1,
                'max_score': 4,
                'color_code': '#198754',
                'description': 'Acceptable risk level with routine monitoring and standard SOP adherence.',
                'action_required': 'No specialized escalation required; periodic trend tracking in quarterly safety review.'
            },
            {
                'band_name': RiskThresholdConfig.BAND_MODERATE,
                'min_score': 5,
                'max_score': 9,
                'color_code': '#ffc107',
                'description': 'Tolerable risk requiring safety review and risk-mitigation measures where practicable.',
                'action_required': 'Review by assigned Safety Manager within 14 days; consider corrective actions.'
            },
            {
                'band_name': RiskThresholdConfig.BAND_HIGH,
                'min_score': 10,
                'max_score': 15,
                'color_code': '#fd7e14',
                'description': 'Undesirable risk level. Active mitigation and barrier implementation mandatory.',
                'action_required': 'Formal safety investigation mandatory; CAPA assignment within 72 hours.'
            },
            {
                'band_name': RiskThresholdConfig.BAND_CRITICAL,
                'min_score': 16,
                'max_score': 25,
                'color_code': '#dc3545',
                'description': 'Intolerable risk level. Immediate operation cessation or procedural suspension.',
                'action_required': 'Immediate executive escalation, fleet or route restriction, and urgent board briefing.'
            },
        ]

        for t in thresholds:
            obj, created = RiskThresholdConfig.objects.update_or_create(
                band_name=t['band_name'],
                defaults=t
            )
            state = "Created" if created else "Updated"
            self.stdout.write(f"  [RiskBand] {state}: {obj.band_name} ({obj.min_score}-{obj.max_score})")

        # 2. Create Users for all 4 Roles
        users_data = [
            {
                'username': 'admin',
                'email': 'admin@skyshield.aero',
                'first_name': 'Chief',
                'last_name': 'Administrator',
                'role': CustomUser.ROLE_ADMINISTRATOR,
                'department': 'EXECUTIVE',
                'employee_id': 'EMP-ADM-001',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': 'safetymanager',
                'email': 'manager.safety@skyshield.aero',
                'first_name': 'Sarah',
                'last_name': 'Vance',
                'role': CustomUser.ROLE_SAFETY_MANAGER,
                'department': 'SAFETY_ASSURANCE',
                'employee_id': 'EMP-SAF-002',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'username': 'investigator',
                'email': 'lead.investigator@skyshield.aero',
                'first_name': 'David',
                'last_name': 'Chen',
                'role': CustomUser.ROLE_INVESTIGATOR,
                'department': 'MAINTENANCE',
                'employee_id': 'EMP-INV-003',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'username': 'reporter',
                'email': 'first.officer@skyshield.aero',
                'first_name': 'Elena',
                'last_name': 'Rostova',
                'role': CustomUser.ROLE_REPORTER,
                'department': 'FLIGHT_OPS',
                'employee_id': 'EMP-REP-004',
                'is_staff': False,
                'is_superuser': False,
            },
        ]

        created_users = {}
        for u in users_data:
            user, created = CustomUser.objects.get_or_create(
                username=u['username'],
                defaults=u
            )
            user.set_password('Password123!')
            user.role = u['role']
            user.department = u['department']
            user.employee_id = u['employee_id']
            user.is_staff = u['is_staff']
            user.is_superuser = u['is_superuser']
            user.save()
            created_users[u['username']] = user
            state = "Created" if created else "Updated"
            self.stdout.write(f"  [User] {state}: {user.username} ({user.get_role_display()})")

        admin_u = created_users['admin']
        manager_u = created_users['safetymanager']
        investigator_u = created_users['investigator']
        reporter_u = created_users['reporter']

        # 3. Create Sample Incidents
        now = timezone.now()

        incidents_seed = [
            {
                'ref': 'SKY-2026-RNW01',
                'title': 'Runway Incursion by Ground Tug during CAT II Low Visibility Operations',
                'type': Incident.TYPE_RUNWAY_INCURSION,
                'date': now - timedelta(days=6, hours=4),
                'location': 'KJFK / Runway 04L at Taxiway Kilo',
                'aircraft': 'N924AA',
                'flight': 'AA1420',
                'desc': 'During CAT II ILS approach in 300m RVR fog, ground tug towing GPU crossed hold-short bars without ATC clearance. Tower observed ground radar alert (ASDE-X) and ordered immediate go-around at 250ft AGL. Aircraft executed clean missed approach.',
                'immediate': 'Tower issued immediate go-around instruction. Ground vehicle instructed to hold position. Ground operations supervisor dispatched.',
                'potential': 'Catastrophic collision on active runway during low-visibility landing roll.',
                'actual': 'Flight delayed 22 minutes following missed approach and subsequent landing. No airframe damage.',
                'sev': 4, 'lik': 3,
                'status': Incident.STATUS_INVESTIGATING,
                'reporter': reporter_u,
                'investigator': investigator_u,
            },
            {
                'ref': 'SKY-2026-BRD02',
                'title': 'Multiple Gull Bird Strike on Rotation with Right Engine High Vibration',
                'type': Incident.TYPE_BIRD_STRIKE,
                'date': now - timedelta(days=12, hours=2),
                'location': 'EGLL / Runway 27R',
                'aircraft': 'G-XLED',
                'flight': 'BA117',
                'desc': 'During takeoff roll at Vr, flock of seagulls ingested into No. 2 engine. High N1 vibration (4.2 units) and burnt organic smell in flight deck. Flight crew declared PAN PAN, leveled off at 4,000ft, executed checklist, and performed overweight return.',
                'immediate': 'Declared PAN PAN. Emergency checklist completed. Fire rescue standby on landing roll.',
                'potential': 'Uncontained engine failure or dual engine degradation on initial climb.',
                'actual': 'Four fan blades damaged on No. 2 engine; boroscope inspection revealed compressor stator impact.',
                'sev': 3, 'lik': 3,
                'status': Incident.STATUS_ACTION_REQUIRED,
                'reporter': reporter_u,
                'investigator': investigator_u,
            },
            {
                'ref': 'SKY-2026-HYD03',
                'title': 'Dual Hydraulic Blue & Yellow System Pressure Loss with Alternate Gear Extension',
                'type': Incident.TYPE_EQUIPMENT_FAILURE,
                'date': now - timedelta(days=25),
                'location': 'KLAX / Inbound Radial 240',
                'aircraft': 'N801SK',
                'flight': 'SK408',
                'desc': 'On descent through 10,000ft, ECAM caution HYD B SYS LO PR triggered, followed 4 minutes later by Y SYS LO PR due to severed flex hose in right main gear bay. Crew successfully executed gravity gear extension and landed safely under Green system.',
                'immediate': 'Crew declared MAYDAY, extended approach pattern, executed gravity gear drop procedure.',
                'potential': 'Total loss of primary flight control actuators or runway excursion on landing rollout without nosewheel steering.',
                'actual': 'Towed off runway; burst hydraulic flex line replaced across fleet.',
                'sev': 4, 'lik': 2,
                'status': Incident.STATUS_CLOSED,
                'reporter': reporter_u,
                'investigator': investigator_u,
                'closed_by': manager_u,
            },
            {
                'ref': 'SKY-2026-RAM04',
                'title': 'Baggage Belt Loader Struck Cargo Door Cowling during Turnaround',
                'type': Incident.TYPE_GROUND_HANDLING,
                'date': now - timedelta(days=3, hours=8),
                'location': 'OMDB / Stand C18',
                'aircraft': 'A6-EER',
                'flight': 'EK204',
                'desc': 'Contract ramp handling belt loader rolled into forward cargo door sill during pre-departure loading due to parking brake failure on ground support equipment (GSE). Dent measuring 8cm x 4cm detected.',
                'immediate': 'Loading suspended. MRO non-destructive testing (NDT) team summoned to measure dent depth.',
                'potential': 'In-flight cargo door latching failure or cabin rapid decompression.',
                'actual': 'Aircraft grounded for 6 hours; temporary repair doubler installed per SRM 53-00-02.',
                'sev': 2, 'lik': 4,
                'status': Incident.STATUS_UNDER_REVIEW,
                'reporter': reporter_u,
                'investigator': investigator_u,
            },
            {
                'ref': 'SKY-2026-PRC05',
                'title': 'Unstabilized Visual Approach below 1,000ft IMC Gate with Late Go-Around',
                'type': Incident.TYPE_PROCEDURE_DEVIATION,
                'date': now - timedelta(days=18),
                'location': 'RJTT / Runway 34L',
                'aircraft': 'JA737X',
                'flight': 'JL88',
                'desc': 'Flight entered instrument conditions at 1,500ft AGL with descent rate exceeding 1,200 fpm and airspeed Vref + 24kt. FO called "Go Around - Unstable" at 800ft; Captain delayed initiation until 420ft AGL before commencing balked landing.',
                'immediate': 'Go-around conducted at 420ft; diverted to primary alternate per fuel reserve requirements.',
                'potential': 'Controlled Flight into Terrain (CFIT) or high-energy runway overrun.',
                'actual': 'No physical damage. Aircraft landed safely on second approach after weather improved.',
                'sev': 4, 'lik': 2,
                'status': Incident.STATUS_INVESTIGATING,
                'reporter': reporter_u,
                'investigator': investigator_u,
            },
            {
                'ref': 'SKY-2026-HZD06',
                'title': 'Safety Hazard: Inoperative Runway Centerline Lighting during Heavy Rain Conditions',
                'type': Incident.TYPE_HAZARD_REPORT,
                'date': now - timedelta(days=1, hours=5),
                'location': 'KSFO / Runway 28R',
                'aircraft': None,
                'flight': None,
                'desc': 'Proactive observation: Section of 400m runway centerline lighting intermittent during heavy precipitation event, causing visual disorientation during touchdown zone transition.',
                'immediate': 'Notified airport operations and airfield maintenance supervisor via radio.',
                'potential': 'Lateral excursion during rollout in wet runway braking action conditions.',
                'actual': 'Airport authority issued NOTAM and scheduled emergency circuit maintenance.',
                'sev': 3, 'lik': 3,
                'status': Incident.STATUS_PENDING_VERIFICATION,
                'reporter': reporter_u,
                'investigator': None,
            },
        ]

        for s in incidents_seed:
            inc, created = Incident.objects.get_or_create(
                reference_number=s['ref'],
                defaults={
                    'title': s['title'],
                    'incident_type': s['type'],
                    'occurrence_date': s['date'],
                    'location': s['location'],
                    'aircraft_registration': s['aircraft'],
                    'flight_number': s['flight'],
                    'description': s['desc'],
                    'immediate_actions_taken': s['immediate'],
                    'potential_consequences': s['potential'],
                    'actual_consequences': s['actual'],
                    'initial_severity': s['sev'],
                    'initial_likelihood': s['lik'],
                    'status': s['status'],
                    'reporter': s['reporter'],
                    'assigned_investigator': s['investigator'],
                    'closed_by': s.get('closed_by'),
                    'closed_at': now - timedelta(days=20) if s.get('closed_by') else None,
                    'closure_notes': "All verification tasks and engineering SB bulletins fully validated." if s.get('closed_by') else ''
                }
            )
            state = "Created" if created else "Exists"
            self.stdout.write(f"  [Incident] {state}: {inc.reference_number} ({inc.risk_level} - {inc.get_status_display()})")

            # Create initial risk assessment
            RiskAssessment.objects.get_or_create(
                incident=inc,
                assessment_type='INITIAL',
                defaults={
                    'likelihood': s['lik'],
                    'severity': s['sev'],
                    'rationale': f"Initial operational risk classification based on reported hazards at {s['location']}.",
                    'mitigation_notes': s['immediate'],
                    'assessor': s['reporter'],
                }
            )

        # 4. Create Formal Investigation for SKY-2026-RNW01
        inc1 = Incident.objects.get(reference_number='SKY-2026-RNW01')
        inv1, created = Investigation.objects.get_or_create(
            incident=inc1,
            defaults={
                'investigator': investigator_u,
                'status': Investigation.STATUS_DRAFT,
                'start_date': (now - timedelta(days=5)).date(),
                'objectives': 'Determine causal factors leading to unauthorized runway crossing in CAT II conditions. Audit ground vehicle situational awareness and communications.',
                'findings': '1. Ground tug driver lost visual sight of taxiway boundary markers due to low ceiling and degraded surface paint.\n2. Ground vehicle radio was tuned to secondary ramp frequency rather than ground control frequency 121.9 MHz.\n3. Stop-bar lighting circuit at taxiway Kilo was inoperative due to ongoing electrical construction.',
                'evidence_reviewed': 'Airport ASDE-X ground radar track replay, ATC voice recording transcripts, ground operations vehicle telematics GPS log.',
                'proposed_root_causes': 'Absence of moving map GPS guidance in ramp vehicles operating in low-visibility environments combined with frequency mis-selection and physical stop bar maintenance blackout.',
                'investigator_notes': 'Interviewed tug operator on Oct 23. Driver stated windshield fogging contributed to disorientation.',
            }
        )

        # 5. Create 5-Whys RCA for Investigation 1
        RootCauseAnalysis.objects.get_or_create(
            investigation=inv1,
            defaults={
                'problem_statement': 'Ground towing vehicle entered active Runway 04L while an arriving commercial airliner was on short final in CAT II weather.',
                'why_1': 'The tug driver navigated past the CAT II holding point without realizing they had reached the active runway boundary.',
                'why_2': 'The driver could not see the painted yellow holding position lines on the taxiway surface.',
                'why_3': 'Surface markings were obscured by rain ponding, and the illuminated red stop bars were unpowered due to electrical work.',
                'why_4': 'Airport operations authorized towing along taxiway Kilo without an escort or active transponder guidance.',
                'why_5': 'Airport Safety Management System lacked an automated risk assessment gate for escort requirements during concurrent stop-bar outages in Low Visibility Procedures (LVP).',
                'root_cause_summary': 'Systemic failure to enforce mandatory vehicle escort protocol during known airfield visual aid outages in low visibility conditions.',
                'preventive_recommendation': 'Implement automated NOTAM/LVP cross-locking in aerodrome dispatch requiring GPS escort for all GSE during stop-bar maintenance.',
            }
        )

        # 6. Add Contributing Factors
        ContributingFactor.objects.get_or_create(
            investigation=inv1,
            category=ContributingFactor.CATEGORY_ENVIRONMENT,
            impact_level=ContributingFactor.IMPACT_SECONDARY,
            defaults={'description': 'Low visibility (RVR 300m) and heavy rain obscured standard ground visual reference points.'}
        )
        ContributingFactor.objects.get_or_create(
            investigation=inv1,
            category=ContributingFactor.CATEGORY_ORGANIZATIONAL,
            impact_level=ContributingFactor.IMPACT_PRIMARY,
            defaults={'description': 'Lack of formalized low-visibility escort SOP when airfield stop-bars are decommissioned for maintenance.'}
        )
        ContributingFactor.objects.get_or_create(
            investigation=inv1,
            category=ContributingFactor.CATEGORY_HUMAN,
            impact_level=ContributingFactor.IMPACT_SECONDARY,
            defaults={'description': 'Tug driver distraction and failure to cross-check radio frequency prior to crossing movement area line.'}
        )

        # 7. Create Corrective Actions (One Overdue, One In Progress, One Completed)
        CorrectiveAction.objects.get_or_create(
            incident=inc1,
            title='Procure and Install Ruggedized ADS-B In Vehicle Displays for Ramp Tugs',
            defaults={
                'action_type': CorrectiveAction.TYPE_PREVENTIVE,
                'description': 'Fit all active movement-area ground handling vehicles with moving-map tablet displays showing runway boundaries and active aircraft positions.',
                'responsible_user': investigator_u,
                'priority': CorrectiveAction.PRIORITY_HIGH,
                'due_date': (now - timedelta(days=2)).date(), # OVERDUE FOR DEMO
                'status': CorrectiveAction.STATUS_IN_PROGRESS,
                'created_by': manager_u,
            }
        )

        CorrectiveAction.objects.get_or_create(
            incident=inc1,
            title='Issue Immediate Safety Directive: Mandatory Escorts during Stop-Bar Outages',
            defaults={
                'action_type': CorrectiveAction.TYPE_CORRECTIVE,
                'description': 'Mandate that no ground equipment may cross any runway intersection without designated Airfield Operations Follow-Me vehicle escort whenever stop bars are de-energized.',
                'responsible_user': manager_u,
                'priority': CorrectiveAction.PRIORITY_CRITICAL,
                'due_date': (now + timedelta(days=5)).date(),
                'status': CorrectiveAction.STATUS_PENDING_VERIFICATION,
                'completion_evidence': 'Safety Notice SN-2026-11 published and briefed at morning shift handover. Acknowledged by all ramp supervisors.',
                'completed_at': now - timedelta(hours=12),
                'completed_by': manager_u,
                'created_by': manager_u,
            }
        )

        # Closed Incident CAPA for SKY-2026-HYD03
        inc3 = Incident.objects.get(reference_number='SKY-2026-HYD03')
        CorrectiveAction.objects.get_or_create(
            incident=inc3,
            title='Fleetwide Replacement of Main Gear Flexible Hydraulic Return Hoses',
            defaults={
                'action_type': CorrectiveAction.TYPE_CORRECTIVE,
                'description': 'Perform fleetwide inspection and premature replacement of hydraulic hose P/N AE71109 per Service Bulletin SB-HYD-26-01.',
                'responsible_user': investigator_u,
                'priority': CorrectiveAction.PRIORITY_CRITICAL,
                'due_date': (now - timedelta(days=15)).date(),
                'status': CorrectiveAction.STATUS_COMPLETED,
                'completion_evidence': 'MRO Work Order WO-99120 completed across all 24 airframes. Verified by Quality Assurance.',
                'completed_at': now - timedelta(days=18),
                'completed_by': investigator_u,
                'verified_by': manager_u,
                'verified_at': now - timedelta(days=16),
                'verification_notes': 'Audit sampling of 4 airframes confirmed correct torque, safety wiring, and pressure check to 3000 PSI without leaks.',
                'created_by': manager_u,
            }
        )

        # 8. Seed Audit Log Activity
        AuditLog.objects.get_or_create(
            action='LOGIN',
            summary='User safetymanager logged into SkyShield Safety Console',
            defaults={
                'user': manager_u,
                'entity_type': 'User',
                'entity_id': str(manager_u.id),
                'ip_address': '127.0.0.1',
            }
        )
        AuditLog.objects.get_or_create(
            action='CREATE',
            summary='Incident SKY-2026-RNW01 logged by first.officer',
            defaults={
                'user': reporter_u,
                'entity_type': 'Incident',
                'entity_id': str(inc1.id),
                'ip_address': '127.0.0.1',
            }
        )
        AuditLog.objects.get_or_create(
            action='STATUS_CHANGE',
            summary='Incident SKY-2026-HYD03 transitioned to CLOSED following verified CAPA implementation',
            defaults={
                'user': manager_u,
                'entity_type': 'Incident',
                'entity_id': str(inc3.id),
                'ip_address': '127.0.0.1',
            }
        )

        self.stdout.write(self.style.SUCCESS("\nSkyShield demonstration dataset successfully seeded!"))
        self.stdout.write(self.style.SUCCESS("Available Demo Credentials (Password for all: 'Password123!'):"))
        self.stdout.write("  - Administrator:     admin")
        self.stdout.write("  - Safety Manager:    safetymanager")
        self.stdout.write("  - Investigator:      investigator")
        self.stdout.write("  - Reporter:          reporter")
