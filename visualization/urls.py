"""
URL patterns for visualization app.
"""
from django.urls import path
from . import views

app_name = 'visualization'

urlpatterns = [
    path('', views.home, name='home'),
    path('visualize/', views.visualize, name='visualize'),
    path('compare/', views.compare, name='compare'),
]