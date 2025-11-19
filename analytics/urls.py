"""
URL patterns for analytics app.

Week 12: Placeholder file - will be completed in Week 15
"""
from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Placeholder - will add routes in Week 15
    path('', views.placeholder_analytics, name='home'),
]