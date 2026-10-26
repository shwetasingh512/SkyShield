from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Incident',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference_number', models.CharField(db_index=True, editable=False, help_text='Unique SkyShield aviation tracking reference (e.g. SKY-2026-X8Y9Z)', max_length=32, unique=True)),
                ('title', models.CharField(help_text='Concise descriptive title of the occurrence.', max_length=200)),
                ('incident_type', models.CharField(choices=[('RUNWAY_INCURSION', 'Runway Incursion'), ('BIRD_STRIKE', 'Bird Strike / Wildlife Hazard'), ('MAINTENANCE_ISSUE', 'Maintenance & Tech Discrepancy'), ('EQUIPMENT_FAILURE', 'Avionics / Ground Equipment Failure'), ('GROUND_HANDLING', 'Ground Handling & Ramp Incident'), ('HUMAN_FACTORS', 'Human Factors & Fatigue'), ('NEAR_MISS', 'Airborne Near Miss / TCAS Alert'), ('HAZARD_REPORT', 'Proactive Safety Hazard Report'), ('PROCEDURE_DEVIATION', 'Operational SOP Deviation'), ('OTHER', 'Other Operational Occurrence')], db_index=True, max_length=30)),
                ('occurrence_date', models.DateTimeField(db_index=True, help_text='Exact local timestamp when the event transpired.')),
                ('reported_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('location', models.CharField(help_text='ICAO/IATA code, facility, ramp, or runway (e.g. KJFK / Taxiway Bravo).', max_length=150)),
                ('aircraft_registration', models.CharField(blank=True, help_text='Tail registration number (e.g. N102AA, G-EZTK).', max_length=20, null=True)),
                ('flight_number', models.CharField(blank=True, help_text='Commercial/Military flight number (e.g. AA482, BA011).', max_length=20, null=True)),
                ('description', models.TextField(help_text='Full objective narrative of facts, conditions, and sequence of events.')),
                ('immediate_actions_taken', models.TextField(blank=True, default='', help_text='Immediate containment or emergency response performed by crew.')),
                ('potential_consequences', models.TextField(blank=True, default='', help_text='Worst-case realistic potential outcome had containment failed.')),
                ('actual_consequences', models.TextField(blank=True, default='', help_text='Actual observed operational delays, damage, or injuries.')),
                ('initial_severity', models.PositiveSmallIntegerField(choices=[(1, '1 - Negligible'), (2, '2 - Minor'), (3, '3 - Moderate'), (4, '4 - Major'), (5, '5 - Catastrophic')], validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('initial_likelihood', models.PositiveSmallIntegerField(choices=[(1, '1 - Extremely Improbable'), (2, '2 - Improbable'), (3, '3 - Remote'), (4, '4 - Occasional'), (5, '5 - Frequent')], validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('risk_score', models.PositiveSmallIntegerField(db_index=True, editable=False, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(25)])),
                ('risk_level', models.CharField(db_index=True, editable=False, max_length=20)),
                ('status', models.CharField(choices=[('REPORTED', 'Reported'), ('UNDER_REVIEW', 'Under Review'), ('INVESTIGATING', 'Investigating'), ('ACTION_REQUIRED', 'Action Required'), ('PENDING_VERIFICATION', 'Pending Verification'), ('CLOSED', 'Closed'), ('REOPENED', 'Reopened')], db_index=True, default='REPORTED', max_length=30)),
                ('closure_notes', models.TextField(blank=True, default='')),
                ('closed_at', models.DateTimeField(blank=True, null=True)),
                ('assigned_investigator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_incidents', to=settings.AUTH_USER_MODEL)),
                ('closed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='closed_incidents', to=settings.AUTH_USER_MODEL)),
                ('reporter', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reported_incidents', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Incident Report',
                'verbose_name_plural': 'Incident Reports',
                'ordering': ['-occurrence_date'],
            },
        ),
        migrations.CreateModel(
            name='IncidentAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='incident_evidence/%Y/%m/')),
                ('filename', models.CharField(max_length=255)),
                ('file_size', models.PositiveIntegerField(help_text='File size in bytes')),
                ('file_type', models.CharField(max_length=100)),
                ('description', models.CharField(blank=True, help_text='e.g. Flight Recorder graph, photo of ramp FOD', max_length=255)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('incident', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='incidents.incident')),
                ('uploaded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Evidence Attachment',
                'verbose_name_plural': 'Evidence Attachments',
                'ordering': ['-uploaded_at'],
            },
        ),
        migrations.CreateModel(
            name='IncidentStatusHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_status', models.CharField(max_length=30)),
                ('to_status', models.CharField(max_length=30)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True, default='')),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('incident', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='status_history', to='incidents.incident')),
            ],
            options={
                'verbose_name': 'Status History Record',
                'verbose_name_plural': 'Status History Records',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='incident',
            index=models.Index(fields=['status', 'occurrence_date'], name='incidents_i_status_cf945f_idx'),
        ),
        migrations.AddIndex(
            model_name='incident',
            index=models.Index(fields=['incident_type', 'risk_level'], name='incidents_i_inciden_fcefc4_idx'),
        ),
    ]
