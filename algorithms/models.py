"""
Database models for the algorithms app.

Design decision: Split into two models for efficient data storage:
- Algorithm: Static metadata (one record per algorithm)
- ExecutionLog: Dynamic performance data (many records per algorithm)

This one-to-many relationship avoids duplicating algorithm metadata for every execution.
"""
from django.db import models
from django.core.validators import MinValueValidator


class Algorithm(models.Model):
    """
    Stores metadata about each algorithm in the system.

    Acts as a catalog of available algorithms with their complexity characteristics.
    Users select algorithms from this catalog for visualization.
    """

    CATEGORY_CHOICES = [
        ('SORT', 'Sorting'),      # Bubble, Merge, Quick Sort
        ('SEARCH', 'Searching'),  # Binary Search, Linear Search
        ('GRAPH', 'Graph'),       # BFS (not yet implemented due to time constraints)
    ]

    # Basic information
    name = models.CharField(
        max_length=100,
        unique=True,  # Prevents duplicate algorithm names
        help_text="Name of the algorithm (e.g., 'Bubble Sort')"
    )

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,  # Restricts to valid categories
        help_text="Algorithm category"
    )

    description = models.TextField(
        help_text="Detailed description of how the algorithm works"
    )

    # Complexity analysis - Big-O notation for each case
    time_complexity_best = models.CharField(
        max_length=50,
        help_text="Best-case time complexity in Big-O notation"
    )

    time_complexity_average = models.CharField(
        max_length=50,
        help_text="Average-case time complexity in Big-O notation"
    )

    time_complexity_worst = models.CharField(
        max_length=50,
        help_text="Worst-case time complexity in Big-O notation"
    )

    space_complexity = models.CharField(
        max_length=50,
        help_text="Space complexity in Big-O notation"
    )

    # Algorithm properties
    is_stable = models.BooleanField(
        default=False,
        help_text="Whether the algorithm is stable (maintains relative order of equal elements)"
    )
    # Stability matters for multi-field sorting scenarios

    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this algorithm was added to the database"
    )

    class Meta:
        # Order by category then name for organized display
        ordering = ['category', 'name']

        verbose_name = 'Algorithm'
        verbose_name_plural = 'Algorithms'

        # Indexes for common queries (category filtering, name lookups)
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        """String representation: "Bubble Sort (Sorting)" """
        return f"{self.name} ({self.get_category_display()})"

    def get_complexity_summary(self):
        """
        One-line complexity summary for comparison pages.

        Returns: "Best: O(n), Avg: O(n²), Worst: O(n²)"
        """
        return (
            f"Best: {self.time_complexity_best}, "
            f"Avg: {self.time_complexity_average}, "
            f"Worst: {self.time_complexity_worst}"
        )


class ExecutionLog(models.Model):
    """
    Records performance metrics from each algorithm execution.

    Why separate from Algorithm: Tracks every execution to analyze how performance
    changes with input size and compare actual vs theoretical complexity.

    Created automatically by views when users run visualizations - not meant for
    manual creation (enforced in admin.py).
    """

    # One Algorithm has many ExecutionLogs
    algorithm = models.ForeignKey(
        Algorithm,
        on_delete=models.CASCADE,  # Delete logs when algorithm is deleted
        related_name='executions',
        help_text="The algorithm that was executed"
    )

    # Execution context
    input_size = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Number of elements in the input"
    )
    # Key for verifying Big-O analysis by seeing how time grows with size

    # Performance metrics
    execution_time_ms = models.FloatField(
        validators=[MinValueValidator(0.0)],
        help_text="Execution time in milliseconds"
    )

    comparisons = models.IntegerField(
        null=True,  # Not all algorithms track comparisons
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Number of comparison operations"
    )

    swaps = models.IntegerField(
        null=True,  # Only relevant for sorting algorithms
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Number of swap operations (for sorting algorithms)"
    )

    # Metadata
    executed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this execution occurred"
    )

    class Meta:
        ordering = ['-executed_at']  # Newest first

        verbose_name = 'Execution Log'
        verbose_name_plural = 'Execution Logs'

        # Indexes for common queries
        indexes = [
            models.Index(fields=['-executed_at']),  # Recent executions
            models.Index(fields=['algorithm', 'input_size']),  # Performance comparisons
        ]

    def __str__(self):
        """String representation: "Bubble Sort - 50 elements - 12.34ms" """
        return (
            f"{self.algorithm.name} - "
            f"{self.input_size} elements - "
            f"{self.execution_time_ms:.2f}ms"
        )

    def get_operations_summary(self):
        """
        Readable summary of operations performed.

        Handles different tracking scenarios gracefully:
        - Sorting: "Comparisons: 45, Swaps: 23"
        - Searching: "Comparisons: 8"
        - No data: "No operation data"
        """
        parts = []

        if self.comparisons is not None:
            parts.append(f"Comparisons: {self.comparisons}")

        if self.swaps is not None:
            parts.append(f"Swaps: {self.swaps}")

        return ", ".join(parts) if parts else "No operation data"