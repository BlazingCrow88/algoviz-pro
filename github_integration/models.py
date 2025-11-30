"""
Models for the github_integration app.

Stores GitHub repository data and code files we fetch for analysis.
I kept this pretty simple - just two models that mirror what we need from
GitHub's API. The relationship is straightforward: one Repository can have
many CodeFiles.
"""
from django.db import models
from django.core.validators import URLValidator
from django.utils import timezone


class Repository(models.Model):
    """
    Stores metadata about GitHub repositories we've searched for or analyzed.

    I'm storing the basic info we get back from GitHub's API - stars, forks, etc.
    The last_fetched field is important for knowing when to refresh data from GitHub
    instead of using stale cached info.
    """

    full_name = models.CharField(
        max_length=200,
        unique=True,  # Can't have duplicate repos - this is our primary identifier
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
        blank=True,  # Not all repos have descriptions
        default='',
        help_text="Repository description"
    )

    url = models.URLField(
        validators=[URLValidator()],  # Make sure we're storing valid URLs
        help_text="GitHub repository URL"
    )

    language = models.CharField(
        max_length=50,
        blank=True,  # Some repos don't have a detected language
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
        auto_now_add=True,  # Automatically set when the record is created
        help_text="When this record was created"
    )

    class Meta:
        ordering = ['-stars', 'name']  # Show most popular repos first, then alphabetical
        verbose_name = 'Repository'
        verbose_name_plural = 'Repositories'
        indexes = [
            # These indexes speed up queries when filtering by owner/name or sorting by stars
            # Makes a big difference when the database gets larger
            models.Index(fields=['owner', 'name']),
            models.Index(fields=['-stars']),
        ]

    def __str__(self):
        return self.full_name

    def update_last_fetched(self):
        """
        Update the timestamp for when we last grabbed data from GitHub.

        Using update_fields here instead of just save() prevents accidentally
        overwriting other fields if they changed elsewhere. More defensive programming.
        """
        self.last_fetched = timezone.now()
        self.save(update_fields=['last_fetched'])


class CodeFile(models.Model):
    """
    Stores actual Python code files we've fetched from GitHub repos.

    These tie back to a Repository through a foreign key. When a repository gets
    deleted, all its code files get deleted too (CASCADE). This prevents orphaned
    files cluttering up the database.
    """

    repository = models.ForeignKey(
        Repository,
        on_delete=models.CASCADE,  # Delete files if their repo gets deleted
        related_name='code_files',  # So we can do repository.code_files.all()
        help_text="Repository this file belongs to"
    )

    path = models.CharField(
        max_length=500,  # Made this longer than name since paths can get deep in nested dirs
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
        auto_now_add=True,  # Track when we grabbed this file
        help_text="When this file was fetched from GitHub"
    )

    class Meta:
        ordering = ['repository', 'path']  # Keep files organized by repo, then by path
        verbose_name = 'Code File'
        verbose_name_plural = 'Code Files'
        unique_together = ['repository', 'path']  # Can't have duplicate file paths in the same repo
        indexes = [
            # Index for faster lookups when searching files by repo and name
            models.Index(fields=['repository', 'name']),
        ]

    def __str__(self):
        return f"{self.repository.full_name}/{self.path}"

    def get_line_count(self):
        """
        Count how many lines are in the file.

        Useful for displaying file stats in the UI or filtering out small/large files.
        """
        return len(self.content.splitlines())