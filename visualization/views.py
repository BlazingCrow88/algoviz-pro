"""
Views for the visualization app.

Week 12: Placeholder views - will be completed in Week 14
"""
from django.shortcuts import render
from django.http import HttpResponse


def placeholder_home(request):
    """
    Placeholder home view for Week 12.

    This will be replaced with actual visualization interface in Week 14.
    """
    return HttpResponse(
        "<h1>AlgoViz Pro - Visualization Coming Soon!</h1>"
        "<p>Visualization interface will be added in Week 14.</p>"
        "<p>For now, you can use the <a href='/algorithms/'>Algorithms API</a>.</p>"
    )
