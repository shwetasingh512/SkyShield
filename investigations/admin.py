from django.contrib import admin
from .models import Investigation, RootCauseAnalysis, ContributingFactor

class ContributingFactorInline(admin.TabularInline):
    model = ContributingFactor
    extra = 1

class RootCauseAnalysisInline(admin.StackedInline):
    model = RootCauseAnalysis
    extra = 0

@admin.register(Investigation)
class InvestigationAdmin(admin.ModelAdmin):
    list_display = ('incident', 'investigator', 'status', 'start_date', 'completion_date', 'reviewed_by')
    list_filter = ('status', 'start_date')
    search_fields = ('incident__reference_number', 'incident__title', 'investigator__username', 'findings')
    inlines = [ContributingFactorInline, RootCauseAnalysisInline]

@admin.register(RootCauseAnalysis)
class RootCauseAnalysisAdmin(admin.ModelAdmin):
    list_display = ('investigation', 'created_at', 'updated_at')
    search_fields = ('investigation__incident__reference_number', 'problem_statement', 'root_cause_summary')

@admin.register(ContributingFactor)
class ContributingFactorAdmin(admin.ModelAdmin):
    list_display = ('investigation', 'category', 'impact_level', 'created_at')
    list_filter = ('category', 'impact_level')
