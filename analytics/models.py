"""
Models for the analytics app.

Stores code analysis results and performance benchmarks.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from github_integration.models import CodeFile


class AnalysisResult(models.Model):
    """
    Stores results of code complexity analysis.

    Attributes:
        code_file: Optional reference to analyzed GitHub file
        source_code: The code that was analyzed (if not from GitHub)
        cyclomatic_complexity: Total cyclomatic complexity
        code_lines: Number of code lines
        num_functions: Number of functions
        num_classes: Number of classes
        max_nesting_depth: Maximum nesting depth found
        maintainability_index: Maintainability score (0-100)
        analyzed_at: When this analysis was performed
    """

    code_file = models.ForeignKey(
        CodeFile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='analyses',
        help_text="GitHub code file that was analyzed"
    )

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

    maintainability_index = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Maintainability index (0-100)"
    )

    # Metadata
    analyzed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this analysis was performed"
    )

    class Meta:
        ordering = ['-analyzed_at']
        verbose_name = 'Analysis Result'
        verbose_name_plural = 'Analysis Results'

    def __str__(self):
        if self.code_file:
            return f"Analysis of {self.code_file.name}"
        return f"Analysis from {self.analyzed_at.strftime('%Y-%m-%d %H:%M')}"

    def get_complexity_rating(self):
        """
        Get a rating based on cyclomatic complexity.

        Returns:
            str: 'Low', 'Medium', 'High', or 'Very High'
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
        Get a rating based on maintainability index.

        Returns:
            str: 'Excellent', 'Good', 'Fair', or 'Poor'
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
    Stores metrics for individual functions.

    This allows tracking complexity at the function level.
    """

    analysis = models.ForeignKey(
        AnalysisResult,
        on_delete=models.CASCADE,
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

    num_params = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Number of parameters"
    )

    complexity = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Cyclomatic complexity of this function"
    )

    max_depth = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Maximum nesting depth"
    )

    class Meta:
        ordering = ['-complexity', 'name']

    def __str__(self):
        return f"{self.name} (complexity: {self.complexity})"