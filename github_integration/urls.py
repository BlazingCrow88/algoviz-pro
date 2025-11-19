"""
URL patterns for github_integration app.

Week 12: Placeholder file - will be completed in Week 13
"""
from django.urls import path
from . import views

app_name = 'github_integration'

urlpatterns = [
    # Placeholder - will add routes in Week 13
    path('', views.placeholder_github, name='home'),
]