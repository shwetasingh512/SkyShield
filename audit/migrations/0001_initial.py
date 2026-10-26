from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('CREATE', 'Created Record'), ('UPDATE', 'Updated Record'), ('STATUS_CHANGE', 'Status Transition'), ('DELETE_ATTEMPT', 'Deletion Attempt'), ('RISK_ASSESS', 'Risk Assessment Recorded'), ('INVESTIGATION', 'Investigation Updated'), ('RCA_ANALYSIS', '5-Whys RCA Completed'), ('CAPA_ASSIGN', 'CAPA Assigned'), ('CAPA_STATUS', 'CAPA Status Change'), ('CAPA_VERIFY', 'CAPA Verified'), ('LOGIN', 'User Login'), ('LOGOUT', 'User Logout'), ('EXPORT', 'Data Export / Report Generated'), ('SECURITY_VIOLATION', 'Security / Permission Violation')], db_index=True, max_length=50)),
                ('entity_type', models.CharField(db_index=True, max_length=50)),
                ('entity_id', models.CharField(blank=True, db_index=True, max_length=50)),
                ('summary', models.CharField(max_length=255)),
                ('details', models.TextField(blank=True, default='')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_entries', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Audit Log Entry',
                'verbose_name_plural': 'Audit Log Entries',
                'ordering': ['-timestamp'],
                'indexes': [
                    models.Index(fields=['entity_type', 'entity_id'], name='audit_audit_entity__6dd4ff_idx'),
                    models.Index(fields=['action', 'timestamp'], name='audit_audit_action_b9bf59_idx'),
                ],
            },
        ),
    ]
