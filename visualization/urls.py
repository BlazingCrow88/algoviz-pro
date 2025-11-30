"""
URL patterns for visualization app.

This handles all the routing for the visualization features - the main interface
where users can actually see algorithms in action. Kept these URLs simple and
clean since they're some of the most frequently accessed pages in the app.
"""
from django.urls import path
from . import views

# app_name creates a namespace so we can use {% url 'visualization:home' %} in templates
# instead of just {% url 'home' %} which could conflict with other apps.
# Learned this the hard way when I had naming collisions between apps!
app_name = 'visualization'

urlpatterns = [
    # Root URL for the visualization app - shows the landing page with feature overview
    # Using '' instead of 'home/' because it's cleaner and more intuitive as the main entry point
    path('', views.home, name='home'),

    # Main visualization interface where users select algorithms and see them run step-by-step
    # This is the core feature of the whole project, so gave it a clear, obvious URL
    path('visualize/', views.visualize, name='visualize'),

    # Comparison view for running multiple algorithms side-by-side
    # Separate URL from visualize because it needs different layout and logic for showing
    # multiple algorithm visualizations at once
    path('compare/', views.compare, name='compare'),
]