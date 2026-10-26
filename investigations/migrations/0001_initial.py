from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('incidents', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Investigation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('DRAFT', 'In Progress / Active Inquiry'), ('SUBMITTED', 'Submitted for Manager Review'), ('APPROVED', 'Approved by Safety Management'), ('REJECTED', 'Returned for Additional Investigation')], db_index=True, default='DRAFT', max_length=20)),
                ('start_date', models.DateField(default=django.utils.timezone.now)),
                ('completion_date', models.DateField(blank=True, null=True)),
                ('objectives', models.TextField(help_text='Investigation scope, objectives, and regulatory/operational boundaries.')),
                ('findings', models.TextField(blank=True, default='', help_text='Key established factual findings and chronological analysis.')),
                ('evidence_reviewed', models.TextField(blank=True, default='', help_text='Telemetry, voice recordings, maintenance logs, weather reports examined.')),
                ('proposed_root_causes', models.TextField(blank=True, default='', help_text='Primary systemic or immediate root causes deduced by the investigator.')),
                ('investigator_notes', models.TextField(blank=True, default='', help_text='Working notes, witness interview observations, and preliminary hypotheses.')),
                ('review_comments', models.TextField(blank=True, default='', help_text='Safety Manager critique, concurrence, or required follow-ups.')),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('incident', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='investigation', to='incidents.incident')),
                ('investigator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='investigations', to=settings.AUTH_USER_MODEL)),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_investigations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Investigation Workspace',
                'verbose_name_plural': 'Investigation Workspaces',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ContributingFactor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('HUMAN', 'Human Performance / CRM / Fatigue / Workload'), ('ENVIRONMENT', 'Environmental / Weather / Turbulence / Visibility'), ('ORGANIZATIONAL', 'Organizational / Policy / Training / Procedures'), ('TECHNICAL', 'Technical / Airframe / Powerplant / Avionics / Software'), ('AIRPORT', 'Aerodrome / Surface Marking / Lighting / ATC Infrastructure')], max_length=20)),
                ('impact_level', models.CharField(choices=[('PRIMARY', 'Primary Causal Factor'), ('SECONDARY', 'Secondary Contributing Factor'), ('LATENT', 'Latent Safety Hazard')], default='SECONDARY', max_length=20)),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('investigation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contributing_factors', to='investigations.investigation')),
            ],
            options={
                'verbose_name': 'Contributing Factor',
                'verbose_name_plural': 'Contributing Factors',
                'ordering': ['impact_level', 'category'],
            },
        ),
        migrations.CreateModel(
            name='RootCauseAnalysis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('problem_statement', models.TextField(help_text='Problem Statement: What specific event or deviation occurred?')),
                ('why_1', models.TextField(help_text='Why did this occur? (Direct trigger)')),
                ('why_2', models.TextField(help_text='Why did the condition in Why #1 exist?')),
                ('why_3', models.TextField(help_text='Why did the condition in Why #2 occur?')),
                ('why_4', models.TextField(help_text='Why did the barrier or defense in Why #3 fail?')),
                ('why_5', models.TextField(help_text='Why did the systemic/organizational process allow Why #4? (Root systemic cause)')),
                ('root_cause_summary', models.TextField(help_text='Synthesized underlying root cause statement.')),
                ('preventive_recommendation', models.TextField(help_text='Core recommendation to eliminate this systemic failure mode.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('investigation', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='root_cause_analysis', to='investigations.investigation')),
            ],
            options={
                'verbose_name': '5-Whys Root Cause Analysis',
                'verbose_name_plural': '5-Whys Root Cause Analyses',
            },
        ),
    ]
