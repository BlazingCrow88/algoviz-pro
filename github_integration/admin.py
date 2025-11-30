"""
Django admin configuration for github_integration app.
"""
from django.contrib import admin
from .models import Repository, CodeFile


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    """Admin interface for Repository model."""

    list_display = ['full_name', 'language', 'stars', 'forks', 'last_fetched', 'created_at']
    list_filter = ['language', 'created_at']
    search_fields = ['full_name', 'name', 'owner', 'description']
    readonly_fields = ['created_at', 'last_fetched']

    fieldsets = [
        ('Repository Info', {
            'fields': ['full_name', 'name', 'owner', 'description', 'url']
        }),
        ('Statistics', {
            'fields': ['language', 'stars', 'forks']
        }),
        ('Metadata', {
            'fields': ['last_fetched', 'created_at']
        }),
    ]


@admin.register(CodeFile)
class CodeFileAdmin(admin.ModelAdmin):
    """Admin interface for CodeFile model."""

    list_display = ['path', 'repository', 'name', 'size', 'fetched_at']
    list_filter = ['repository', 'fetched_at']
    search_fields = ['path', 'name', 'content']
    readonly_fields = ['fetched_at']

    def has_add_permission(self, request):
        """Disable manual creation of code files."""
        return False