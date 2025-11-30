"""
URL patterns for analytics app.

These routes handle code complexity analysis - both the web interface and API.
I separated the analyze POST endpoint from the home page GET so the form submission
goes to a different URL, which makes it easier to handle errors and redirect.
"""
from django.urls import path
from . import views

# Namespace so I can use {% url 'analytics:analyze' %} in templates
app_name = 'analytics'

urlpatterns = [
    # Main analytics landing page with the code input form
    path('', views.home, name='home'),

    # Handles form submission and runs the complexity analysis
    # POST only - this is where the actual analysis happens
    path('analyze/', views.analyze, name='analyze'),

    # Show detailed results for a specific analysis
    # Using pk because we need to look up the AnalysisResult by ID
    path('results/<int:pk>/', views.results, name='results'),

    # JSON API endpoint for programmatic access (in case I want to add that feature)
    # Separated from the main analyze route so API clients don't get HTML responses
    path('api/analyze/', views.analyze_api, name='analyze_api'),

    # Performance benchmarks page - shows algorithm timing comparisons
    # Separate from analytics since it's a different feature
    path('benchmarks/', views.benchmarks, name='benchmarks'),
]