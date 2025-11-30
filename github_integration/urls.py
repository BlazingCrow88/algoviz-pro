"""
URL patterns for github_integration app.
"""
from django.urls import path
from . import views

app_name = 'github_integration'

urlpatterns = [
    # Search repositories
    path('', views.search_repositories, name='search'),
    path('search/', views.search_repositories, name='search'),

    # Repository details
    path('repo/<str:owner>/<str:repo>/', views.repository_detail, name='repo_detail'),

    # Fetch and view code
    path('fetch-code/', views.fetch_code, name='fetch_code'),
    path('code/<int:file_id>/', views.view_code, name='view_code'),
]
