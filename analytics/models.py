"""
Database models for the analytics app.

Stores code analysis results with proper normalization: AnalysisResult for
overall metrics, FunctionMetric for per-function details. This enables
querying like "show all functions with complexity > 10" rather than storing
JSON blobs.

Design decision: Store BOTH GitHub CodeFile reference AND source code copy.
CodeFile links to origin, source_code preserves what was analyzed (GitHub
code may change). Point-in-time snapshot for historical accuracy.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from github_integration.models import CodeFile


class AnalysisResult(models.Model):
    """
    Overall results from analyzing Python code.

    Parent model in one-to-many relationship with FunctionMetric.
    One analysis can have many function metrics.
    """

    # Optional GitHub file reference (null if pasted code)
    code_file = models.ForeignKey(
        CodeFile,
        on_delete=models.CASCADE,  # Delete analyses if file deleted
        null=True,
        blank=True,
        related_name='analyses',
        help_text="GitHub code file that was analyzed"
    )

    # Point-in-time snapshot of analyzed code
    source_code = models.TextField(
        help_text="Source code that was analyzed"
    )

    # Complexity metrics
    cyclomatic_complexity = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="McCabe cyclomatic complexity"
    )

    code_lines = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Number of lines of code"
    )

    num_functions = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Number of functions"
    )

    num_classes = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Number of classes"
    )

    max_nesting_depth = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Maximum nesting depth"
    )

    # 0-100 score (higher = better maintainability)
    maintainability_index = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Maintainability index (0-100)"
    )

    analyzed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this analysis was performed"
    )

    class Meta:
        ordering = ['-analyzed_at']  # Newest first
        verbose_name = 'Analysis Result'
        verbose_name_plural = 'Analysis Results'

    def __str__(self):
        """Show GitHub filename or analysis date."""
        if self.code_file:
            return f"Analysis of {self.code_file.name}"
        return f"Analysis from {self.analyzed_at.strftime('%Y-%m-%d %H:%M')}"

    def get_complexity_rating(self):
        """
        Human-readable complexity rating.

        Thresholds based on McCabe research:
        - 1-10: Low (recommended max)
        - 11-20: Medium
        - 21-50: High (refactor recommended)
        - 51+: Very High
        """
        if self.cyclomatic_complexity <= 10:
            return 'Low'
        elif self.cyclomatic_complexity <= 20:
            return 'Medium'
        elif self.cyclomatic_complexity <= 50:
            return 'High'
        else:
            return 'Very High'

    def get_maintainability_rating(self):
        """
        Human-readable maintainability rating.

        Thresholds (higher = better):
        - 80-100: Excellent
        - 60-79: Good
        - 40-59: Fair
        - 0-39: Poor
        """
        if self.maintainability_index >= 80:
            return 'Excellent'
        elif self.maintainability_index >= 60:
            return 'Good'
        elif self.maintainability_index >= 40:
            return 'Fair'
        else:
            return 'Poor'


class FunctionMetric(models.Model):
    """
    Complexity metrics for individual functions.

    Why separate model: Enables querying/sorting functions across analyses.
    Better than storing as JSON - proper types, validation, relationships.

    One AnalysisResult has many FunctionMetrics.
    """

    # Parent analysis
    analysis = models.ForeignKey(
        AnalysisResult,
        on_delete=models.CASCADE,  # Delete metrics with parent
        related_name='function_metrics'
    )

    name = models.CharField(
        max_length=200,
        help_text="Function name"
    )

    line_number = models.IntegerField(
        help_text="Line number where function is defined"
    )

    num_lines = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Number of lines in function"
    )

    # Many parameters (>5) suggests poor design
    num_params = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Number of parameters"
    )

    # Min 1 because every function has at least complexity 1
    complexity = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Cyclomatic complexity of this function"
    )

    max_depth = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Maximum nesting depth"
    )

    class Meta:
        ordering = ['-complexity', 'name']  # Most complex first

    def __str__(self):
        """Show function name and complexity."""
        return f"{self.name} (complexity: {self.complexity})"