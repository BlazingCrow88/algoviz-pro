"""
URL patterns for algorithms app.

Maps URLs to views for algorithm listing, details, and execution.
Follows RESTful design principles with clear, hierarchical URL structure.

URL Structure:
    - /algorithms/ - List view (index)
    - /algorithms/<id>/ - Detail view for specific algorithm
    - /algorithms/execute/<name>/ - Action endpoint for running algorithms

This design separates read operations (list, detail) from write/action
operations (execute) for clarity and follows Django best practices.
"""
from django.urls import path
from . import views

# Namespace allows reversing URLs as 'algorithms:list' etc.
# This prevents naming collisions when multiple apps have similar view names
app_name = 'algorithms'

urlpatterns = [
    # List all algorithms - serves as the main landing page
    # Empty path ('') makes this the default view for /algorithms/
    # Named 'list' for easy reversal in templates: {% url 'algorithms:list' %}
    # Example: /algorithms/
    path('', views.algorithm_list, name='list'),

    # View detailed information about a specific algorithm
    # Uses <int:pk> to capture algorithm ID from URL as an integer
    # 'pk' convention matches Django's primary key naming standard
    # Example: /algorithms/1/ shows details for algorithm with id=1
    path('<int:pk>/', views.algorithm_detail, name='detail'),

    # Execute an algorithm with user-provided input
    # Uses <str:algo_name> to accept algorithm name (e.g., 'bubble', 'merge')
    # Separate 'execute/' prefix distinguishes action URLs from detail URLs
    # This prevents conflicts between algorithm IDs and action names
    # Example: /algorithms/execute/bubble/ runs bubble sort
    path('execute/<str:algo_name>/', views.execute_algorithm, name='execute'),
]