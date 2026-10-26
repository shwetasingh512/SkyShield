from django.contrib import admin
from .models import CorrectiveAction

@admin.register(CorrectiveAction)
class CorrectiveActionAdmin(admin.ModelAdmin):
    list_display = ('title', 'incident', 'responsible_user', 'priority', 'due_date', 'status', 'is_overdue')
    list_filter = ('status', 'priority', 'due_date')
    search_fields = ('title', 'description', 'incident__reference_number', 'responsible_user__username')
    readonly_fields = ('created_at', 'updated_at')
