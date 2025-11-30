"""
Views for the visualization app.

Handles rendering of visualization pages.
"""
from django.shortcuts import render
from algorithms.models import Algorithm


def home(request):
    """
    Landing page for AlgoViz Pro.

    Displays project overview, features, and complexity reference table.
    """
    # Get algorithm counts for display
    sorting_count = Algorithm.objects.filter(category='SORT').count()
    searching_count = Algorithm.objects.filter(category='SEARCH').count()
    graph_count = Algorithm.objects.filter(category='GRAPH').count()

    context = {
        'sorting_count': sorting_count,
        'searching_count': searching_count,
        'graph_count': graph_count,
        'total_algorithms': sorting_count + searching_count + graph_count,
    }

    return render(request, 'visualization/home.html', context)


def visualize(request):
    """
    Main visualization page with interactive controls.

    Provides interface for executing and visualizing algorithms
    with step-by-step animation controls.
    """
    return render(request, 'visualization/visualize.html')


def compare(request):
    """
    Side-by-side algorithm comparison page.

    Allows users to compare performance of different algorithms.
    """
    algorithms = Algorithm.objects.all()

    context = {
        'algorithms': algorithms,
    }

    return render(request, 'visualization/compare.html', context)
