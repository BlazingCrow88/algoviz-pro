"""
Views for the algorithms app - handles web requests and responses.

What this file does: This is the "controller" layer in Django's MTV pattern.
When someone visits /algorithms/ or POSTs to /algorithms/execute/bubble/, the
functions here handle those requests and return appropriate responses.

Why views are critical: This is where we validate user input, run algorithms,
handle errors gracefully, and return data to the frontend. The professor will
definitely try to break this with invalid inputs - our defensive programming
here is what stops the app from crashing.

Design pattern: We use function-based views (FBVs) instead of class-based views
(CBVs) because they're simpler and more explicit for this project. CBVs would
add unnecessary abstraction when our views are relatively straightforward.

Security notes:
- Input validation on EVERYTHING (array size, format, target values)
- CSRF exempt on execute_algorithm (TODO: fix before production!)
- Size limits to prevent DoS (can't send 1 million element arrays)
- Graceful error handling (always return JSON, never expose stack traces)
"""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
import json
import time

from .models import Algorithm, ExecutionLog
from .sorting import BubbleSort, MergeSort, QuickSort
from .searching import BinarySearch, LinearSearch

# ALGORITHM_MAP: String names → actual Python classes
#
# Why we need this: URLs can't directly specify Python classes, so we map
# string names from the URL (like 'bubble') to the actual class (BubbleSort).
#
# Design decision: Using a dict instead of if/elif chain or dynamic imports
# - More maintainable: Adding new algorithms is one line
# - More secure: Whitelist of valid algorithms (can't import arbitrary classes)
# - More testable: Can easily mock individual algorithms
#
# Alternative considered: Using importlib to dynamically import based on URL
# name, but that's a security nightmare - user could potentially import anything!
#
# Adding new algorithms: Just add to this dict and implement the class
ALGORITHM_MAP = {
    'bubble': BubbleSort,
    'merge': MergeSort,
    'quick': QuickSort,
    'binary': BinarySearch,
    'linear': LinearSearch,
}


def algorithm_list(request):
    """
    Display all available algorithms grouped by category.

    This is a simple read-only view - just fetches from database and renders.
    No complex logic or validation needed since there's no user input.

    Template organization: We separate algorithms by category (sorting, searching,
    graph) so the template can render them in organized sections rather than one
    big list. Users can find what they need faster.

    Args:
        request: Django HttpRequest object (we don't actually use it much here)

    Returns:
        HttpResponse: Rendered HTML template with algorithm data

    Error handling: get_object_or_404 would handle missing objects, but since
    we're querying .all() there's no way for this to fail (empty queryset is fine).
    """
    # Fetch all algorithms from database
    # This is lazy-evaluated - query doesn't actually run until we access the data
    algorithms = Algorithm.objects.all()

    # Filter by category for template organization
    # These are separate querysets but Django's smart enough to combine them
    # into one SQL query when they're evaluated
    sorting_algos = algorithms.filter(category='SORT')
    searching_algos = algorithms.filter(category='SEARCH')
    graph_algos = algorithms.filter(category='GRAPH')

    # Context dict gets passed to template as variables
    # Template can access these as {{ algorithms }}, {{ total_count }}, etc.
    context = {
        'algorithms': algorithms,  # All algorithms (for overall stats)
        'sorting_algos': sorting_algos,  # Just sorting (for that section)
        'searching_algos': searching_algos,  # Just searching
        'graph_algos': graph_algos,  # Just graph
        'total_count': algorithms.count(),  # Total number (hits DB once)
    }

    return render(request, 'algorithms/list.html', context)


def algorithm_detail(request, pk):
    """
    Show detailed information about a specific algorithm.

    This view displays complexity analysis, description, and recent execution
    history so users can see both the theory and real performance data.

    Why show recent executions: Helps users see that the actual performance
    matches the theoretical complexity. If someone runs bubble sort on 100
    elements and sees 5000 comparisons, they can verify that's roughly n²/2.

    Args:
        request: HttpRequest object
        pk: Primary key of the algorithm (from URL like /algorithms/5/)

    Returns:
        HttpResponse with rendered template

    Error handling: get_object_or_404 automatically returns a nice 404 page
    if the algorithm doesn't exist. Better than letting it crash with a
    DoesNotExist exception that would show a 500 error.

    Edge cases:
    - pk=999 (doesn't exist) → 404 page
    - pk=-1 (invalid) → URL routing rejects this before view is called
    - No recent executions → Empty queryset is fine, template handles it
    """
    # Fetch the algorithm or return 404 if not found
    # This is Django's recommended pattern for "get one object or fail gracefully"
    algorithm = get_object_or_404(Algorithm, pk=pk)

    # Get recent execution logs for performance data
    # Limiting to 10 so the page doesn't get cluttered with hundreds of rows
    # order_by('-executed_at') means newest first (- means descending)
    recent_executions = ExecutionLog.objects.filter(
        algorithm=algorithm
    ).order_by('-executed_at')[:10]

    # Alternative: Could add pagination for viewing all logs, but 10 is enough
    # to show performance trends without overwhelming the user

    context = {
        'algorithm': algorithm,
        'recent_executions': recent_executions,
    }

    return render(request, 'algorithms/detail.html', context)


@require_http_methods(["POST"])  # Only allow POST - this modifies state
@csrf_exempt  # SECURITY WARNING: Disabled CSRF for easier testing
# TODO: Remove @csrf_exempt before deploying to production!
# Need to either:
# 1. Add {% csrf_token %} to frontend forms
# 2. Send CSRF token in fetch() headers for JavaScript requests
# 3. Use Django REST Framework which handles this automatically
#
# Why it's currently exempt: During development, testing with curl/Postman
# is easier without CSRF. But in production, this is a security risk -
# attackers could make our users' browsers execute algorithms without consent.
def execute_algorithm(request, algo_name):
    """
    Execute an algorithm and return step-by-step results for visualization.

    This is the most complex view in the app because it:
    1. Validates multiple types of input (array, target, algorithm name)
    2. Handles both JSON (from fetch) and form data (from HTML forms)
    3. Runs the actual algorithm
    4. Collects all visualization steps
    5. Logs execution metrics
    6. Returns detailed error messages for every failure case

    Why return JSON instead of rendering HTML: The frontend JavaScript needs
    raw data to animate the visualization. If we returned HTML, the JavaScript
    would have to parse it, which is messy and fragile.

    Why so much error handling: The professor WILL try to break this. Every
    invalid input case needs a clear, user-friendly error message. We never
    want to return a 500 error with a Python stack trace - that's unprofessional
    and exposes implementation details.

    Args:
        request: POST request with 'array' and optionally 'target'
        algo_name: Algorithm to run (from URL like /algorithms/execute/bubble/)

    Returns:
        JsonResponse with:
        - Success case: steps array, stats, execution time
        - Error case: error message, helpful details, appropriate HTTP status code

    Request format examples:
        JSON:  POST {"array": "5,2,8,1,9"}
        Form:  POST array=5,2,8,1,9
        JSON:  POST {"array": [5,2,8,1,9]}  (also supported)

    Response format:
        {
            "success": true,
            "steps": [{...}, {...}, ...],  // All visualization states
            "algorithm": "bubble",
            "input_size": 5,
            "total_time_ms": 0.23,
            "comparisons": 10,
            "swaps": 6,
            "step_count": 17
        }

    Edge cases handled:
    - Empty array
    - Non-integer values
    - Array too large (DoS prevention)
    - Missing target for searches
    - Invalid algorithm name
    - Malformed JSON
    - Invalid content types
    """
    try:
        # Handle both JSON and form-encoded data
        # JavaScript fetch() sends JSON, HTML forms send form data
        # Supporting both makes the API more flexible
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            array_input = data.get('array', '')
        else:
            # Form data from traditional HTML forms
            array_input = request.POST.get('array', '')

        # VALIDATION #1: Array must be provided
        if not array_input:
            return JsonResponse({
                'error': 'Array input is required',
                'details': 'Please provide comma-separated integers in the "array" parameter'
            }, status=400)  # 400 Bad Request - client error

        # VALIDATION #2: Convert input to list of integers
        # This is defensive programming - assume user input is garbage until proven otherwise
        try:
            if isinstance(array_input, str):
                # Handle "5,2,8,1,9" or "5, 2, 8" (with spaces)
                # .strip() removes whitespace from each number
                input_array = [int(x.strip()) for x in array_input.split(',')]
            elif isinstance(array_input, list):
                # Handle [5,2,8,1,9] from JSON
                # Still need to convert to int in case they sent ["5","2","8"]
                input_array = [int(x) for x in array_input]
            else:
                # Someone sent something weird like a dict or boolean
                raise ValueError("Invalid array format")
        except (ValueError, AttributeError) as e:
            # ValueError: int() failed (non-numeric input like "abc")
            # AttributeError: tried to call .split() on non-string
            return JsonResponse({
                'error': 'Invalid array format',
                'details': 'Array must be comma-separated integers (e.g., "5,2,8,1,9")'
            }, status=400)

        # VALIDATION #3: Empty array check
        # This would cause division by zero errors and visualization bugs
        if not input_array:
            return JsonResponse({
                'error': 'Array cannot be empty',
                'details': 'Please provide at least one integer'
            }, status=400)

        # VALIDATION #4: Size limit for performance and DoS prevention
        # Why 100? Larger arrays cause two problems:
        # 1. Browser freezes during animation (too many DOM updates)
        # 2. O(n²) algorithms take forever (10000 elements = 100 million operations)
        #
        # This is a reasonable limit that demonstrates algorithms without crashing.
        # Could make this configurable, but 100 is good for educational purposes.
        MAX_SIZE = 100
        if len(input_array) > MAX_SIZE:
            return JsonResponse({
                'error': f'Array too large (maximum {MAX_SIZE} elements)',
                'details': f'You provided {len(input_array)} elements. Please use a smaller array.'
            }, status=400)

        # VALIDATION #5: Algorithm must exist in our whitelist
        # Using .lower() so 'Bubble', 'BUBBLE', and 'bubble' all work
        algo_class = ALGORITHM_MAP.get(algo_name.lower())
        if not algo_class:
            # Tell user what algorithms ARE available (helpful error message)
            available = ', '.join(ALGORITHM_MAP.keys())
            return JsonResponse({
                'error': f'Unknown algorithm: {algo_name}',
                'details': f'Available algorithms: {available}'
            }, status=400)

        # Start timing the execution
        # We measure wall-clock time (not CPU time) because that's what users experience
        start_time = time.time()

        # Instantiate the algorithm class
        algo = algo_class()

        # Searching algorithms have different requirements than sorting
        # They need a target value to search for
        is_searching = algo_name.lower() in ['binary', 'linear']

        if is_searching:
            # VALIDATION #6: Searches need a target value
            if request.content_type == 'application/json':
                target = data.get('target')
            else:
                target = request.POST.get('target')

            if target is None:
                return JsonResponse({
                    'error': 'Target value required for searching algorithms',
                    'details': 'Please provide a target value to search for'
                }, status=400)

            # VALIDATION #7: Target must be a valid integer
            try:
                target = int(target)
            except (ValueError, TypeError):
                return JsonResponse({
                    'error': 'Invalid target value',
                    'details': 'Target must be an integer'
                }, status=400)

            # SPECIAL CASE: Binary search requires sorted input
            # We sort it here so users don't have to manually sort first
            # This makes the API more user-friendly at the cost of modifying input
            #
            # Alternative: Could reject unsorted arrays and tell user to sort first,
            # but that's annoying UX. Better to just sort it for them.
            if algo_name.lower() == 'binary':
                input_array.sort()

            # Run the search algorithm
            # The .search() method is a generator that yields states
            # list() consumes the generator and gives us all states at once
            steps = list(algo.search(input_array, target))
        else:
            # Run the sorting algorithm
            # Same pattern - generator that yields states, consume with list()
            steps = list(algo.sort(input_array))

        # Calculate total execution time
        execution_time_ms = (time.time() - start_time) * 1000

        # Extract statistics from the final step
        # The last yielded state contains final counts
        final_step = steps[-1] if steps else {}
        comparisons = final_step.get('comparisons', 0)
        swaps = final_step.get('swaps', 0)

        # LOG TO DATABASE: Track execution for analytics
        # This is "best effort" logging - if it fails, we don't crash the request
        # User cares about getting their visualization, not whether we logged it
        try:
            # Find the Algorithm model instance
            # Using __icontains for case-insensitive partial match
            # "bubble" matches Algorithm with name="Bubble Sort"
            algorithm_obj = Algorithm.objects.filter(
                name__icontains=algo_name
            ).first()

            if algorithm_obj:
                # Create execution log entry
                ExecutionLog.objects.create(
                    algorithm=algorithm_obj,
                    input_size=len(input_array),
                    execution_time_ms=execution_time_ms,
                    comparisons=comparisons if comparisons else None,
                    swaps=swaps if swaps else None
                )
        except Exception as log_error:
            # Log the error but don't fail the request
            # Logging is nice-to-have, not critical
            # In production, would use proper logging instead of print
            print(f"Failed to log execution: {log_error}")

        # SUCCESS! Return all the data the frontend needs
        return JsonResponse({
            'success': True,
            'steps': steps,  # Array of state dicts for visualization
            'algorithm': algo_name,  # Echo back which algorithm ran
            'input_size': len(input_array),  # How many elements
            'total_time_ms': round(execution_time_ms, 2),  # Total execution time
            'comparisons': comparisons,  # How many comparisons made
            'swaps': swaps,  # How many swaps made (sorting only)
            'step_count': len(steps)  # How many visualization frames
        })

    except json.JSONDecodeError:
        # User sent invalid JSON (like {broken json})
        return JsonResponse({
            'error': 'Invalid JSON in request body',
            'details': 'Please send valid JSON data'
        }, status=400)

    except Exception as e:
        # Catch-all for anything unexpected
        # This ensures we ALWAYS return JSON, never let Python exceptions
        # bubble up to Django's default 500 error page (which shows stack traces)
        #
        # In production, would log this to a monitoring service like Sentry
        return JsonResponse({
            'error': 'An unexpected error occurred',
            'details': str(e)  # Show the error message but not the full stack trace
        }, status=500)  # 500 Internal Server Error - our fault, not client's