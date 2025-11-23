"""
URL patterns for analytics app.
"""
from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.home, name='home'),
    path('analyze/', views.analyze, name='analyze'),
    path('results/<int:pk>/', views.results, name='results'),
    path('api/analyze/', views.analyze_api, name='analyze_api'),
    path('benchmarks/', views.benchmarks, name='benchmarks'),
]