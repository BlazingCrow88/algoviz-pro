"""
Models for the github_integration app.

Stores information about GitHub repositories and fetched code files.
"""
from django.db import models
from django.core.validators import URLValidator
from django.utils import timezone


class Repository(models.Model):
    """
    Stores metadata about a GitHub repository.

    Attributes:
        full_name: Repository full name (owner/repo)
        name: Repository name
        owner: Repository owner username
        description: Repository description
        url: GitHub URL
        language: Primary programming language
        stars: Number of stars
        forks: Number of forks
        last_fetched: When we last fetched data from this repo
        created_at: When this record was created
    """

    full_name = models.CharField(
        max_length=200,
        unique=True,
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

    stars = models.IntegerField(
        default=0,
        help_text="Number of stars"
    )

    forks = models.IntegerField(
        default=0,
        help_text="Number of forks"
    )

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
        ordering = ['-stars', 'name']
        verbose_name = 'Repository'
        verbose_name_plural = 'Repositories'
        indexes = [
            models.Index(fields=['owner', 'name']),
            models.Index(fields=['-stars']),
        ]

    def __str__(self):
        return self.full_name

    def update_last_fetched(self):
        """Update the last_fetched timestamp to now."""
        self.last_fetched = timezone.now()
        self.save(update_fields=['last_fetched'])


class CodeFile(models.Model):
    """
    Stores content of a fetched Python file from GitHub.

    Attributes:
        repository: Foreign key to Repository
        path: File path within repository
        name: File name
        content: File content (Python code)
        size: File size in bytes
        fetched_at: When this file was fetched
    """

    repository = models.ForeignKey(
        Repository,
        on_delete=models.CASCADE,
        related_name='code_files',
        help_text="Repository this file belongs to"
    )

    path = models.CharField(
        max_length=500,
        help_text="File path within repository"
    )

    name = models.CharField(
        max_length=255,
        help_text="File name"
    )

    content = models.TextField(
        help_text="Python code content"
    )

    size = models.IntegerField(
        default=0,
        help_text="File size in bytes"
    )

    fetched_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this file was fetched from GitHub"
    )

    class Meta:
        ordering = ['repository', 'path']
        verbose_name = 'Code File'
        verbose_name_plural = 'Code Files'
        unique_together = ['repository', 'path']
        indexes = [
            models.Index(fields=['repository', 'name']),
        ]

    def __str__(self):
        return f"{self.repository.full_name}/{self.path}"

    def get_line_count(self):
        """Return number of lines in the file."""
        return len(self.content.splitlines())