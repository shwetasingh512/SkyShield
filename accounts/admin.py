from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'department', 'employee_id', 'is_active', 'is_staff')
    list_filter = ('role', 'department', 'is_active', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'employee_id')
    ordering = ('username',)

    fieldsets = UserAdmin.fieldsets + (
        ('SkyShield Role & Organization', {
            'fields': ('role', 'department', 'employee_id', 'phone_number')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('SkyShield Role & Organization', {
            'fields': ('role', 'department', 'employee_id', 'phone_number')
        }),
    )
