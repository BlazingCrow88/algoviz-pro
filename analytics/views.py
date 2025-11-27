"""
Views for the analytics app.

Handles code analysis and results display.
"""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import logging

from .complexity_analyzer import ComplexityAnalyzer
from .models import AnalysisResult, FunctionMetric

logger = logging.getLogger(__name__)


def home(request):
    """
    Analytics home page.

    Shows recent analyses and provides interface for new analysis.
    """
    recent_analyses = AnalysisResult.objects.all()[:10]

    context = {
        'recent_analyses': recent_analyses,
    }

    return render(request, 'analytics/home.html', context)


def analyze(request):
    """
    Code analysis input page.

    GET: Show form for code input
    POST: Analyze code and redirect to results
    """
    if request.method == 'POST':
        source_code = request.POST.get('source_code', '').strip()

        if not source_code:
            return render(request, 'analytics/analyze.html', {
                'error': 'Please provide source code to analyze'
            })

        try:
            # Analyze code
            analyzer = ComplexityAnalyzer()
            metrics = analyzer.analyze(source_code)

            # Save results
            analysis = AnalysisResult.objects.create(
                source_code=source_code,
                cyclomatic_complexity=metrics['cyclomatic_complexity'],
                code_lines=metrics['code_lines'],
                num_functions=metrics['num_functions'],
                num_classes=metrics['num_classes'],
                max_nesting_depth=metrics['max_nesting_depth'],
                maintainability_index=metrics['maintainability_index']
            )

            # Save function metrics
            for func_data in metrics['functions']:
                FunctionMetric.objects.create(
                    analysis=analysis,
                    name=func_data['name'],
                    line_number=func_data['line_number'],
                    num_lines=func_data['num_lines'],
                    num_params=func_data['num_params'],
                    complexity=func_data['complexity'],
                    max_depth=func_data['max_depth']
                )

            # Redirect to results
            from django.shortcuts import redirect
            return redirect('analytics:results', pk=analysis.id)

        except SyntaxError as e:
            return render(request, 'analytics/analyze.html', {
                'error': f'Syntax Error: {str(e)}',
                'source_code': source_code
            })
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return render(request, 'analytics/analyze.html', {
                'error': f'An error occurred: {str(e)}',
                'source_code': source_code
            })

    # GET request - show form
    return render(request, 'analytics/analyze.html')


def results(request, pk):
    """
    Display analysis results.

    Args:
        pk: Primary key of AnalysisResult
    """
    analysis = get_object_or_404(AnalysisResult, pk=pk)
    function_metrics = analysis.function_metrics.all()

    # Re-analyze to get recommendations
    try:
        analyzer = ComplexityAnalyzer()
        metrics = analyzer.analyze(analysis.source_code)
        recommendations = metrics.get('recommendations', [])
    except:
        recommendations = []

    context = {
        'analysis': analysis,
        'function_metrics': function_metrics,
        'recommendations': recommendations,
        'complexity_rating': analysis.get_complexity_rating(),
        'maintainability_rating': analysis.get_maintainability_rating(),
    }

    return render(request, 'analytics/results.html', context)


@require_http_methods(["POST"])
@csrf_exempt
def analyze_api(request):
    """
    API endpoint for code analysis.

    POST parameters:
        - source_code: Python source code to analyze

    Returns:
        JSON response with analysis results
    """
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        source_code = data.get('source_code', '').strip()

        if not source_code:
            return JsonResponse({
                'error': 'Source code is required'
            }, status=400)

        # Analyze code
        analyzer = ComplexityAnalyzer()
        metrics = analyzer.analyze(source_code)

        return JsonResponse({
            'success': True,
            'metrics': metrics,
            'report': analyzer.generate_report()
        })

    except SyntaxError as e:
        return JsonResponse({
            'error': f'Syntax error in code: {str(e)}'
        }, status=400)

    except Exception as e:
        logger.error(f"API analysis error: {e}")
        return JsonResponse({
            'error': f'An error occurred: {str(e)}'
        }, status=500)


def benchmarks(request):
    """
    Display performance benchmarks and comparisons.
    """
    from algorithms.models import ExecutionLog

    # Get execution logs for benchmarking
    logs = ExecutionLog.objects.all()[:100]

    context = {
        'logs': logs,
    }

    return render(request, 'analytics/benchmarks.html', context)