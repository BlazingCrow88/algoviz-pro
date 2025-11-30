"""
Views for the algorithms app.

Handles displaying algorithm info and executing them with user input.
The execute_algorithm view returns step-by-step states so the frontend
can animate what's happening in real-time.
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

# Maps URL names like 'bubble' to the actual class
# Makes it easy to add new algorithms without changing views
ALGORITHM_MAP = {
    'bubble': BubbleSort,
    'merge': MergeSort,
    'quick': QuickSort,
    'binary': BinarySearch,
    'linear': LinearSearch,
}


def algorithm_list(request):
    """
    Show all available algorithms.

    Pulls algorithms from database and groups them by category
    so the template can display them in organized sections.

    Args:
        request: HTTP request object

    Returns:
        HttpResponse: Rendered template with algorithm list
    """
    algorithms = Algorithm.objects.all()

    # Split into categories so template can show separate sections
    sorting_algos = algorithms.filter(category='SORT')
    searching_algos = algorithms.filter(category='SEARCH')
    graph_algos = algorithms.filter(category='GRAPH')

    context = {
        'algorithms': algorithms,
        'sorting_algos': sorting_algos,
        'searching_algos': searching_algos,
        'graph_algos': graph_algos,
        'total_count': algorithms.count(),
    }

    return render(request, 'algorithms/list.html', context)


def algorithm_detail(request, pk):
    """
    Show details about a specific algorithm.

    Displays complexity info and recent execution logs so users
    can see how the algorithm performs.

    Args:
        request: HTTP request object
        pk: Primary key of the algorithm

    Returns:
        HttpResponse: Rendered template with algorithm details
    """
    algorithm = get_object_or_404(Algorithm, pk=pk)

    # Show last 10 runs to give performance examples without cluttering the page
    recent_executions = ExecutionLog.objects.filter(
        algorithm=algorithm
    ).order_by('-executed_at')[:10]

    context = {
        'algorithm': algorithm,
        'recent_executions': recent_executions,
    }

    return render(request, 'algorithms/detail.html', context)


@require_http_methods(["POST"])
@csrf_exempt  # TODO: Fix this before deploying - needs proper CSRF handling
def execute_algorithm(request, algo_name):
    """
    Run an algorithm and return all steps for visualization.

    Takes an array (and target for searches), executes the algorithm,
    and returns every intermediate step so JavaScript can animate it.

    Args:
        request: POST request with 'array' and optional 'target'
        algo_name: Which algorithm to run (bubble, merge, quick, etc.)

    Returns:
        JsonResponse with steps array or error message

    Example:
        POST /algorithms/execute/bubble/
        Body: array=5,2,8,1,9

        Returns: {"success": true, "steps": [...], "comparisons": 10, ...}
    """
    try:
        # Handle both JSON (from fetch) and form data (from HTML forms)
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            array_input = data.get('array', '')
        else:
            array_input = request.POST.get('array', '')

        # Gotta have an array to sort/search
        if not array_input:
            return JsonResponse({
                'error': 'Array input is required',
                'details': 'Please provide comma-separated integers in the "array" parameter'
            }, status=400)

        # Convert to actual integers
        # Handle both "5,2,8" strings and [5,2,8] lists
        # .strip() catches cases like "5, 2, 8" with spaces
        try:
            if isinstance(array_input, str):
                input_array = [int(x.strip()) for x in array_input.split(',')]
            elif isinstance(array_input, list):
                input_array = [int(x) for x in array_input]
            else:
                raise ValueError("Invalid array format")
        except (ValueError, AttributeError) as e:
            return JsonResponse({
                'error': 'Invalid array format',
                'details': 'Array must be comma-separated integers (e.g., "5,2,8,1,9")'
            }, status=400)

        # Empty array would break everything downstream
        if not input_array:
            return JsonResponse({
                'error': 'Array cannot be empty',
                'details': 'Please provide at least one integer'
            }, status=400)

        # Cap at 100 elements - bigger arrays freeze the browser during animation
        MAX_SIZE = 100
        if len(input_array) > MAX_SIZE:
            return JsonResponse({
                'error': f'Array too large (maximum {MAX_SIZE} elements)',
                'details': f'You provided {len(input_array)} elements. Please use a smaller array.'
            }, status=400)

        # Look up which class to use
        algo_class = ALGORITHM_MAP.get(algo_name.lower())
        if not algo_class:
            available = ', '.join(ALGORITHM_MAP.keys())
            return JsonResponse({
                'error': f'Unknown algorithm: {algo_name}',
                'details': f'Available algorithms: {available}'
            }, status=400)

        # Time the execution for performance metrics
        start_time = time.time()
        algo = algo_class()

        # Search algorithms work differently than sorting
        is_searching = algo_name.lower() in ['binary', 'linear']

        if is_searching:
            # Searches need a target value
            if request.content_type == 'application/json':
                target = data.get('target')
            else:
                target = request.POST.get('target')

            if target is None:
                return JsonResponse({
                    'error': 'Target value required for searching algorithms',
                    'details': 'Please provide a target value to search for'
                }, status=400)

            try:
                target = int(target)
            except (ValueError, TypeError):
                return JsonResponse({
                    'error': 'Invalid target value',
                    'details': 'Target must be an integer'
                }, status=400)

            # Binary search only works on sorted arrays
            if algo_name.lower() == 'binary':
                input_array.sort()

            # Run the search and collect all steps
            steps = list(algo.search(input_array, target))
        else:
            # Run the sort and collect all steps
            steps = list(algo.sort(input_array))

        execution_time_ms = (time.time() - start_time) * 1000

        # Grab stats from the last step
        final_step = steps[-1] if steps else {}
        comparisons = final_step.get('comparisons', 0)
        swaps = final_step.get('swaps', 0)

        # Log to database for analytics
        # If this fails, don't crash the whole request - logging isn't critical
        try:
            algorithm_obj = Algorithm.objects.filter(
                name__icontains=algo_name
            ).first()

            if algorithm_obj:
                ExecutionLog.objects.create(
                    algorithm=algorithm_obj,
                    input_size=len(input_array),
                    execution_time_ms=execution_time_ms,
                    comparisons=comparisons if comparisons else None,
                    swaps=swaps if swaps else None
                )
        except Exception as log_error:
            # Just print it - user doesn't care if logging failed
            print(f"Failed to log execution: {log_error}")

        # Send back all the steps for visualization
        return JsonResponse({
            'success': True,
            'steps': steps,
            'algorithm': algo_name,
            'input_size': len(input_array),
            'total_time_ms': round(execution_time_ms, 2),
            'comparisons': comparisons,
            'swaps': swaps,
            'step_count': len(steps)
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON in request body',
            'details': 'Please send valid JSON data'
        }, status=400)

    except Exception as e:
        # Catch anything weird so we always return JSON
        return JsonResponse({
            'error': 'An unexpected error occurred',
            'details': str(e)
        }, status=500)