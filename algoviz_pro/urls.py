"""
URL configuration for algoviz_pro project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/

Examples:
Function views
    1. Add an import: from my_app import views
    2. Add a URL to urlpatterns: path('', views.home, name='home')
Class-based views
    1. Add an import: from other_app.views import Home
    2. Add a URL to urlpatterns: path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns: path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    # Admin panel - needed this for managing test data and checking database entries
    path('admin/', admin.site.urls),

    # Redirect root to visualization since that's the main feature users want to see
    # Used permanent=False so I can change the landing page later if needed
    path('', RedirectView.as_view(url='/visualization/', permanent=False)),

    # All the sorting/searching algorithm logic lives in the algorithms app
    path('algorithms/', include('algorithms.urls')),

    # Main user interface where people interact with the visualizations
    path('visualization/', include('visualization.urls')),

    # GitHub integration for pulling and analyzing repositories
    path('github/', include('github_integration.urls')),

    # Complexity analysis tools - separate from algorithms since it's a different feature
    path('analytics/', include('analytics.urls')),
]