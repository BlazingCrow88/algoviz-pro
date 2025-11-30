"""
URL patterns for github_integration app.

Routes for searching GitHub repos, viewing details, and fetching code files.
I kept the URL structure pretty simple - just enough to handle the main workflows
without getting too nested or complicated.
"""
from django.urls import path
from . import views

app_name = 'github_integration'

urlpatterns = [
    # Both root and /search/ go to the same view - makes it more flexible
    # Users can access the search from either URL without getting a 404
    path('', views.search_repositories, name='search'),
    path('search/', views.search_repositories, name='search'),

    # Repository detail page - uses owner and repo name from the URL
    # This matches GitHub's URL structure (github.com/owner/repo) which felt natural
    path('repo/<str:owner>/<str:repo>/', views.repository_detail, name='repo_detail'),

    # POST endpoint for actually fetching code files from GitHub
    # Separated this from search because it's a different action - search just displays
    # results, fetch_code actually saves files to the database
    path('fetch-code/', views.fetch_code, name='fetch_code'),

    # View individual code files by their database ID
    # Using the ID instead of path makes the URL simpler and avoids encoding issues
    # with file paths that have slashes and special characters
    path('code/<int:file_id>/', views.view_code, name='view_code'),
]