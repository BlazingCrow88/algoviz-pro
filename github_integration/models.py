"""
Database models for the GitHub integration app.

Caches GitHub repository metadata and fetched code files to avoid redundant
API calls. Critical for staying under GitHub's rate limits (60/hour without
auth, 5000/hour with token) and for performance (DB query ~5ms vs API call ~500ms).

Data flow: Search repo → cache metadata → fetch file → cache content → reuse
"""
from django.db import models
from django.core.validators import URLValidator
from django.utils import timezone


class Repository(models.Model):
    """
    Stores GitHub repository metadata.

    One-to-many with CodeFile: One repo can have many files.
    Caches search results and repo details to minimize GitHub API calls.
    """

    # Repository identification
    full_name = models.CharField(
        max_length=200,
        unique=True,  # "owner/repo" must be unique, creates DB index
        help_text="Full repository name (owner/repo)"
    )

    name = models.CharField(
        max_length=100,
        help_text="Repository name"
    )

    owner = models.CharField(
        max_length=100,
        help_text="Repository owner username"
    )

    # Repository metadata
    description = models.TextField(
        blank=True,
        default='',
        help_text="Repository description"
    )

    url = models.URLField(
        validators=[URLValidator()],
        help_text="GitHub repository URL"
    )

    language = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="Primary programming language"
    )

    # Popularity metrics (updated when we re-fetch from GitHub)
    stars = models.IntegerField(
        default=0,
        help_text="Number of stars"
    )

    forks = models.IntegerField(
        default=0,
        help_text="Number of forks"
    )

    # Cache management timestamps
    last_fetched = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When we last fetched data from GitHub"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this record was created"
    )

    class Meta:
        ordering = ['-stars', 'name']  # Most popular first
        verbose_name = 'Repository'
        verbose_name_plural = 'Repositories'

        # Indexes for performance (speed up common queries)
        indexes = [
            models.Index(fields=['owner', 'name']),  # Search by owner/name
            models.Index(fields=['-stars']),  # Sort by popularity
        ]

    def __str__(self):
        return self.full_name

    def update_last_fetched(self):
        """
        Update last_fetched to current time.

        Uses update_fields for performance - only updates this one field
        instead of all fields (faster SQL UPDATE).
        """
        self.last_fetched = timezone.now()
        self.save(update_fields=['last_fetched'])


class CodeFile(models.Model):
    """
    Stores Python code content fetched from GitHub.

    Caches file contents to avoid re-fetching from GitHub. Trade-off: uses
    disk space (~50KB per 1000-line file) but saves API calls and time.
    """

    # Relationship to parent Repository
    repository = models.ForeignKey(
        Repository,
        on_delete=models.CASCADE,  # Delete files when repo deleted
        related_name='code_files',  # Access as repo.code_files.all()
        help_text="Repository this file belongs to"
    )

    # File identification
    path = models.CharField(
        max_length=500,  # Some repos have deep directory structures
        help_text="File path within repository"
    )

    name = models.CharField(
        max_length=255,
        help_text="File name"
    )

    # File content
    content = models.TextField(
        help_text="Python code content"
    )

    size = models.IntegerField(
        default=0,
        help_text="File size in bytes"
    )

    # Metadata
    fetched_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this file was fetched from GitHub"
    )

    class Meta:
        ordering = ['repository', 'path']
        verbose_name = 'Code File'
        verbose_name_plural = 'Code Files'

        # Prevent duplicate files - (repository, path) must be unique
        # Use get_or_create() or update_or_create() to handle this gracefully
        unique_together = ['repository', 'path']

        indexes = [
            models.Index(fields=['repository', 'name']),  # Find files by name
        ]
        # Note: unique_together creates index automatically, don't duplicate

    def __str__(self):
        return f"{self.repository.full_name}/{self.path}"

    def get_line_count(self):
        """
        Count lines in file.

        Not stored as field (would be denormalization). Calculating on-demand
        is fast enough (~1ms for 1000 lines) and keeps data normalized.
        """
        return len(self.content.splitlines())