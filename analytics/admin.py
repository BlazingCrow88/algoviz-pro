"""
Django admin configuration for analytics app.
"""
from django.contrib import admin
from .models import AnalysisResult, FunctionMetric


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    """Admin interface for AnalysisResult model."""

    list_display = ['id', 'get_source_preview', 'cyclomatic_complexity',
                    'num_functions', 'maintainability_index', 'analyzed_at']
    list_filter = ['analyzed_at']
    readonly_fields = ['analyzed_at']
    date_hierarchy = 'analyzed_at'

    def get_source_preview(self, obj):
        """Show first 50 characters of source code."""
        if obj.code_file:
            return f"From: {obj.code_file.name}"
        preview = obj.source_code[:50]
        if len(obj.source_code) > 50:
            preview += "..."
        return preview

    get_source_preview.short_description = 'Source'


@admin.register(FunctionMetric)
class FunctionMetricAdmin(admin.ModelAdmin):
    """Admin interface for FunctionMetric model."""

    list_display = ['name', 'analysis', 'complexity', 'num_lines', 'num_params', 'max_depth']
    list_filter = ['complexity']
    search_fields = ['name']