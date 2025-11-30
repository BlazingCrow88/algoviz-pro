"""
Views for the algorithms app.

This module handles HTTP requests related to algorithm listing and execution.
It provides endpoints for displaying available algorithms and executing them
with user-provided input.
"""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import time

from .models import Algorithm, ExecutionLog
from .sorting import BubbleSort, MergeSort, QuickSort
from .searching import BinarySearch, LinearSearch

# Map algorithm names to their implementation classes
ALGORITHM_MAP = {
    'bubble': BubbleSort,
    'merge': MergeSort,
    'quick': QuickSort,
    'binary': BinarySearch,
    'linear': LinearSearch,
}

# Maximum array size for visualization
MAX_ARRAY_SIZE = 100


def algorithm_list(request):
    """
    Display list of available algorithms.

    This view retrieves all algorithms from the database and displays them
    in a list with their complexity information.

    Args:
        request: HTTP request object

    Returns:
        HttpResponse: Rendered template with algorithm list
    """
    algorithms = Algorithm.objects.all()

    # Group algorithms by category for better organization
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
    Display detailed information about a specific algorithm.

    Args:
        request: HTTP request object
        pk: Primary key of the algorithm

    Returns:
        HttpResponse: Rendered template with algorithm details
    """
    algorithm = get_object_or_404(Algorithm, pk=pk)

    # Get recent execution logs for this algorithm
    recent_executions = ExecutionLog.objects.filter(
        algorithm=algorithm
    ).order_by('-executed_at')[:10]

    context = {
        'algorithm': algorithm,
        'recent_executions': recent_executions,
    }

    return render(request, 'algorithms/detail.html', context)


@require_http_methods(["POST"])
@csrf_exempt  # Remove this in production and handle CSRF properly
def execute_algorithm(request, algo_name):
    """
    Execute algorithm with given input and return steps as JSON.

    This view handles POST requests containing an array to sort or search. It executes
    the requested algorithm and returns all intermediate steps for visualization.

    Args:
        request: HTTP POST request with 'array' parameter (and 'target' for searching)
        algo_name: Name of algorithm to execute ('bubble', 'merge', 'quick', 'binary', 'linear')

    Returns:
        JsonResponse: JSON containing:
            - success: Boolean indicating if execution succeeded
            - steps: List of state dictionaries from algorithm execution
            - algorithm: Name of algorithm executed
            - input_size: Size of input array
            - total_time_ms: Total execution time
            - comparisons: Total comparison operations
            - swaps: Total swap operations (if applicable)

        Error responses (JSON with 'error' key):
            - 400: Invalid input (bad array format, wrong algorithm name, etc.)
            - 405: Wrong HTTP method (not POST)
            - 500: Internal server error during execution

    Example request:
        POST /algorithms/execute/bubble/
        Body: array=5,2,8,1,9

    Example response:
        {
            "success": true,
            "steps": [
                {"array": [5,2,8,1,9], "comparing": [0,1], ...},
                {"array": [2,5,8,1,9], "swapped": [0,1], ...},
                ...
            ],
            "algorithm": "bubble",
            "input_size": 5,
            "total_time_ms": 12.5,
            "comparisons": 10,
            "swaps": 4
        }
    """
    try:
        # Parse input array from request
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            array_input = data.get('array', '')
            target_input = data.get('target', '')
        else:
            array_input = request.POST.get('array', '')
            target_input = request.POST.get('target', '')

        # Validate and parse array
        if not array_input:
            return JsonResponse({
                'error': 'Array input is required',
                'details': 'Please provide comma-separated integers in the "array" parameter'
            }, status=400)

        # Convert string to integer array
        try:
            if isinstance(array_input, str):
                input_array = [int(x.strip()) for x in array_input.split(',')]
            elif isinstance(array_input, list):
                input_array = [int(x) for x in array_input]
            else:
                raise ValueError("Invalid array format")
        except (ValueError, AttributeError):
            return JsonResponse({
                'error': 'Invalid array format',
                'details': 'Array must be comma-separated integers (e.g., "5,2,8,1,9")'
            }, status=400)

        # Validate array is not empty
        if not input_array:
            return JsonResponse({
                'error': 'Array cannot be empty',
                'details': 'Please provide at least one integer'
            }, status=400)

        # Validate array size (prevent performance issues)
        if len(input_array) > MAX_ARRAY_SIZE:
            return JsonResponse({
                'error': f'Array too large (maximum {MAX_ARRAY_SIZE} elements)',
                'details': f'You provided {len(input_array)} elements. Please use a smaller array.'
            }, status=400)

        # Get algorithm class
        algo_class = ALGORITHM_MAP.get(algo_name.lower())
        if not algo_class:
            available = ', '.join(ALGORITHM_MAP.keys())
            return JsonResponse({
                'error': f'Unknown algorithm: {algo_name}',
                'details': f'Available algorithms: {available}'
            }, status=400)

        # Check if this is a searching algorithm
        is_searching = algo_name.lower() in ['binary', 'linear']

        if is_searching:
            # Validate target input for searching algorithms
            if not target_input and target_input != 0:
                return JsonResponse({
                    'error': 'Target value is required for searching algorithms',
                    'details': 'Please provide a target value to search for'
                }, status=400)

            try:
                target = int(target_input)
            except (ValueError, TypeError):
                return JsonResponse({
                    'error': 'Invalid target value',
                    'details': 'Target must be an integer'
                }, status=400)

        # Execute algorithm and collect all steps
        start_time = time.time()
        algo = algo_class()

        if is_searching:
            steps = list(algo.search(input_array, target))
        else:
            steps = list(algo.sort(input_array))

        execution_time_ms = (time.time() - start_time) * 1000

        # Get final statistics from last step
        final_step = steps[-1] if steps else {}
        comparisons = final_step.get('comparisons', 0)
        swaps = final_step.get('swaps', 0)

        # Log execution to database (for analytics)
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
            # Don't fail the request if logging fails
            print(f"Failed to log execution: {log_error}")

        # Return successful response
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
        # Catch any unexpected errors
        return JsonResponse({
            'error': 'An unexpected error occurred',
            'details': str(e)
        }, status=500)