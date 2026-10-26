from django.contrib import admin
from .models import RiskAssessment, RiskThresholdConfig

@admin.register(RiskThresholdConfig)
class RiskThresholdConfigAdmin(admin.ModelAdmin):
    list_display = ('band_name', 'min_score', 'max_score', 'color_code', 'description')
    ordering = ('min_score',)

@admin.register(RiskAssessment)
class RiskAssessmentAdmin(admin.ModelAdmin):
    list_display = ('incident', 'assessment_type', 'calculated_score', 'risk_level', 'assessor', 'created_at')
    list_filter = ('assessment_type', 'risk_level', 'created_at')
    search_fields = ('incident__reference_number', 'incident__title', 'rationale', 'assessor__username')
    readonly_fields = ('calculated_score', 'risk_level', 'created_at')
