"""
Views for the analytics app.

Handles code complexity analysis submissions and displays results.
I structured this with separate views for form display vs analysis processing
to keep the logic clean and make error handling easier.
"""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import logging

from .complexity_analyzer import ComplexityAnalyzer
from .models import AnalysisResult, FunctionMetric

# Set up logging so I could track errors in production without cluttering the UI
logger = logging.getLogger(__name__)


def home(request):
    """
    Analytics landing page showing recent analysis history.

    I show the 10 most recent analyses so users can quickly access their past
    results without having to re-analyze code. Limiting to 10 keeps the page
    fast and prevents database overload.
    """
    recent_analyses = AnalysisResult.objects.all()[:10]

    context = {
        'recent_analyses': recent_analyses,
    }

    return render(request, 'analytics/home.html', context)


def analyze(request):
    """
    Handles code analysis form submission and processing.

    GET: Display the empty form for users to paste code
    POST: Run the complexity analysis and save results to database

    I separated this from the home page so I could handle POST differently and
    provide better error messages if something goes wrong with the analysis.
    """
    if request.method == 'POST':
        source_code = request.POST.get('source_code', '').strip()

        # Validate that user actually submitted code
        if not source_code:
            return render(request, 'analytics/analyze.html', {
                'error': 'Please provide source code to analyze'
            })

        try:
            # Run the complexity analyzer on the submitted code
            analyzer = ComplexityAnalyzer()
            metrics = analyzer.analyze(source_code)

            # Save the main analysis results to database
            # This creates the parent record that function metrics will link to
            analysis = AnalysisResult.objects.create(
                source_code=source_code,
                cyclomatic_complexity=metrics['cyclomatic_complexity'],
                code_lines=metrics['code_lines'],
                num_functions=metrics['num_functions'],
                num_classes=metrics['num_classes'],
                max_nesting_depth=metrics['max_nesting_depth'],
                maintainability_index=metrics['maintainability_index']
            )

            # Save individual function metrics as separate records
            # This lets us query and display the most complex functions later
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

            # Redirect to results page instead of rendering directly
            # This prevents the "resubmit form" issue if user refreshes the page
            from django.shortcuts import redirect
            return redirect('analytics:results', pk=analysis.id)

        except SyntaxError as e:
            # User submitted invalid Python - show them the error and their code
            # Preserving their input saves them from having to retype everything
            return render(request, 'analytics/analyze.html', {
                'error': f'Syntax Error: {str(e)}',
                'source_code': source_code
            })
        except Exception as e:
            # Catch any other errors (database issues, unexpected analyzer bugs, etc.)
            # Log to server but show user-friendly message
            logger.error(f"Analysis error: {e}")
            return render(request, 'analytics/analyze.html', {
                'error': f'An error occurred: {str(e)}',
                'source_code': source_code
            })

    # GET request - just show the empty form
    return render(request, 'analytics/analyze.html')


def results(request, pk):
    """
    Display detailed results for a specific analysis.

    Shows the complexity metrics, function breakdown, and recommendations.
    I re-run the analyzer here just to get fresh recommendations, even though
    we already have the metrics saved. This seemed easier than storing
    recommendations as JSON in the database.
    """
    analysis = get_object_or_404(AnalysisResult, pk=pk)
    function_metrics = analysis.function_metrics.all()

    # Re-analyze just to generate recommendations
    # Not the most efficient, but it's fast enough and simpler than serializing
    # the recommendations list to the database
    try:
        analyzer = ComplexityAnalyzer()
        metrics = analyzer.analyze(analysis.source_code)
        recommendations = metrics.get('recommendations', [])
    except:
        # If re-analysis fails for some reason, just skip recommendations
        # The core metrics are already saved so the page still works
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
@csrf_exempt  # Allow external tools to hit this API without CSRF token
def analyze_api(request):
    """
    JSON API endpoint for programmatic code analysis.

    I added this so the analytics could be used by external tools or scripts,
    not just the web interface. The @csrf_exempt decorator is necessary because
    API clients won't have Django's CSRF token. In a real production app I'd
    use API keys instead, but this works for the project scope.

    POST parameters:
        - source_code: Python source code to analyze

    Returns:
        JSON response with analysis metrics and recommendations
    """
    try:
        # Handle both JSON and form-encoded requests
        # Some API clients send JSON, others use form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        source_code = data.get('source_code', '').strip()

        if not source_code:
            return JsonResponse({
                'error': 'Source code is required'
            }, status=400)

        # Run the analysis and return results as JSON
        # Don't save to database for API calls since we don't know the source
        analyzer = ComplexityAnalyzer()
        metrics = analyzer.analyze(source_code)

        return JsonResponse({
            'success': True,
            'metrics': metrics,
            'report': analyzer.generate_report()
        })

    except SyntaxError as e:
        # Return 400 for user errors (bad syntax)
        return JsonResponse({
            'error': f'Syntax error in code: {str(e)}'
        }, status=400)

    except Exception as e:
        # Return 500 for server errors (bugs in our code)
        logger.error(f"API analysis error: {e}")
        return JsonResponse({
            'error': f'An error occurred: {str(e)}'
        }, status=500)


def benchmarks(request):
    """
    Show performance benchmarks comparing algorithm execution times.

    This pulls from the algorithms app's ExecutionLog to show timing data.
    I kept this simple - just display the raw logs and let users compare.
    A fancier version would aggregate and chart the data.
    """
    from algorithms.models import ExecutionLog

    # Grab the 100 most recent execution logs
    # Limiting to 100 keeps the page performant and shows enough data to be useful
    logs = ExecutionLog.objects.all()[:100]

    context = {
        'logs': logs,
    }

    return render(request, 'analytics/benchmarks.html', context)