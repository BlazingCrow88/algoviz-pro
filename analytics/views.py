"""
Views for the analytics app.

Handles code analysis requests: users paste code or fetch from GitHub,
analyze complexity using AST parsing, view detailed metrics.

Includes both web views (HTML) and API endpoint (JSON) for programmatic access.
"""
from django.shortcuts import render, get_object_or_404, redirect
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
    Analytics landing page with recent analyses and analysis form.

    Shows 10 most recent analyses without pagination (YAGNI - can add later
    if needed).
    """
    recent_analyses = AnalysisResult.objects.all()[:10]

    context = {
        'recent_analyses': recent_analyses,
    }

    return render(request, 'analytics/home.html', context)


def analyze(request):
    """
    Handle code analysis submission.

    GET: Show analysis form
    POST: Process code, save results, redirect to results page
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

            # Save overall results
            analysis = AnalysisResult.objects.create(
                source_code=source_code,
                cyclomatic_complexity=metrics['cyclomatic_complexity'],
                code_lines=metrics['code_lines'],
                num_functions=metrics['num_functions'],
                num_classes=metrics['num_classes'],
                max_nesting_depth=metrics['max_nesting_depth'],
                maintainability_index=metrics['maintainability_index']
            )

            # Save per-function metrics for queryability
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

            return redirect('analytics:results', pk=analysis.id)

        except SyntaxError as e:
            return render(request, 'analytics/analyze.html', {
                'error': f'Syntax Error: {str(e)}',
                'source_code': source_code  # Pre-fill so they don't lose work
            })

        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return render(request, 'analytics/analyze.html', {
                'error': f'An error occurred: {str(e)}',
                'source_code': source_code
            })

    return render(request, 'analytics/analyze.html')


def results(request, pk):
    """
    Display detailed analysis results.

    Design decision: Re-analyze code to get fresh recommendations rather than
    storing them. Recommendations are dynamic (rules might change), and storing
    text would be denormalization. Re-analysis is fast (~10ms).
    """
    analysis = get_object_or_404(AnalysisResult, pk=pk)
    function_metrics = analysis.function_metrics.all()

    # Re-analyze for fresh recommendations
    try:
        analyzer = ComplexityAnalyzer()
        metrics = analyzer.analyze(analysis.source_code)
        recommendations = metrics.get('recommendations', [])
    except:
        # Degrade gracefully if re-analysis fails
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
@csrf_exempt  # TODO: Add CSRF protection for production
def analyze_api(request):
    """
    JSON API endpoint for programmatic code analysis.

    Why separate from analyze(): Different format (JSON vs HTML), different
    error handling, different auth needs. Cleaner separation.

    Design decision: Don't save API results to database. API is for one-off
    checks. Use web endpoint if persistence needed.

    Request: POST {"source_code": "..."}
    Response: {"success": true, "metrics": {...}, "report": "..."}
    """
    try:
        # Handle both JSON and form-encoded
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        source_code = data.get('source_code', '').strip()

        if not source_code:
            return JsonResponse({
                'error': 'Source code is required'
            }, status=400)

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
    Display algorithm performance benchmarks.

    Why in analytics app: Comparing algorithm performance is data analysis.
    Could go in algorithms app but analytics made more sense.

    Import inside function to avoid circular imports.
    """
    from algorithms.models import ExecutionLog

    logs = ExecutionLog.objects.all()[:100]

    context = {
        'logs': logs,
    }

    return render(request, 'analytics/benchmarks.html', context)