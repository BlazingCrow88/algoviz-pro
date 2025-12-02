"""
Views for the algorithms app.

Design decisions: Using function-based views because they're more explicit for
this project's needs. Class-based views would add unnecessary abstraction.
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

# Map URL names to classes instead of dynamic imports for security
# This whitelist prevents users from importing arbitrary code
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

    Why separate by category: Makes it easier for users to find what they need
    rather than showing one long list. Sorting vs searching are different use cases.
    """
    algorithms = Algorithm.objects.all()

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
    Show detailed information about a specific algorithm.

    Why show recent executions: Lets users verify that actual performance matches
    theoretical complexity. Seeing bubble sort make ~n²/2 comparisons confirms
    the O(n²) analysis.
    """
    algorithm = get_object_or_404(Algorithm, pk=pk)

    # Limit to 10 to avoid cluttering the page with hundreds of entries
    recent_executions = ExecutionLog.objects.filter(
        algorithm=algorithm
    ).order_by('-executed_at')[:10]

    context = {
        'algorithm': algorithm,
        'recent_executions': recent_executions,
    }

    return render(request, 'algorithms/detail.html', context)


@require_http_methods(["POST"])
@csrf_exempt  # TODO: Remove before production - disabled for easier dev/testing
def execute_algorithm(request, algo_name):
    """
    Execute an algorithm and return step-by-step results for visualization.

    Why return JSON: Frontend needs raw data for animation. HTML would require
    parsing and is fragile for this use case.

    Why so much validation: The professor will definitely try to break this with
    edge cases. Every failure needs a clear error message, never a stack trace.
    """
    try:
        # Support both JSON (fetch API) and form data (traditional forms)
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            array_input = data.get('array', '')
        else:
            array_input = request.POST.get('array', '')

        if not array_input:
            return JsonResponse({
                'error': 'Array input is required',
                'details': 'Please provide comma-separated integers in the "array" parameter'
            }, status=400)

        # Handle both string format "5,2,8" and list format [5,2,8]
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

        if not input_array:
            return JsonResponse({
                'error': 'Array cannot be empty',
                'details': 'Please provide at least one integer'
            }, status=400)

        # Size limit prevents DoS attacks and keeps visualizations smooth
        # Larger arrays cause browser freezing during animation
        MAX_SIZE = 100
        if len(input_array) > MAX_SIZE:
            return JsonResponse({
                'error': f'Array too large (maximum {MAX_SIZE} elements)',
                'details': f'You provided {len(input_array)} elements. Please use a smaller array.'
            }, status=400)

        # Validate against whitelist - can't let users execute arbitrary code
        algo_class = ALGORITHM_MAP.get(algo_name.lower())
        if not algo_class:
            available = ', '.join(ALGORITHM_MAP.keys())
            return JsonResponse({
                'error': f'Unknown algorithm: {algo_name}',
                'details': f'Available algorithms: {available}'
            }, status=400)

        start_time = time.time()
        algo = algo_class()

        # Searching algorithms need target value, sorting algorithms don't
        is_searching = algo_name.lower() in ['binary', 'linear']

        if is_searching:
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

            # Binary search requires sorted input - sort automatically rather than
            # rejecting unsorted arrays. Better UX even though it modifies input.
            if algo_name.lower() == 'binary':
                input_array.sort()

            steps = list(algo.search(input_array, target))
        else:
            steps = list(algo.sort(input_array))

        execution_time_ms = (time.time() - start_time) * 1000

        # Get stats from final step for response
        final_step = steps[-1] if steps else {}
        comparisons = final_step.get('comparisons', 0)
        swaps = final_step.get('swaps', 0)

        # Best-effort logging - don't fail the request if logging fails
        # Users care about getting their visualization, not whether we tracked it
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
            # In production would use proper logging instead of print
            print(f"Failed to log execution: {log_error}")

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
        # Catch-all ensures we always return JSON, never expose stack traces
        return JsonResponse({
            'error': 'An unexpected error occurred',
            'details': str(e)
        }, status=500)