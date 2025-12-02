"""
Views for the analytics app - handles code analysis requests and displays.

What this app does: Lets users paste Python code (or get it from GitHub),
analyze its complexity using AST parsing, and see detailed metrics about
code quality.

View organization:
- home(): Landing page with recent analyses
- analyze(): Form to submit code + POST handler to run analysis
- results(): Display detailed results for a specific analysis
- analyze_api(): JSON API endpoint (for JavaScript/external tools)
- benchmarks(): Performance comparison page

Design note: We have both web views (render HTML) and API views (return JSON)
to support both browser users and programmatic access. The API endpoint makes
it easy to integrate with external tools or build a CLI client.
"""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import logging

from .complexity_analyzer import ComplexityAnalyzer
from .models import AnalysisResult, FunctionMetric

# Set up logging for this module
# In production, these logs would go to a file or monitoring service like Sentry
# For development, they print to console
# Logging is better than print() because:
# 1. Can control log levels (DEBUG, INFO, WARNING, ERROR)
# 2. Can configure output destination (file, console, network)
# 3. Automatically includes timestamps and module names
logger = logging.getLogger(__name__)


def home(request):
    """
    Analytics landing page - shows recent analyses and analysis form.

    This is a simple read-only view. We fetch the 10 most recent analyses
    to give users a sense of activity and let them revisit past analyses.

    Design decision: Showing 10 recent analyses without pagination.
    - Pro: Simple, loads fast, covers most use cases
    - Con: Can't see analyses beyond the first 10

    Could add pagination if this becomes an issue, but YAGNI (You Aren't
    goinng to need it) - don't add features until they're actually needed.

    Args:
        request: HTTP request object (not used much here)

    Returns:
        Rendered HTML page with recent analyses
    """
    # Get 10 most recent analyses (ordering is set in model Meta)
    # [:10] is a LIMIT clause in SQL - efficient
    # Django's ORM is lazy - this query doesn't execute until the template
    # actually accesses recent_analyses
    recent_analyses = AnalysisResult.objects.all()[:10]

    context = {
        'recent_analyses': recent_analyses,
    }

    return render(request, 'analytics/home.html', context)


def analyze(request):
    """
    Handle code analysis submission.

    GET: Show the analysis form
    POST: Process submitted code and save results

    This view does BOTH:
    1. Display form (GET request)
    2. Process form submission (POST request)

    Alternative design: Could use Django's generic FormView or separate the
    GET and POST into different views, but this pattern is simpler and works
    fine for a straightforward form.

    Flow:
    User visits /analytics/analyze/ (GET)
    → See form with textarea
    User pastes code and submits (POST)
    → Code is analyzed
    → Results saved to database
    → Redirect to results page

    Args:
        request: HTTP request with optional POST data

    Returns:
        - GET: Rendered form page
        - POST: Redirect to results (success) or form with error (failure)
    """
    if request.method == 'POST':
        # User submitted the form - process it

        # Get source code from form
        # .strip() removes leading/trailing whitespace
        # Empty string default prevents KeyError if field is missing
        source_code = request.POST.get('source_code', '').strip()

        # VALIDATION: Code can't be empty
        # Analyzing empty code would give meaningless results
        if not source_code:
            # Re-render form with error message
            # User stays on same page and sees what went wrong
            return render(request, 'analytics/analyze.html', {
                'error': 'Please provide source code to analyze'
            })

        try:
            # STEP 1: Analyze the code
            analyzer = ComplexityAnalyzer()
            metrics = analyzer.analyze(source_code)
            # If code has syntax errors, this raises SyntaxError
            # which we catch below

            # STEP 2: Save analysis results to database
            # Why save to database:
            # 1. User can revisit results later (persistent storage)
            # 2. Can build history/trends over time
            # 3. Can compare different analyses
            # 4. Enables analytics (what code patterns are common?)
            analysis = AnalysisResult.objects.create(
                source_code=source_code,  # Store the actual code
                cyclomatic_complexity=metrics['cyclomatic_complexity'],
                code_lines=metrics['code_lines'],
                num_functions=metrics['num_functions'],
                num_classes=metrics['num_classes'],
                max_nesting_depth=metrics['max_nesting_depth'],
                maintainability_index=metrics['maintainability_index']
            )

            # STEP 3: Save per-function metrics
            # Each function in the analyzed code gets its own FunctionMetric record
            # This lets us query things like "show all functions with complexity > 10"
            # across all analyses
            for func_data in metrics['functions']:
                FunctionMetric.objects.create(
                    analysis=analysis,  # Link to parent analysis
                    name=func_data['name'],
                    line_number=func_data['line_number'],
                    num_lines=func_data['num_lines'],
                    num_params=func_data['num_params'],
                    complexity=func_data['complexity'],
                    max_depth=func_data['max_depth']
                )

            # Transaction note: Django wraps each request in a transaction by default
            # If anything fails after the analysis.objects.create(), the transaction
            # rolls back and we don't get orphaned AnalysisResult records.
            # This is good - we don't want AnalysisResults without FunctionMetrics

            # STEP 4: Redirect to results page
            # Using redirect (302) instead of render so that refreshing the page
            # doesn't resubmit the form (Post/Redirect/Get pattern)
            from django.shortcuts import redirect
            return redirect('analytics:results', pk=analysis.id)

        except SyntaxError as e:
            # User's code has syntax errors (missing colons, unmatched parens, etc.)
            # This is a USER error, not a bug in our code
            # Show friendly error message and let them fix it
            return render(request, 'analytics/analyze.html', {
                'error': f'Syntax Error: {str(e)}',
                'source_code': source_code  # Pre-fill form so they don't lose work
            })

        except Exception as e:
            # Something unexpected went wrong (database error, etc.)
            # This is probably OUR error or infrastructure issue
            # Log it for debugging but show user-friendly message
            logger.error(f"Analysis error: {e}")
            return render(request, 'analytics/analyze.html', {
                'error': f'An error occurred: {str(e)}',
                'source_code': source_code  # Pre-fill form
            })

    # GET request - just show the form
    # No data needed, template has empty form
    return render(request, 'analytics/analyze.html')


def results(request, pk):
    """
    Display detailed analysis results for a specific analysis.

    Shows:
    - Overall metrics (complexity, LOC, maintainability)
    - Per-function breakdown
    - Recommendations for improvement

    Design quirk: We RE-ANALYZE the code here to get fresh recommendations.
    Why not just use saved data?
    - We store metrics in database for querying/history
    - But recommendations are dynamic (rules might change)
    - Recommendations include text like "consider refactoring X"
    - Storing that text in DB would be denormalization

    Trade-off: Re-analyzing takes ~10ms for typical code, acceptable for
    showing results page. If performance becomes an issue, could cache
    recommendations or store them as JSON.

    Args:
        request: HTTP request
        pk: Primary key of AnalysisResult to display

    Returns:
        Rendered results page with analysis data
    """
    # Fetch the analysis or 404 if it doesn't exist
    # get_object_or_404 is better than .get() because it automatically
    # returns a nice 404 page instead of raising DoesNotExist exception
    analysis = get_object_or_404(AnalysisResult, pk=pk)

    # Get all function metrics for this analysis
    # Uses the related_name from ForeignKey: analysis.function_metrics
    # This is more efficient than filtering: FunctionMetric.objects.filter(analysis=analysis)
    function_metrics = analysis.function_metrics.all()

    # Re-analyze to get fresh recommendations
    # This is quick (just AST walking, no database I/O)
    try:
        analyzer = ComplexityAnalyzer()
        metrics = analyzer.analyze(analysis.source_code)
        recommendations = metrics.get('recommendations', [])
    except:
        # If re-analysis fails for some reason, just skip recommendations
        # Better to show results without recommendations than crash the page
        # This is defensive programming - degrade gracefully
        recommendations = []

    context = {
        'analysis': analysis,  # Main analysis object
        'function_metrics': function_metrics,  # List of function details
        'recommendations': recommendations,  # Fresh recommendations
        'complexity_rating': analysis.get_complexity_rating(),  # "Low"/"High"/etc
        'maintainability_rating': analysis.get_maintainability_rating(),  # "Good"/"Poor"/etc
    }

    return render(request, 'analytics/results.html', context)


@require_http_methods(["POST"])  # Only allow POST, reject GET/PUT/DELETE
@csrf_exempt  # SECURITY WARNING: Disabled for easier API testing
# TODO: Fix CSRF for production!
# Options:
# 1. Require CSRF token in POST data or headers
# 2. Use API key authentication instead of CSRF
# 3. Use Django REST Framework which handles this properly
#
# Why currently exempt: During development, testing with curl/Postman is
# easier without CSRF. But in production, this is a security risk.
def analyze_api(request):
    """
    JSON API endpoint for code analysis.

    This is for programmatic access - JavaScript frontends, CLI tools, etc.
    Returns JSON instead of HTML so clients can parse results easily.

    Why separate from analyze() view:
    - Different return format (JSON vs HTML)
    - Different error handling (status codes vs rendered error pages)
    - Different authentication needs (might use API keys)

    Could have combined them with a format parameter, but separation is cleaner.

    Request format:
        POST /analytics/api/analyze/
        Content-Type: application/json
        Body: {"source_code": "def hello(): return 'world'"}

    Response format (success):
        {
            "success": true,
            "metrics": {
                "cyclomatic_complexity": 1,
                "code_lines": 1,
                "functions": [...],
                ...
            },
            "report": "=== CODE COMPLEXITY REPORT ===\n..."
        }

    Response format (error):
        {
            "error": "Syntax error in code: ..."
        }

    Args:
        request: POST request with source_code parameter

    Returns:
        JsonResponse with analysis results or error
    """
    try:
        # Handle both JSON and form-encoded requests
        # JavaScript typically sends JSON, curl might send form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        # Extract source code
        source_code = data.get('source_code', '').strip()

        # VALIDATION: Source code required
        if not source_code:
            return JsonResponse({
                'error': 'Source code is required'
            }, status=400)  # 400 Bad Request - client error

        # Analyze the code
        analyzer = ComplexityAnalyzer()
        metrics = analyzer.analyze(source_code)
        # Note: We don't save to database for API calls
        # Why: API might be used for one-off checks that don't need persistence
        # If caller wants to save, they can hit the web endpoint instead

        # Return all metrics and optional text report
        return JsonResponse({
            'success': True,
            'metrics': metrics,  # All metrics as dict
            'report': analyzer.generate_report()  # Text report (optional)
        })

    except SyntaxError as e:
        # User's code has syntax errors
        # Return 400 (client error) because it's their code that's wrong
        return JsonResponse({
            'error': f'Syntax error in code: {str(e)}'
        }, status=400)

    except Exception as e:
        # Something went wrong on our end
        # Log for debugging and return 500 (server error)
        logger.error(f"API analysis error: {e}")
        return JsonResponse({
            'error': f'An error occurred: {str(e)}'
        }, status=500)


def benchmarks(request):
    """
    Display algorithm performance benchmarks.

    Shows execution logs from the algorithms app to help users compare
    algorithm performance (bubble sort vs merge sort, etc.).

    This view ties together the analytics and algorithms apps - showing that
    our project has multiple interconnected components.

    Why this is here instead of algorithms app:
    - "Analytics" is about data analysis and visualization
    - Comparing algorithm performance is analysis
    - Could go either way, but analytics app made more sense

    Implementation note: Importing ExecutionLog inside the function instead
    of at module level. Why?
    - Avoids circular import issues (if algorithms.models imported analytics.models)
    - Only loads the model when this specific view is called
    - Slightly cleaner separation of concerns

    Args:
        request: HTTP request

    Returns:
        Rendered benchmarks page with execution logs
    """
    # Import here to avoid circular imports
    from algorithms.models import ExecutionLog

    # Get recent execution logs for display
    # [:100] limits to 100 most recent (prevent loading thousands of records)
    # Ordering is set in ExecutionLog.Meta (newest first)
    logs = ExecutionLog.objects.all()[:100]

    # Could add filtering/grouping here:
    # - Group by algorithm (show all bubble sort runs together)
    # - Filter by input size (compare same-size inputs)
    # - Calculate averages (average execution time per algorithm)
    # For now, just showing raw logs is sufficient

    context = {
        'logs': logs,
    }

    return render(request, 'analytics/benchmarks.html', context)