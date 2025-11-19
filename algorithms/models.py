"""
Models for the algorithms app.

This module defines database models for storing algorithm metadata and
execution logs for benchmarking purposes.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Algorithm(models.Model):
    """
    Stores metadata about each algorithm implementation.

    This model tracks the name, category, complexity analysis, and other
    properties of algorithms available in the system.

    Attributes:
        name: Human-readable algorithm name (e.g., "Bubble Sort")
        category: Algorithm category (sorting, searching, or graph)
        description: Detailed explanation of how the algorithm works
        time_complexity_best: Best-case time complexity (e.g., "O(n)")
        time_complexity_average: Average-case time complexity
        time_complexity_worst: Worst-case time complexity
        space_complexity: Space complexity (auxiliary space used)
        is_stable: Whether the algorithm maintains relative order of equal elements
        created_at: Timestamp when this record was created
    """

    # Category choices for algorithm classification
    CATEGORY_CHOICES = [
        ('SORT', 'Sorting'),
        ('SEARCH', 'Searching'),
        ('GRAPH', 'Graph'),
    ]

    # Basic information
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Name of the algorithm (e.g., 'Bubble Sort')"
    )

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        help_text="Algorithm category"
    )

    description = models.TextField(
        help_text="Detailed description of how the algorithm works"
    )

    # Complexity analysis
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

    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this algorithm was added to the database"
    )

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Algorithm'
        verbose_name_plural = 'Algorithms'
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        """String representation showing name and category."""
        return f"{self.name} ({self.get_category_display()})"

    def get_complexity_summary(self):
        """
        Returns a formatted summary of time complexities.

        Returns:
            str: Formatted string like "Best: O(n), Avg: O(n²), Worst: O(n²)"
        """
        return (
            f"Best: {self.time_complexity_best}, "
            f"Avg: {self.time_complexity_average}, "
            f"Worst: {self.time_complexity_worst}"
        )


class ExecutionLog(models.Model):
    """
    Logs individual algorithm executions for benchmarking and analysis.

    Each time an algorithm is executed, we log the performance metrics to
    enable comparison and analysis of different algorithms and input sizes.

    Attributes:
        algorithm: Foreign key to the Algorithm that was executed
        input_size: Number of elements in the input array
        execution_time_ms: How long the algorithm took to run (milliseconds)
        comparisons: Number of comparison operations performed
        swaps: Number of swap operations performed (for sorting algorithms)
        executed_at: Timestamp when the algorithm was executed
    """

    algorithm = models.ForeignKey(
        Algorithm,
        on_delete=models.CASCADE,
        related_name='executions',
        help_text="The algorithm that was executed"
    )

    input_size = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Number of elements in the input"
    )

    execution_time_ms = models.FloatField(
        validators=[MinValueValidator(0.0)],
        help_text="Execution time in milliseconds"
    )

    comparisons = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Number of comparison operations"
    )

    swaps = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Number of swap operations (for sorting algorithms)"
    )

    executed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this execution occurred"
    )

    class Meta:
        ordering = ['-executed_at']  # Most recent first
        verbose_name = 'Execution Log'
        verbose_name_plural = 'Execution Logs'
        indexes = [
            models.Index(fields=['-executed_at']),
            models.Index(fields=['algorithm', 'input_size']),
        ]

    def __str__(self):
        """String representation with key metrics."""
        return (
            f"{self.algorithm.name} - "
            f"{self.input_size} elements - "
            f"{self.execution_time_ms:.2f}ms"
        )

    def get_operations_summary(self):
        """
        Returns a summary of operations performed.

        Returns:
            str: Formatted string like "Comparisons: 45, Swaps: 23"
        """
        parts = []
        if self.comparisons is not None:
            parts.append(f"Comparisons: {self.comparisons}")
        if self.swaps is not None:
            parts.append(f"Swaps: {self.swaps}")
        return ", ".join(parts) if parts else "No operation data"