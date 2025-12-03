"""
URL configuration for AlgoViz Pro.

Main project URL routing - includes app-specific URL configurations.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Root redirects to visualization home
    path('', RedirectView.as_view(url='/visualization/', permanent=False)),

    # App URL configurations
    path('algorithms/', include('algorithms.urls')),
    path('visualization/', include('visualization.urls')),
    path('github/', include('github_integration.urls')),
    path('analytics/', include('analytics.urls')),
]