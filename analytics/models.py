"""
Models for the analytics app.

These models store the complexity analysis results so we can track analysis history
and show users their past results. I split function metrics into a separate model
because one analysis can have many functions, and this way I can query and sort
individual functions by complexity.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from github_integration.models import CodeFile


class AnalysisResult(models.Model):
    """
    Main model for storing code complexity analysis results.

    I made code_file optional (null=True) because users can either analyze code
    from GitHub OR paste code directly. This flexibility was important for testing
    and for users who don't want to connect their GitHub.

    The various metric fields (cyclomatic_complexity, code_lines, etc.) mirror what
    the ComplexityAnalyzer calculates - storing them in the database lets us show
    analysis history and compare results over time.
    """

    # Link to GitHub file if the code came from there, otherwise null
    code_file = models.ForeignKey(
        CodeFile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='analyses',
        help_text="GitHub code file that was analyzed"
    )

    # Always store the actual code that was analyzed so we can reference it later
    source_code = models.TextField(
        help_text="Source code that was analyzed"
    )

    # Core complexity metrics - these come straight from the analyzer
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

    # 0-100 score for overall code quality - capped with validators to prevent bad data
    maintainability_index = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Maintainability index (0-100)"
    )

    # Track when analysis happened - auto_now_add means Django sets this automatically
    analyzed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this analysis was performed"
    )

    class Meta:
        # Show newest analyses first since users care about recent results
        ordering = ['-analyzed_at']
        verbose_name = 'Analysis Result'
        verbose_name_plural = 'Analysis Results'

    def __str__(self):
        # Show filename if from GitHub, otherwise show timestamp for pasted code
        if self.code_file:
            return f"Analysis of {self.code_file.name}"
        return f"Analysis from {self.analyzed_at.strftime('%Y-%m-%d %H:%M')}"

    def get_complexity_rating(self):
        """
        Convert raw complexity number into a readable rating.

        I used these thresholds based on common best practices - 10 or less is
        considered maintainable, over 50 is a red flag. Makes it easier for users
        to quickly understand if their code is problematic.
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
        Give a quality grade based on the maintainability index.

        80+ is excellent code, below 40 means there are serious issues.
        This makes the 0-100 score more intuitive for users who aren't familiar
        with maintainability metrics.
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
    Stores complexity metrics for individual functions within an analysis.

    I separated this into its own model instead of jamming it into AnalysisResult
    because one piece of code can have many functions, and this way I can:
    1. Query for the most complex functions across all analyses
    2. Sort functions by complexity to show users which ones need attention
    3. Keep the database normalized (one analysis -> many function metrics)

    The ForeignKey CASCADE means if you delete an analysis, all its function
    metrics get deleted too, which makes sense - no orphaned data.
    """

    # Each function metric belongs to one analysis result
    analysis = models.ForeignKey(
        AnalysisResult,
        on_delete=models.CASCADE,
        related_name='function_metrics'
    )

    name = models.CharField(
        max_length=200,
        help_text="Function name"
    )

    # Store line number so users can find the function in their code
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

    # Function-level complexity - minimum 1 since even empty functions have base complexity
    complexity = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Cyclomatic complexity of this function"
    )

    max_depth = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Maximum nesting depth"
    )

    class Meta:
        # Sort by complexity descending so the worst offenders show up first,
        # then alphabetically by name for consistent ordering
        ordering = ['-complexity', 'name']

    def __str__(self):
        return f"{self.name} (complexity: {self.complexity})"