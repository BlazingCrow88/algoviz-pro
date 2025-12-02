"""
URL routing configuration for the algorithms app.
"""
from django.urls import path
from . import views

app_name = 'algorithms'

urlpatterns = [
    # List all available algorithms
    path('', views.algorithm_list, name='list'),

    # View details for a specific algorithm
    path('<int:pk>/', views.algorithm_detail, name='detail'),

    # Execute algorithm by name (e.g., /algorithms/execute/bubble/)
    # Uses name instead of ID for cleaner API - view validates against whitelist
    path('execute/<str:algo_name>/', views.execute_algorithm, name='execute'),
]