"""
Views for the visualization app.

These handle the main user-facing pages where people interact with the algorithm
visualizations. Kept the views pretty simple since most of the heavy lifting happens
in JavaScript on the frontend - these just set up the initial page state.
"""
from django.shortcuts import render
from algorithms.models import Algorithm


def home(request):
    """
    Landing page for AlgoViz Pro.

    Shows an overview of what the platform does and displays stats about how many
    algorithms are available. The stats are dynamic so they update automatically
    as I add more algorithms to the database.
    """
    # Querying counts by category instead of just total because it looks way better
    # on the landing page to show "5 sorting, 3 searching, 2 graph algorithms" rather
    # than just "10 algorithms". Gives users a better sense of what's available.
    sorting_count = Algorithm.objects.filter(category='SORT').count()
    searching_count = Algorithm.objects.filter(category='SEARCH').count()
    graph_count = Algorithm.objects.filter(category='GRAPH').count()

    # Passing these to the template so we can display algorithm counts in the feature boxes
    # Could've calculated total_algorithms in the template but doing it here keeps the
    # template logic simpler
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

    This is where the actual magic happens - users select an algorithm and watch it
    run step-by-step. All the visualization logic is handled by JavaScript/Canvas,
    so this view is super simple - just renders the template with the controls.

    Decided not to pass any context here because the algorithm selection and execution
    happens entirely on the frontend via AJAX calls to the algorithms app.
    """
    return render(request, 'visualization/visualize.html')


def compare(request):
    """
    Side-by-side algorithm comparison page.

    Lets users run two algorithms at the same time to compare performance. This is
    really useful for understanding why Quick Sort is faster than Bubble Sort, etc.
    """
    # Grabbing all algorithms so users can pick which ones to compare
    # Originally filtered this by category but decided to let users compare across
    # categories too - like comparing Binary Search vs Linear Search is interesting
    algorithms = Algorithm.objects.all()

    context = {
        'algorithms': algorithms,
    }

    return render(request, 'visualization/compare.html', context)