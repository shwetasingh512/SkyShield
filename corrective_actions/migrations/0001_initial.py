from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('incidents', '0001_initial'),
        ('investigations', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CorrectiveAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_type', models.CharField(choices=[('CORRECTIVE', 'Corrective Action (Immediate Hazard Rectification)'), ('PREVENTIVE', 'Preventive Action (Long-Term Systemic Defense)')], default='CORRECTIVE', max_length=20)),
                ('title', models.CharField(help_text='Concise title of corrective or preventive measure.', max_length=200)),
                ('description', models.TextField(help_text='Detailed engineering, operational, or training instruction.')),
                ('priority', models.CharField(choices=[('LOW', 'Low Priority (SOP review within 60 days)'), ('MEDIUM', 'Medium Priority (Action required within 30 days)'), ('HIGH', 'High Priority (Mitigation required within 14 days)'), ('CRITICAL', 'Critical Priority (Immediate containment / 72 hours)')], db_index=True, default='MEDIUM', max_length=20)),
                ('due_date', models.DateField(db_index=True)),
                ('status', models.CharField(choices=[('OPEN', 'Open / Assigned'), ('IN_PROGRESS', 'In Progress'), ('PENDING_VERIFICATION', 'Pending Verification & Sign-off'), ('COMPLETED', 'Completed & Verified'), ('CANCELLED', 'Cancelled / Supurceded')], db_index=True, default='OPEN', max_length=25)),
                ('completion_evidence', models.TextField(blank=True, default='', help_text='Factual evidence of implementation (e.g. bulletin number, training roster, work order ref).')),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('verification_notes', models.TextField(blank=True, default='', help_text='Safety Manager verification notes confirming barrier effectiveness.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('completed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='completed_actions', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_actions', to=settings.AUTH_USER_MODEL)),
                ('incident', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='corrective_actions', to='incidents.incident')),
                ('investigation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='corrective_actions', to='investigations.investigation')),
                ('responsible_user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='assigned_actions', to=settings.AUTH_USER_MODEL)),
                ('verified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='verified_actions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Corrective & Preventive Action',
                'verbose_name_plural': 'Corrective & Preventive Actions',
                'ordering': ['due_date', 'priority'],
            },
        ),
        migrations.AddIndex(
            model_name='correctiveaction',
            index=models.Index(fields=['status', 'due_date'], name='corrective__status_ad6c9d_idx'),
        ),
        migrations.AddIndex(
            model_name='correctiveaction',
            index=models.Index(fields=['responsible_user', 'status'], name='corrective__respons_78ffb5_idx'),
        ),
    ]
