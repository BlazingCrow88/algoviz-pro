"""
Database models for the algorithms app.

Why I needed these models:
The whole point of this project is to visualize and analyze algorithms, so I
needed to store information about each algorithm (name, complexity, etc.) and
track every time an algorithm runs (execution time, comparisons, swaps).

Design decision: Split into TWO models instead of one:
- Algorithm: Stores static info about each algorithm (one record per algorithm)
- ExecutionLog: Stores dynamic data from each run (many records per algorithm)

This is a classic one-to-many relationship in database design. I could have
combined them, but then I'd duplicate algorithm metadata for every execution,
which would be inefficient and harder to maintain.

Django note: These models become database tables automatically when we run
'python manage.py migrate'. Django's ORM is way better than writing SQL by hand!
"""
from django.db import models
from django.core.validators import MinValueValidator


class Algorithm(models.Model):
    """
    Stores metadata about each algorithm in the system.

    Why this model exists: We need a central place to store information about
    each algorithm - its name, what category it belongs to, complexity analysis,
    etc. This acts like a "catalog" of available algorithms.

    Real-world use: When a user selects "Bubble Sort" from the dropdown, we query
    this model to get its complexity info to display on the visualization page.

    Database note: Each Algorithm record can have many ExecutionLog records
    (through the foreign key relationship), but each Algorithm only exists once.
    """

    # Category choices - keeping it simple with just three main types
    # Could expand this later (like adding "tree" or "dynamic programming")
    # but these three cover all the algorithms I implemented for this project
    CATEGORY_CHOICES = [
        ('SORT', 'Sorting'),      # Bubble, Merge, Quick Sort
        ('SEARCH', 'Searching'),  # Binary Search, Linear Search, BFS
        ('GRAPH', 'Graph'),       # BFS (also counts as graph algorithm)
    ]

    # --- BASIC INFORMATION FIELDS ---

    name = models.CharField(
        max_length=100,
        unique=True,  # Can't have two algorithms with same name - prevents duplicates
        help_text="Name of the algorithm (e.g., 'Bubble Sort')"
    )
    # Note: unique=True creates a database index automatically, which speeds up lookups

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,  # Restricts to valid categories - prevents typos
        help_text="Algorithm category"
    )
    # Using choices instead of free text because we want consistent categorization
    # for filtering and display purposes

    description = models.TextField(
        help_text="Detailed description of how the algorithm works"
    )
    # TextField instead of CharField because descriptions can be long (no length limit)

    # --- COMPLEXITY ANALYSIS FIELDS ---
    # These are the CS theory part - storing Big-O notation for each case

    time_complexity_best = models.CharField(
        max_length=50,
        help_text="Best-case time complexity in Big-O notation"
    )
    # Example: "O(n)" for Bubble Sort on already-sorted array

    time_complexity_average = models.CharField(
        max_length=50,
        help_text="Average-case time complexity in Big-O notation"
    )
    # This is usually what matters most in practice

    time_complexity_worst = models.CharField(
        max_length=50,
        help_text="Worst-case time complexity in Big-O notation"
    )
    # Example: "O(n²)" for Bubble Sort on reverse-sorted array

    space_complexity = models.CharField(
        max_length=50,
        help_text="Space complexity in Big-O notation"
    )
    # Measures extra memory needed - important for large datasets

    # --- ALGORITHM PROPERTIES ---

    is_stable = models.BooleanField(
        default=False,  # Most algorithms aren't stable, so False is safer default
        help_text="Whether the algorithm is stable (maintains relative order of equal elements)"
    )
    # Stability matters when sorting complex objects (like sorting students by grade,
    # then by name - stable sort preserves the name order for students with same grade)

    # --- METADATA ---

    created_at = models.DateTimeField(
        auto_now_add=True,  # Django sets this automatically on creation
        help_text="When this algorithm was added to the database"
    )
    # Useful for tracking when algorithms were added during project development

    class Meta:
        """
        Django Meta options for model configuration.

        These control how Django handles queries and how the model appears
        in the admin interface.
        """

        # Default ordering for querysets - shows algorithms grouped by category
        # then alphabetically by name. Makes the admin panel and views more organized.
        ordering = ['category', 'name']

        # How the model appears in the admin panel (singular and plural)
        verbose_name = 'Algorithm'
        verbose_name_plural = 'Algorithms'  # Django would auto-generate "Algorithms" anyway, but being explicit

        # Database indexes for faster queries
        # These speed up common lookups like "get all sorting algorithms" or "find algorithm by name"
        indexes = [
            models.Index(fields=['category']),  # Fast filtering by category
            models.Index(fields=['name']),      # Fast lookups by name
        ]
        # Trade-off: Indexes make SELECT queries faster but INSERT/UPDATE slightly slower
        # Worth it here because we query algorithms often but rarely add new ones

    def __str__(self):
        """
        String representation for displaying in admin and templates.

        Shows algorithm name with category in parentheses.
        Example: "Bubble Sort (Sorting)"

        Django calls this method whenever it needs to display an Algorithm object
        as a string (in admin dropdowns, error messages, etc.)
        """
        return f"{self.name} ({self.get_category_display()})"
        # get_category_display() is a Django magic method that converts 'SORT' to 'Sorting'

    def get_complexity_summary(self):
        """
        Generate a one-line summary of time complexity for all cases.

        This is useful for displaying on algorithm comparison pages where we want
        to show all three cases without taking up much space.

        Returns:
            str: Formatted complexity summary
                 Example: "Best: O(n), Avg: O(n²), Worst: O(n²)"

        Usage example:
            In template: {{ algorithm.get_complexity_summary }}
        """
        return (
            f"Best: {self.time_complexity_best}, "
            f"Avg: {self.time_complexity_average}, "
            f"Worst: {self.time_complexity_worst}"
        )


class ExecutionLog(models.Model):
    """
    Records performance metrics from each algorithm execution.

    Why separate from Algorithm model: We want to track EVERY time an algorithm
    runs, not just store one set of stats. This lets us:
    - See how performance changes with input size
    - Compare the same algorithm with different inputs
    - Analyze trends (is Quick Sort really faster than Merge Sort in practice?)

    Design decision: These are created automatically by the views when users run
    visualizations - NOT meant to be created manually (hence the admin restriction
    in admin.py that prevents adding logs through the admin panel).

    Real-world scenario: If a user visualizes Bubble Sort with 50 elements 3 times,
    we'll have 3 ExecutionLog records all pointing to the same Algorithm record.
    """

    # Foreign key creates the one-to-many relationship
    # One Algorithm can have many ExecutionLogs, but each log belongs to one Algorithm
    algorithm = models.ForeignKey(
        Algorithm,
        on_delete=models.CASCADE,  # If Algorithm is deleted, delete all its logs too
        related_name='executions',  # Lets us do: algorithm.executions.all()
        help_text="The algorithm that was executed"
    )
    # CASCADE is important: If we delete "Bubble Sort" from the database, we also
    # delete all execution logs for it (prevents orphaned data)

    # --- EXECUTION CONTEXT ---

    input_size = models.IntegerField(
        validators=[MinValueValidator(0)],  # Can't have negative input size
        help_text="Number of elements in the input"
    )
    # This is KEY for complexity analysis - lets us see how execution time grows
    # with input size to verify our Big-O analysis

    # --- PERFORMANCE METRICS ---

    execution_time_ms = models.FloatField(
        validators=[MinValueValidator(0.0)],  # Time can't be negative
        help_text="Execution time in milliseconds"
    )
    # FloatField because execution time isn't always a whole number
    # Using milliseconds (not seconds) gives more precision for fast algorithms

    comparisons = models.IntegerField(
        null=True,  # Some algorithms don't track comparisons
        blank=True,  # OK to leave blank in forms
        validators=[MinValueValidator(0)],
        help_text="Number of comparison operations"
    )
    # Null/blank because searching algorithms might not count comparisons the same way
    # as sorting algorithms

    swaps = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Number of swap operations (for sorting algorithms)"
    )
    # Only relevant for sorting algorithms - searching algorithms don't swap
    # That's why null=True/blank=True

    # --- METADATA ---

    executed_at = models.DateTimeField(
        auto_now_add=True,  # Automatically set to current time when log is created
        help_text="When this execution occurred"
    )
    # Using auto_now_add (not auto_now) because we want timestamp of creation,
    # not last modification

    class Meta:
        """Model configuration for ExecutionLog."""

        ordering = ['-executed_at']  # Negative sign = newest first (descending)
        # Makes sense for logs - usually want to see most recent executions first

        verbose_name = 'Execution Log'
        verbose_name_plural = 'Execution Logs'

        # Indexes for common query patterns
        indexes = [
            # Index on executed_at (descending) for "show me recent executions"
            models.Index(fields=['-executed_at']),

            # Composite index for "show me all executions of Bubble Sort with 100 elements"
            models.Index(fields=['algorithm', 'input_size']),
        ]
        # These speed up the analytics page where we compare algorithm performance

    def __str__(self):
        """
        String representation showing the key info at a glance.

        Format: "Bubble Sort - 50 elements - 12.34ms"

        Helps when looking at logs in the admin panel or in error messages -
        you can immediately see what algorithm ran, how much data, and how long it took.
        """
        return (
            f"{self.algorithm.name} - "
            f"{self.input_size} elements - "
            f"{self.execution_time_ms:.2f}ms"  # .2f rounds to 2 decimal places
        )

    def get_operations_summary(self):
        """
        Generate a readable summary of comparisons and swaps.

        Why this method: Different algorithms track different metrics. Sorting
        algorithms track both comparisons and swaps, but searching algorithms
        might only track comparisons. This method handles all cases gracefully.

        Returns:
            str: Summary of operations performed
                 Examples:
                 - "Comparisons: 45, Swaps: 23" (sorting algorithm)
                 - "Comparisons: 8" (searching algorithm)
                 - "No operation data" (if tracking wasn't enabled)

        Usage: Can display this in templates or admin to see operation counts
        """
        parts = []

        # Only include comparisons if we tracked them
        if self.comparisons is not None:
            parts.append(f"Comparisons: {self.comparisons}")

        # Only include swaps if we tracked them
        if self.swaps is not None:
            parts.append(f"Swaps: {self.swaps}")

        # Return formatted string, or fallback if no data
        return ", ".join(parts) if parts else "No operation data"
        # Could happen if an algorithm execution failed before tracking started