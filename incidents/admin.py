from django.contrib import admin
from .models import Incident, IncidentStatusHistory, IncidentAttachment

class IncidentAttachmentInline(admin.TabularInline):
    model = IncidentAttachment
    extra = 0
    readonly_fields = ('filename', 'file_size', 'file_type', 'uploaded_by', 'uploaded_at')

class IncidentStatusHistoryInline(admin.TabularInline):
    model = IncidentStatusHistory
    extra = 0
    readonly_fields = ('from_status', 'to_status', 'changed_by', 'timestamp', 'notes')

@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'title', 'incident_type', 'occurrence_date', 'risk_score', 'risk_level', 'status', 'reporter', 'assigned_investigator')
    list_filter = ('status', 'incident_type', 'risk_level', 'occurrence_date')
    search_fields = ('reference_number', 'title', 'location', 'aircraft_registration', 'flight_number', 'description')
    readonly_fields = ('reference_number', 'risk_score', 'risk_level', 'reported_at', 'updated_at')
    inlines = [IncidentAttachmentInline, IncidentStatusHistoryInline]

@admin.register(IncidentAttachment)
class IncidentAttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'incident', 'file_size', 'uploaded_by', 'uploaded_at')

@admin.register(IncidentStatusHistory)
class IncidentStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('incident', 'from_status', 'to_status', 'changed_by', 'timestamp')
    readonly_fields = ('incident', 'from_status', 'to_status', 'changed_by', 'timestamp', 'notes')
