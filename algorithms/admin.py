"""
Django admin configuration for algorithms app.

Registers models with the admin interface for easy management.
"""
from django.contrib import admin
from .models import Algorithm, ExecutionLog


@admin.register(Algorithm)
class AlgorithmAdmin(admin.ModelAdmin):
    """Admin interface for Algorithm model."""

    list_display = ['name', 'category', 'time_complexity_average', 'space_complexity', 'is_stable', 'created_at']
    list_filter = ['category', 'is_stable']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']

    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'category', 'description']
        }),
        ('Complexity Analysis', {
            'fields': ['time_complexity_best', 'time_complexity_average',
                       'time_complexity_worst', 'space_complexity']
        }),
        ('Properties', {
            'fields': ['is_stable']
        }),
        ('Metadata', {
            'fields': ['created_at'],
            'classes': ['collapse']
        }),
    ]


@admin.register(ExecutionLog)
class ExecutionLogAdmin(admin.ModelAdmin):
    """Admin interface for ExecutionLog model."""

    list_display = ['algorithm', 'input_size', 'execution_time_ms', 'comparisons', 'swaps', 'executed_at']
    list_filter = ['algorithm', 'executed_at']
    search_fields = ['algorithm__name']
    readonly_fields = ['executed_at']
    date_hierarchy = 'executed_at'

    def has_add_permission(self, request):
        """Disable manual creation of execution logs."""
        return False
