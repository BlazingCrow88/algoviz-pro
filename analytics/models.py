"""
Database models for the analytics app - stores code analysis results.

What this stores: When we analyze code (using complexity_analyzer.py), we
want to save the results in the database so users can:
1. View analysis history (what they analyzed and when)
2. Compare analyses (is this code better than last version?)
3. Track trends (is their code getting more complex over time?)

Why two models: We split data into AnalysisResult (overall metrics) and
FunctionMetric (per-function details). This is database normalization -
instead of storing function data in a JSON blob, we use proper relationships
so we can query like "show me all functions with complexity > 10".

Design decision: We store BOTH a reference to the GitHub CodeFile AND a copy
of the source code. Why the redundancy?
- CodeFile reference: Links to where code came from (GitHub repo)
- source_code copy: Preserves what we analyzed (code on GitHub might change)
This lets users see "I analyzed version X which had complexity Y" even if
the GitHub file has since been updated.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from github_integration.models import CodeFile


class AnalysisResult(models.Model):
    """
    Stores overall results from analyzing a piece of Python code.

    This is the "parent" model in a one-to-many relationship with FunctionMetric.
    One AnalysisResult can have many FunctionMetrics (one per function in the code).

    Why we store this: Every time a user runs code analysis, we create an
    AnalysisResult record. This lets them build up a history of analyses and
    see trends over time.

    Example usage:
        # User analyzes some code
        result = AnalysisResult.objects.create(
            source_code="def hello(): return 'world'",
            cyclomatic_complexity=1,
            code_lines=1,
            num_functions=1,
            ...
        )

        # Later, retrieve their analysis history
        recent = AnalysisResult.objects.filter(analyzed_at__gte=last_week)
    """

    # OPTIONAL: Link to GitHub file (if code came from GitHub)
    #
    # Why nullable: User might paste code directly rather than fetch from GitHub
    # Why CASCADE: If GitHub file is deleted, delete associated analyses too
    #              (no point keeping analysis of code we can't reference)
    #
    # related_name='analyses': Lets us do codefile.analyses.all() to get all
    #                          analyses of that file
    code_file = models.ForeignKey(
        CodeFile,
        on_delete=models.CASCADE,
        null=True,  # OK to not have a GitHub file
        blank=True,  # OK to leave blank in forms
        related_name='analyses',
        help_text="GitHub code file that was analyzed"
    )

    # Store a COPY of the source code that was analyzed
    #
    # Why store this when we have code_file reference:
    # - GitHub code changes over time
    # - We want to preserve what we analyzed (point-in-time snapshot)
    # - User might have analyzed pasted code (no GitHub file)
    #
    # TextField not CharField because code can be thousands of lines
    source_code = models.TextField(
        help_text="Source code that was analyzed"
    )

    # --- COMPLEXITY METRICS ---
    # These are the key numbers from complexity_analyzer.py

    # McCabe cyclomatic complexity - number of independent paths through code
    # Higher = more complex = harder to test = more likely to have bugs
    # MinValueValidator(0) prevents negative values (doesn't make sense)
    cyclomatic_complexity = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="McCabe cyclomatic complexity"
    )

    # Count of actual code lines (excludes comments and blank lines)
    # Used for calculating code-to-complexity ratio
    code_lines = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Number of lines of code"
    )

    # How many function definitions in the code
    # Helps assess modularization (lots of small functions vs few giant ones)
    num_functions = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Number of functions"
    )

    # How many class definitions
    # Indicates OOP usage
    num_classes = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Number of classes"
    )

    # Deepest nesting level (if/for/while inside if/for/while etc.)
    # >4 is hard to understand (exceeds human working memory)
    max_nesting_depth = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Maximum nesting depth"
    )

    # Maintainability index: 0-100 score (higher = better)
    # Combines complexity, LOC, and other factors into single metric
    # FloatField because MI can be like 73.45
    # MaxValueValidator(100) because MI is capped at 100
    maintainability_index = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Maintainability index (0-100)"
    )

    # --- METADATA ---

    # When this analysis was performed
    # auto_now_add=True means Django sets this automatically on creation
    # Useful for sorting analyses by recency or filtering by date
    analyzed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this analysis was performed"
    )

    class Meta:
        """Django model configuration."""

        # Default ordering: newest first (- means descending)
        # When you do AnalysisResult.objects.all(), you get newest analyses first
        # Makes sense - users usually care about recent analyses more than old ones
        ordering = ['-analyzed_at']

        # How this model appears in Django admin
        verbose_name = 'Analysis Result'
        verbose_name_plural = 'Analysis Results'  # Not "Analysis Resultss"

    def __str__(self):
        """
        String representation for admin and templates.

        Shows either the GitHub filename or the date analyzed,
        depending on whether we have a code_file reference.

        Examples:
        - "Analysis of sorting.py" (if from GitHub)
        - "Analysis from 2024-12-01 14:30" (if pasted code)
        """
        if self.code_file:
            # Have a GitHub file reference - show its name
            return f"Analysis of {self.code_file.name}"

        # No GitHub file - show when it was analyzed
        # strftime formats datetime as human-readable string
        return f"Analysis from {self.analyzed_at.strftime('%Y-%m-%d %H:%M')}"

    def get_complexity_rating(self):
        """
        Translate numeric complexity into human-readable rating.

        Why we need this: Showing "complexity: 47" isn't very meaningful to
        most users. "High complexity" is clearer and more actionable.

        Rating thresholds based on McCabe's research:
        - 1-10: Low (recommended maximum)
        - 11-20: Medium (getting concerning)
        - 21-50: High (should refactor)
        - 51+: Very High (definitely refactor)

        These thresholds are based on research showing that complexity >10
        correlates with exponentially more bugs.

        Returns:
            str: 'Low', 'Medium', 'High', or 'Very High'

        Usage: In templates, can show color-coded badges based on rating
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
        Translate maintainability index into rating.

        MI is 0-100 scale where higher = better (opposite of complexity).

        Rating thresholds:
        - 80-100: Excellent (well-written code)
        - 60-79: Good (acceptable quality)
        - 40-59: Fair (needs improvement)
        - 0-39: Poor (needs urgent attention)

        These map roughly to letter grades: A, B, C, D/F

        Returns:
            str: 'Excellent', 'Good', 'Fair', or 'Poor'

        Design note: Could have stored the rating in the database instead of
        calculating it every time, but that would be denormalization. Computing
        it on the fly is cleaner (single source of truth) and the performance
        difference is negligible (simple if/elif).
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
    Stores complexity metrics for individual functions within analyzed code.

    WHY SEPARATE MODEL:
    Instead of storing function data as JSON in AnalysisResult, we use a
    separate model with a foreign key. This is proper database normalization.

    Benefits of separate model:
    1. Can query: "show me all functions with complexity > 10"
    2. Can sort: "show me the most complex functions across all analyses"
    3. Can aggregate: "average function complexity across all code"
    4. Cleaner schema: each field has proper type and validation

    If we stored as JSON, we'd lose all these capabilities.

    RELATIONSHIP:
    One AnalysisResult → Many FunctionMetrics (one per function in the code)

    Example:
        analysis = AnalysisResult.objects.get(pk=1)
        # Get all functions from this analysis
        functions = analysis.function_metrics.all()
        # Find complex functions
        complex = functions.filter(complexity__gt=10)
    """

    # Foreign key to parent AnalysisResult
    # CASCADE: If AnalysisResult is deleted, delete its FunctionMetrics too
    #          (function metrics don't make sense without parent analysis)
    # related_name: Lets us do analysis.function_metrics.all()
    analysis = models.ForeignKey(
        AnalysisResult,
        on_delete=models.CASCADE,
        related_name='function_metrics'
    )

    # Function name as it appears in the code
    # CharField(max_length=200) should be enough for any reasonable function name
    # Most Python function names are < 50 chars, but we're generous
    name = models.CharField(
        max_length=200,
        help_text="Function name"
    )

    # Line number where function is defined
    # Helps users locate the function in the source code
    # "Function 'process_data' on line 47 has high complexity"
    line_number = models.IntegerField(
        help_text="Line number where function is defined"
    )

    # How many lines of code in this function
    # Functions >50 lines typically do too much (Single Responsibility violation)
    num_lines = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Number of lines in function"
    )

    # Parameter count
    # Many parameters (>5) suggests function does too much or has poor design
    # Might indicate need for a parameter object or builder pattern
    num_params = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Number of parameters"
    )

    # Cyclomatic complexity of just this function
    # MinValueValidator(1) because every function has at least complexity 1
    # (the single path through the function)
    complexity = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Cyclomatic complexity of this function"
    )

    # Maximum nesting depth within this function
    # Deep nesting (>4) is hard to understand
    max_depth = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Maximum nesting depth"
    )

    class Meta:
        """Django model configuration."""

        # Default ordering: most complex first, then alphabetically by name
        # This puts problematic functions at the top of the list
        # Makes sense - users want to see what needs attention first
        ordering = ['-complexity', 'name']

        # No verbose_name specified - Django will use "Function Metric" by default
        # which is fine for this model

    def __str__(self):
        """
        String representation showing function name and complexity.

        Example: "process_data (complexity: 15)"

        Useful in Django admin dropdowns and debugging.
        """
        return f"{self.name} (complexity: {self.complexity})"