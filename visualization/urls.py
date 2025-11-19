"""
URL patterns for visualization app.

Week 12: Placeholder file - will be completed in Week 14
"""
from django.urls import path
from . import views

app_name = 'visualization'

urlpatterns = [
    # Placeholder - will add routes in Week 14
    path('', views.placeholder_home, name='home'),
]