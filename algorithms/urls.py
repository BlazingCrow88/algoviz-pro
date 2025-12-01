"""
URL routing configuration for the algorithms app.

What this file does: Maps web URLs to the view functions that handle them.
When someone visits /algorithms/execute/bubble/, Django uses this file to
figure out which function should handle that request.

Django's URL routing: Unlike Flask where you use decorators (@app.route),
Django keeps URL patterns in a separate file. This separation makes it easier
to see all routes at a glance and reorganize them without touching view code.

Why we need app-specific URLs: This project has multiple apps (algorithms,
visualization, github_integration, analytics), each with their own urls.py.
The main project urls.py includes these, creating a hierarchy:
- /algorithms/ → routes to this file
- /visualization/ → routes to visualization/urls.py
- etc.

URL pattern philosophy: Following RESTful conventions where possible:
- GET /algorithms/ → list all algorithms
- GET /algorithms/1/ → show algorithm #1
- POST /algorithms/execute/bubble/ → run bubble sort

"""
from django.urls import path
from . import views

# App namespace prevents naming conflicts
# Without this, multiple apps could have views named 'list' or 'detail'
# and Django wouldn't know which one to use when you do {% url 'list' %}
# With namespace: {% url 'algorithms:list' %} is unambiguous
app_name = 'algorithms'

urlpatterns = [
    # Main landing page: /algorithms/
    # Empty string '' means this matches /algorithms/ exactly (no extra path)
    #
    # Why 'list' as the name: Follows Django convention for list views
    # Can reverse this URL in templates with: {% url 'algorithms:list' %}
    # Can reverse in Python with: reverse('algorithms:list')
    #
    # Example URL: http://localhost:8000/algorithms/
    path('', views.algorithm_list, name='list'),

    # Detail page for a specific algorithm: /algorithms/5/
    # <int:pk> is a path converter that:
    #   - Captures an integer from the URL
    #   - Passes it to the view as a parameter named 'pk'
    #   - Only matches integers (rejects /algorithms/abc/)
    #
    # Why 'pk' instead of 'id': Django convention - 'pk' (primary key) is what
    # Django uses internally. Could use 'id' but 'pk' is more Djangonic.
    #
    # Security note: Django automatically validates that pk is an integer
    # so views.algorithm_detail doesn't need to check for SQL injection
    #
    # Example URL: http://localhost:8000/algorithms/3/
    # Calls: views.algorithm_detail(request, pk=3)
    path('<int:pk>/', views.algorithm_detail, name='detail'),

    # Execute an algorithm: /algorithms/execute/bubble/
    # <str:algo_name> captures a string (the algorithm name)
    #
    # Design decision: Why 'execute/' prefix?
    # Without it, /algorithms/bubble/ would be ambiguous:
    #   - Is 'bubble' an algorithm ID? (conflicts with <int:pk>)
    #   - Is 'bubble' an algorithm name to execute?
    # The 'execute/' prefix makes intent clear and prevents route conflicts
    #
    # Alternative designs considered:
    #   - /algorithms/<id>/execute/ - but this would require ID lookup first
    #   - /algorithms/run/<name>/ - 'execute' is more explicit
    #
    # Security consideration: The view needs to validate algo_name against
    # a whitelist of valid algorithms. Can't just eval() or import based on
    # user input! This is a potential attack vector the professor might test.
    #
    # Example URL: http://localhost:8000/algorithms/execute/bubble/
    # Calls: views.execute_algorithm(request, algo_name='bubble')
    path('execute/<str:algo_name>/', views.execute_algorithm, name='execute'),
]

# URL pattern testing notes:
# Django provides path converters: int, str, slug, uuid, path
# - int: Matches integers (what we use for pk)
# - str: Matches non-empty string, excluding '/' (what we use for algo_name)
# - slug: Matches slugs like 'bubble-sort' (we could use this too)
#
# Edge cases to handle in views:
# - /algorithms/999/ where algorithm #999 doesn't exist → 404
# - /algorithms/execute/invalid_algo/ → user-friendly error
# - /algorithms/execute// (empty name) → str converter prevents this
# - /algorithms/-1/ → int converter prevents this (only positive)
#
# URL reversing is critical for maintainability:
# BAD:  <a href="/algorithms/1/">Algorithm 1</a>
# GOOD: <a href="{% url 'algorithms:detail' pk=1 %}">Algorithm 1</a>
# If we change the URL pattern later, the GOOD version still works!