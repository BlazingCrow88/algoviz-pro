"""
Database models for the GitHub integration app.

What this stores: When we fetch data from GitHub (using api_client.py), we
save it to the database so we don't have to fetch it again. This is critical
for two reasons:
1. **Rate Limits**: GitHub only allows 5000 API calls per hour. Without caching
   in the database, we'd hit that limit fast.
2. **Speed**: Fetching from our database takes ~5ms, fetching from GitHub API
   takes ~500ms. Database is 100x faster.

Why two models: We separate Repository (metadata about the repo) from CodeFile
(actual code contents) because:
- One repository has MANY code files (one-to-many relationship)
- We might want repository info without fetching all its files
- Proper database normalization (don't duplicate repo info for every file)

Data lifecycle:
1. User searches for a repository → save Repository record
2. User views repository → update last_fetched timestamp
3. User selects a file → save CodeFile record with content
4. Next time user wants same file → fetch from database (instant!)
5. If data is stale (old last_fetched) → re-fetch from GitHub API

This is a classic **cache pattern** - store expensive API results in fast local
database to avoid redundant slow API calls.
"""
from django.db import models
from django.core.validators import URLValidator
from django.utils import timezone


class Repository(models.Model):
    """
    Stores metadata about a GitHub repository.

    This is the "parent" in a one-to-many relationship with CodeFile.
    One repository can have many code files.

    Why store this: When user searches for repos, we cache the results so:
    1. Next search is instant (no GitHub API call)
    2. We can show "recently viewed" without re-fetching
    3. We preserve data even if repo is deleted from GitHub

    What we DON'T store: Everything! GitHub returns 100+ fields per repo
    (issues, pull requests, contributors, etc.). We only store what we need
    for our UI. This keeps our database lean and queries fast.

    Example usage:
        # Save a repository from GitHub search
        repo = Repository.objects.create(
            full_name='django/django',
            name='django',
            owner='django',
            description='The Web framework for perfectionists...',
            url='https://github.com/django/django',
            language='Python',
            stars=75000,
            forks=30000
        )

        # Later, fetch it
        repo = Repository.objects.get(full_name='django/django')
        print(f"Django has {repo.stars} stars!")
    """

    # REPOSITORY IDENTIFICATION
    # ========================

    # Full name uniquely identifies a repository on GitHub
    # Format: "owner/repository" like "django/django" or "torvalds/linux"
    #
    # Why unique=True: Can't have two repos with same full_name in our database
    # This creates a database UNIQUE constraint and index automatically
    #
    # Why max_length=200: GitHub limits are 100 chars for owner + 100 for repo
    # So 200 is generous enough
    full_name = models.CharField(
        max_length=200,
        unique=True,  # Database-level uniqueness constraint
        help_text="Full repository name (owner/repo)"
    )

    # Repository name only (without owner)
    # Example: "django" (from "django/django")
    #
    # Why store separately when we have full_name: Makes queries easier
    # Can filter by name: Repository.objects.filter(name='django')
    # Without this, would need: full_name__endswith='/django' (ugly)
    name = models.CharField(
        max_length=100,
        help_text="Repository name"
    )

    # Repository owner (username or organization)
    # Example: "django" (from "django/django")
    #
    # Why store separately: Same reason as name - easier filtering
    # Can find all repos by an owner: Repository.objects.filter(owner='django')
    owner = models.CharField(
        max_length=100,
        help_text="Repository owner username"
    )

    # REPOSITORY METADATA
    # ===================

    # Description of what the repository does
    # blank=True: OK to have no description (some repos don't have one)
    # default='': Empty string instead of NULL (Django convention for text fields)
    #
    # Why TextField not CharField: Descriptions can be long (1000+ characters)
    # TextField has no length limit, CharField requires max_length
    description = models.TextField(
        blank=True,
        default='',
        help_text="Repository description"
    )

    # GitHub web URL (what you'd click in a browser)
    # Example: "https://github.com/django/django"
    #
    # URLValidator: Django validates this is a proper URL format
    # Prevents storing invalid URLs like "not a url" or "ftp://wrong-protocol"
    #
    # Why URLField: Special field type that automatically includes URLValidator
    # Also renders as <input type="url"> in forms (gives mobile users URL keyboard)
    url = models.URLField(
        validators=[URLValidator()],
        help_text="GitHub repository URL"
    )

    # Primary programming language of the repository
    # Examples: "Python", "JavaScript", "Java", etc.
    #
    # blank=True: Some repos don't have a detected language (mostly documentation)
    # max_length=50: Should be enough for any language name
    language = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="Primary programming language"
    )

    # POPULARITY METRICS
    # ==================
    # These change over time, so we update them when we re-fetch from GitHub

    # Number of stars (GitHub's "like" metric)
    # Popular repos have 10,000+ stars, some have 100,000+
    # default=0: New repos start with 0 stars
    stars = models.IntegerField(
        default=0,
        help_text="Number of stars"
    )

    # Number of forks (how many people copied the repo)
    # Indicates how many people are building on top of it
    forks = models.IntegerField(
        default=0,
        help_text="Number of forks"
    )

    # CACHE MANAGEMENT
    # ================

    # When we last fetched data from GitHub for this repo
    # null=True, blank=True: Initially NULL (never fetched yet)
    #
    # Why we need this: To know if our cached data is stale
    # If last_fetched was 2 days ago, we might want to re-fetch
    # If last_fetched was 5 minutes ago, use cached data
    #
    # Implementation note: We manually update this with update_last_fetched()
    # method. Could use auto_now=True but we want manual control.
    last_fetched = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When we last fetched data from GitHub"
    )

    # When we created this database record
    # auto_now_add=True: Django sets this automatically on creation (never changes)
    #
    # Difference from last_fetched:
    # - created_at: When we first added this repo to our database (never changes)
    # - last_fetched: When we last updated it from GitHub (changes on refresh)
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this record was created"
    )

    class Meta:
        """Django model configuration."""

        # Default ordering: Most popular first, then alphabetically
        # '-stars' means descending (most to least), 'name' means ascending (A-Z)
        #
        # Why this order: Users usually care about popular repos first
        # When displaying repositories, showing highest-starred first makes sense
        ordering = ['-stars', 'name']

        # How model appears in Django admin
        verbose_name = 'Repository'
        verbose_name_plural = 'Repositories'  # Not "Repositorys"

        # DATABASE INDEXES FOR PERFORMANCE
        # ================================
        # Indexes speed up queries but use disk space and slow down writes
        # Trade-off: Faster SELECTs, slower INSERTs/UPDATEs
        #
        # We create indexes on fields we frequently query or sort by
        indexes = [
            # Composite index on (owner, name)
            # Speeds up: Repository.objects.get(owner='django', name='django')
            # Why: Users often search by "owner/name" combination
            # This is essentially an index on full_name split into parts
            models.Index(fields=['owner', 'name']),

            # Index on stars (descending)
            # Speeds up: Repository.objects.order_by('-stars')
            # Why: We order by stars in our default ordering (see above)
            # Without this index, database would have to sort every time
            # With index, it's pre-sorted (instant)
            models.Index(fields=['-stars']),
        ]

        # Why NOT index every field:
        # - Indexes use disk space (duplicate data in special structure)
        # - Indexes slow down writes (need to update index on every INSERT/UPDATE)
        # - Only index fields you actually query/sort by frequently

    def __str__(self):
        """
        String representation for admin and debugging.

        Shows full_name (like "django/django") instead of generic "Repository object (1)"
        Makes Django admin much more readable.

        Example: In admin, you see "django/django" not "Repository object (42)"
        """
        return self.full_name

    def update_last_fetched(self):
        """
        Update the last_fetched timestamp to now.

        This is a MANUAL timestamp update (not automatic like auto_now=True).
        We want manual control so we only update when we ACTUALLY fetch from GitHub,
        not every time we save the model for any reason.

        Why update_fields=['last_fetched']: Performance optimization
        Only updates this one field in the database, not all fields.

        SQL executed:
            UPDATE github_integration_repository
            SET last_fetched = '2024-12-01 15:30:00'
            WHERE id = 42;

        Instead of updating ALL fields (slower):
            UPDATE github_integration_repository
            SET full_name=..., name=..., owner=..., [all 10 fields]
            WHERE id = 42;

        Usage:
            repo = Repository.objects.get(full_name='django/django')
            # ... fetch fresh data from GitHub API ...
            repo.stars = new_star_count  # Update with fresh data
            repo.save()  # Save the changes
            repo.update_last_fetched()  # Mark as freshly fetched
        """
        self.last_fetched = timezone.now()  # Current time in UTC
        self.save(update_fields=['last_fetched'])  # Only update this field


class CodeFile(models.Model):
    """
    Stores actual Python code content fetched from GitHub.

    This is the "child" in a one-to-many relationship with Repository.
    Each CodeFile belongs to exactly one Repository.

    Why store code in database: Same reason as Repository - caching!
    - GitHub API calls are slow (500ms) and rate-limited
    - Database queries are fast (5ms) and unlimited
    - Once we fetch a file, store it so we don't fetch again

    Trade-off consideration: Code files can be LARGE (100KB+). Storing many
    files uses significant disk space. But disk is cheap and API calls are
    limited, so it's worth it.

    Example usage:
        # Fetch a file from GitHub and save it
        file = CodeFile.objects.create(
            repository=repo,
            path='django/core/handlers/wsgi.py',
            name='wsgi.py',
            content='<actual Python code>',
            size=5432
        )

        # Later, retrieve it instantly
        file = CodeFile.objects.get(repository=repo, path='django/core/handlers/wsgi.py')
        print(file.content)  # No GitHub API call needed!
    """

    # RELATIONSHIP TO REPOSITORY
    # ==========================

    # Foreign key to parent Repository
    #
    # CASCADE behavior: If Repository is deleted, delete all its CodeFiles too
    # Why CASCADE: CodeFiles don't make sense without their repository
    # If we delete "django/django" repo, we should delete all its Python files too
    # Otherwise we'd have orphaned files (no parent repo)
    #
    # related_name='code_files': Reverse relationship name
    # Lets us do: repo.code_files.all() to get all files in a repository
    # Without related_name, would be: repo.codefile_set.all() (ugly)
    #
    # Example of CASCADE:
    #   repo = Repository.objects.get(full_name='django/django')
    #   repo.delete()  # Deletes repo AND all its CodeFile records automatically
    repository = models.ForeignKey(
        Repository,
        on_delete=models.CASCADE,  # Delete files when repo is deleted
        related_name='code_files',  # Access as repo.code_files.all()
        help_text="Repository this file belongs to"
    )

    # FILE IDENTIFICATION
    # ===================

    # Full path within repository
    # Example: "django/core/handlers/wsgi.py"
    #
    # Why max_length=500: Some repos have DEEP directory structures
    # Path like "src/very/deeply/nested/directories/and/more/file.py" can be long
    # 500 should handle most cases, GitHub's actual limit is much longer
    path = models.CharField(
        max_length=500,
        help_text="File path within repository"
    )

    # Just the filename (without directory path)
    # Example: "wsgi.py"
    #
    # Why store separately from path: Makes filtering easier
    # Can find all files named "test.py": CodeFile.objects.filter(name='test.py')
    # Without this, would need complex regex on path field
    name = models.CharField(
        max_length=255,
        help_text="File name"
    )

    # FILE CONTENT
    # ============

    # The actual Python code as text
    #
    # Why TextField: Code files can be LONG (10,000+ lines)
    # TextField has no length limit, can store entire files
    #
    # Storage consideration: A 1000-line file might be 50KB of text
    # If we cache 1000 files, that's 50MB of database storage
    # This is acceptable - disk is cheap, API calls are limited
    #
    # Alternative considered: Could store just file metadata and fetch content
    # on-demand from GitHub. But that defeats the caching purpose.
    content = models.TextField(
        help_text="Python code content"
    )

    # File size in bytes
    # Helps us decide whether to fetch a file (skip very large files)
    # Also useful for showing "This is a 10KB file" in UI
    size = models.IntegerField(
        default=0,
        help_text="File size in bytes"
    )

    # METADATA
    # ========

    # When we fetched this file from GitHub
    # auto_now_add=True: Set automatically when record is created
    #
    # Could also use last_fetched pattern like Repository, but for simplicity
    # we just track when we first fetched it. If we need fresh content,
    # we delete the old record and create a new one.
    fetched_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this file was fetched from GitHub"
    )

    class Meta:
        """Django model configuration."""

        # Default ordering: By repository, then by path
        # Groups files from same repo together, sorts paths alphabetically
        # Makes sense when displaying "files in this repository"
        ordering = ['repository', 'path']

        verbose_name = 'Code File'
        verbose_name_plural = 'Code Files'

        # UNIQUE CONSTRAINT
        # =================
        # Prevent duplicate files: Can't have two records for the same file
        # Combination of (repository, path) must be unique
        #
        # Why: A file like "django/django:django/core/wsgi.py" should only exist
        # once in our database. Without this, we could accidentally create duplicates
        # when fetching the same file multiple times.
        #
        # Database creates a composite unique index on (repository_id, path)
        #
        # What happens if we try to create duplicate:
        #   CodeFile.objects.create(repository=repo, path='same/path.py', ...)
        #   CodeFile.objects.create(repository=repo, path='same/path.py', ...)  # ERROR!
        # Django raises IntegrityError
        #
        # How we handle: Use get_or_create() instead of create()
        #   file, created = CodeFile.objects.get_or_create(
        #       repository=repo,
        #       path='path.py',
        #       defaults={'content': '...', 'size': 100}
        #   )
        # If file exists, get it. If not, create it. No error!
        unique_together = ['repository', 'path']

        # INDEXES
        # =======
        indexes = [
            # Composite index on (repository, name)
            # Speeds up: repo.code_files.filter(name='wsgi.py')
            # Useful for "find all wsgi.py files in this repository"
            models.Index(fields=['repository', 'name']),
        ]

        # Note: unique_together automatically creates an index, so we don't need
        # to explicitly index (repository, path) - it's already indexed!

    def __str__(self):
        """
        String representation showing full path in repository.

        Format: "django/django/django/core/wsgi.py"
        Shows both repo and file path so it's clear what file this is.

        Example in admin: See "django/django/setup.py" not "CodeFile object (42)"
        """
        return f"{self.repository.full_name}/{self.path}"

    def get_line_count(self):
        """
        Calculate number of lines in the file.

        Why not store line_count as a field: It's derivable from content
        Storing it would be denormalization (duplicate data).

        Trade-off:
        - Calculating: Takes ~1ms for 1000-line file (splitlines is fast)
        - Storing: Uses 4 bytes per record, but saves computation

        For our use case, calculating on-demand is fine. Line count isn't
        queried frequently enough to justify storing it.

        Implementation: splitlines() handles different line endings:
        - Unix: \n
        - Windows: \r\n
        - Old Mac: \r

        Returns:
            int: Number of lines in the file

        Example:
            file = CodeFile.objects.get(name='wsgi.py')
            print(f"This file has {file.get_line_count()} lines")
        """
        return len(self.content.splitlines())