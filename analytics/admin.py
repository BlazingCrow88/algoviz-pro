"""
Django admin configuration for analytics app.

I set this up so I could easily check the complexity analysis results during testing
and debug issues when the metrics looked off.
"""
from django.contrib import admin
from .models import AnalysisResult, FunctionMetric


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    """Admin interface for viewing code analysis results."""

    # Show the key metrics right in the list view, so I don't have to click into each one
    list_display = ['id', 'get_source_preview', 'cyclomatic_complexity',
                    'num_functions', 'maintainability_index', 'analyzed_at']

    # Filter by date since I ran tons of test analyses and needed to find recent ones
    list_filter = ['analyzed_at']

    # Don't want to accidentally change timestamps - they should reflect actual analysis time
    readonly_fields = ['analyzed_at']

    # Date hierarchy makes it way easier to find analyses from specific testing sessions
    date_hierarchy = 'analyzed_at'

    def get_source_preview(self, obj):
        """
        Show a preview of what code was analyzed without cluttering the admin list.
        If it's from a file upload, show the filename since that's more useful.
        This otherwise shows the first 50 chars of the actual code.
        """
        if obj.code_file:
            return f"From: {obj.code_file.name}"
        preview = obj.source_code[:50]
        if len(obj.source_code) > 50:
            preview += "..."
        return preview

    get_source_preview.short_description = 'Source'


@admin.register(FunctionMetric)
class FunctionMetricAdmin(admin.ModelAdmin):
    """Admin interface for individual function complexity metrics."""

    # Display all the important complexity indicators at a glance
    list_display = ['name', 'analysis', 'complexity', 'num_lines', 'num_params', 'max_depth']

    # Filter by complexity to quickly find problematic functions during testing
    list_filter = ['complexity']

    # Search by function name since I often needed to check specific functions
    search_fields = ['name']