from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('incidents', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RiskThresholdConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('band_name', models.CharField(choices=[('LOW', 'Low Risk (Acceptable)'), ('MODERATE', 'Moderate Risk (Review Required)'), ('HIGH', 'High Risk (Mitigation Required)'), ('CRITICAL', 'Critical Risk (Immediate Action / Grounding)')], max_length=20, unique=True)),
                ('min_score', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(25)])),
                ('max_score', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(25)])),
                ('color_code', models.CharField(default='#28a745', help_text='Hex or CSS color code', max_length=20)),
                ('description', models.TextField(help_text='Operational impact criteria for this risk band.')),
                ('action_required', models.TextField(help_text='Standard mandatory response protocol.')),
            ],
            options={
                'verbose_name': 'Risk Band Configuration',
                'verbose_name_plural': 'Risk Band Configurations',
                'ordering': ['min_score'],
            },
        ),
        migrations.CreateModel(
            name='RiskAssessment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assessment_type', models.CharField(choices=[('INITIAL', 'Initial Submission Assessment'), ('REVIEW', 'Safety Manager Review Assessment'), ('INVESTIGATION', 'Post-Investigation Reassessment'), ('RESIDUAL', 'Residual Risk After Actions')], default='INITIAL', max_length=20)),
                ('likelihood', models.PositiveSmallIntegerField(choices=[(1, '1 - Extremely Improbable (Almost never occurs in fleet/industry)'), (2, '2 - Improbable (Very unlikely to occur; has occurred rarely)'), (3, '3 - Remote (Unlikely, but possible to occur in lifecycle)'), (4, '4 - Occasional (Likely to occur several times)'), (5, '5 - Frequent (Likely to occur frequently in operation)')], help_text='Probability of occurrence scale 1-5', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('severity', models.PositiveSmallIntegerField(choices=[(1, '1 - Negligible (Inconvenience or minor delay; no damage or injury)'), (2, '2 - Minor (Minor operating limitations or minor damage)'), (3, '3 - Moderate (Significant reduction in safety margins; minor injury)'), (4, '4 - Major (Serious incident; injuries; significant structural damage)'), (5, '5 - Catastrophic (Aircraft loss, fatal injury, or hull write-off)')], help_text='Consequence severity scale 1-5', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('calculated_score', models.PositiveSmallIntegerField(editable=False, help_text='Strictly server-calculated score: Likelihood x Severity', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(25)])),
                ('risk_level', models.CharField(db_index=True, editable=False, max_length=20)),
                ('rationale', models.TextField(help_text='Detailed justification for assigned likelihood and severity ratings.')),
                ('mitigation_notes', models.TextField(blank=True, default='', help_text='Proposed containment or mitigating factors.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('assessor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='conducted_risk_assessments', to=settings.AUTH_USER_MODEL)),
                ('incident', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='risk_assessments', to='incidents.incident')),
            ],
            options={
                'verbose_name': 'Risk Assessment',
                'verbose_name_plural': 'Risk Assessments',
                'ordering': ['-created_at'],
            },
        ),
    ]
