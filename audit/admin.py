from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'entity_type', 'entity_id', 'summary', 'ip_address')
    list_filter = ('action', 'entity_type', 'timestamp')
    search_fields = ('summary', 'details', 'entity_id', 'user__username', 'ip_address')
    readonly_fields = [f.name for f in AuditLog._meta.fields]
    ordering = ('-timestamp',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
