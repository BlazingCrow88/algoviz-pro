"""
Django admin configuration for github_integration app.

Sets up the admin interface so we can view and manage repositories and code files
directly from Django's built-in admin panel. Really helpful for debugging and
checking what data we've actually pulled from GitHub.
"""
from django.contrib import admin
from .models import Repository, CodeFile


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    """
    Custom admin for Repository model.

    I organized this to make it easy to find repos by language or search for specific
    ones. The fieldsets group related info together which makes the detail view way
    less cluttered than having everything in one long list.
    """

    list_display = ['full_name', 'language', 'stars', 'forks', 'last_fetched', 'created_at']
    list_filter = ['language', 'created_at']
    search_fields = ['full_name', 'name', 'owner', 'description']
    readonly_fields = ['created_at', 'last_fetched']  # These get set automatically, don't want them edited manually

    fieldsets = [
        ('Repository Info', {
            'fields': ['full_name', 'name', 'owner', 'description', 'url']
        }),
        ('Statistics', {
            'fields': ['language', 'stars', 'forks']
        }),
        ('Metadata', {
            'fields': ['last_fetched', 'created_at']  # Keeping timestamps separate so they're easy to check
        }),
    ]


@admin.register(CodeFile)
class CodeFileAdmin(admin.ModelAdmin):
    """
    Custom admin for CodeFile model.

    Mainly used this for viewing what code we've fetched from GitHub repos.
    The search_fields let you search through actual code content which was super
    useful during testing.
    """

    list_display = ['path', 'repository', 'name', 'size', 'fetched_at']
    list_filter = ['repository', 'fetched_at']
    search_fields = ['path', 'name', 'content']  # Being able to search file content directly is pretty handy
    readonly_fields = ['fetched_at']

    def has_add_permission(self, request):
        """
        Disable manual creation of code files.

        Code files should only come from the GitHub API, not manual admin creation.
        This prevents accidentally adding invalid data that doesn't match a real file.
        """
        return False