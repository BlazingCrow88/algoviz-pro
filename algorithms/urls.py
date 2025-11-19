"""
URL patterns for algorithms app.

Maps URLs to views for algorithm listing, details, and execution.
"""
from django.urls import path
from . import views

app_name = 'algorithms'

urlpatterns = [
    # List all algorithms
    # Example: /algorithms/
    path('', views.algorithm_list, name='list'),

    # View algorithm details
    # Example: /algorithms/1/
    path('<int:pk>/', views.algorithm_detail, name='detail'),

    # Execute an algorithm with input
    # Example: /algorithms/execute/bubble/
    path('execute/<str:algo_name>/', views.execute_algorithm, name='execute'),
]
