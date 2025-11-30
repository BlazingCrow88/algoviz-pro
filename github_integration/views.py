"""
Views for the github_integration app.

Handles the main user interactions with GitHub - searching repos, viewing details,
and fetching code files to analyze. Most of the heavy lifting happens in the API
client, these views just coordinate between the GitHub API and our templates.
"""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import logging

from .api_client import GitHubAPIClient, GitHubAPIError, RateLimitError, RepositoryNotFoundError
from .models import Repository, CodeFile

logger = logging.getLogger(__name__)


def search_repositories(request):
    """
    Main search interface for finding GitHub repositories.

    I'm handling both GET (show the form) and POST (do the search) in one view
    instead of separating them - keeps things simpler since they share the same
    template anyway. The rate limit info gets displayed to users so they know
    how many API calls they have left.
    """
    if request.method == 'POST':
        query = request.POST.get('query', '').strip()
        language = request.POST.get('language', 'python')
        sort = request.POST.get('sort', 'stars')

        # Don't waste an API call on empty searches
        if not query:
            return render(request, 'github_integration/search.html', {
                'error': 'Please enter a search query'
            })

        try:
            client = GitHubAPIClient()
            repositories = client.search_repositories(
                query=query,
                language=language,
                sort=sort,
                max_results=20  # Limiting to 20 to keep the page from getting too long
            )

            # Show rate limit so users know when they might hit the limit
            rate_limit = client.get_rate_limit()

            return render(request, 'github_integration/search.html', {
                'repositories': repositories,
                'query': query,
                'rate_limit': rate_limit,
            })

        except RateLimitError as e:
            # User-friendly error message when they've hit GitHub's rate limit
            return render(request, 'github_integration/search.html', {
                'error': str(e),
                'query': query,
            })

        except GitHubAPIError as e:
            # Catch-all for other GitHub API issues (network errors, etc.)
            return render(request, 'github_integration/search.html', {
                'error': f'GitHub API error: {str(e)}',
                'query': query,
            })

    # GET request - just show the empty search form
    return render(request, 'github_integration/search.html')


def repository_detail(request, owner, repo):
    """
    Show detailed info about a specific repository and its Python files.

    This view does double duty - it fetches fresh data from GitHub's API but also
    saves/updates the repo in our database. That way we can track what repos users
    have looked at even after the cache expires. The get_or_create pattern prevents
    duplicate repos in the database.
    """
    try:
        client = GitHubAPIClient()
        repo_data = client.get_repository(owner, repo)

        # Save to our database or update if it already exists
        repository, created = Repository.objects.get_or_create(
            full_name=repo_data['full_name'],
            defaults={
                'name': repo_data['name'],
                'owner': repo_data['owner']['login'],
                'description': repo_data.get('description', ''),
                'url': repo_data['html_url'],
                'language': repo_data.get('language', ''),
                'stars': repo_data.get('stargazers_count', 0),
                'forks': repo_data.get('forks_count', 0),
            }
        )

        if not created:
            # Update star/fork counts since they change over time
            # Description could change too if the owner updates it
            repository.description = repo_data.get('description', '')
            repository.stars = repo_data.get('stargazers_count', 0)
            repository.forks = repo_data.get('forks_count', 0)
            repository.save()

        # Find Python files in the repo - limited to 20 to avoid burning API calls
        python_files = client.get_python_files(owner, repo, max_files=20)

        # Show which files we've already downloaded and analyzed
        fetched_files = CodeFile.objects.filter(repository=repository)

        context = {
            'repository': repository,
            'repo_data': repo_data,
            'python_files': python_files,
            'fetched_files': fetched_files,
        }

        return render(request, 'github_integration/repo_detail.html', context)

    except RepositoryNotFoundError:
        # Repository doesn't exist or is private
        return render(request, 'github_integration/repo_detail.html', {
            'error': f'Repository {owner}/{repo} not found'
        })

    except GitHubAPIError as e:
        # Network issues, rate limits, etc
        return render(request, 'github_integration/repo_detail.html', {
            'error': f'Error fetching repository: {str(e)}'
        })


@require_http_methods(["POST"])  # Only allow POST to prevent accidental fetches from GET requests
@csrf_exempt  # Needed for AJAX requests that don't include CSRF token
def fetch_code(request):
    """
    Download a code file from GitHub and save it to our database.

    Returns JSON instead of rendering a template since this is called via AJAX.
    I had to add csrf_exempt because the AJAX calls weren't sending the CSRF token
    properly and kept getting 403 errors. Not ideal security-wise but fine for this
    project since we're not handling sensitive data.
    """
    try:
        # Handle both JSON and form-encoded requests
        # Different JavaScript libraries send data differently, so supporting both
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        owner = data.get('owner')
        repo = data.get('repo')
        path = data.get('path')

        # Validate we got all required parameters before hitting the API
        if not all([owner, repo, path]):
            return JsonResponse({
                'error': 'Missing required parameters: owner, repo, path'
            }, status=400)

        # Make sure we have a Repository record for this repo
        full_name = f"{owner}/{repo}"
        repository, _ = Repository.objects.get_or_create(
            full_name=full_name,
            defaults={
                'name': repo,
                'owner': owner,
                'url': f'https://github.com/{full_name}',
            }
        )

        # Actually fetch the file content from GitHub
        client = GitHubAPIClient()
        content = client.get_file_content(owner, repo, path)

        # Store in database - update_or_create prevents duplicates if they fetch the same file twice
        code_file, created = CodeFile.objects.update_or_create(
            repository=repository,
            path=path,
            defaults={
                'name': path.split('/')[-1],  # Extract just the filename from the full path
                'content': content,
                'size': len(content),
            }
        )

        # Track when we last fetched from this repo
        repository.update_last_fetched()

        # Return all the file info as JSON for the frontend to use
        return JsonResponse({
            'success': True,
            'file': {
                'id': code_file.id,
                'path': code_file.path,
                'name': code_file.name,
                'content': code_file.content,
                'size': code_file.size,
                'line_count': code_file.get_line_count(),
            },
            'created': created,  # Let frontend know if this was a new file or an update
        })

    except RepositoryNotFoundError:
        # File doesn't exist in the repo or repo is private
        return JsonResponse({
            'error': 'File not found in repository'
        }, status=404)

    except GitHubAPIError as e:
        # GitHub API issues - network, rate limits, etc
        return JsonResponse({
            'error': f'GitHub API error: {str(e)}'
        }, status=500)

    except Exception as e:
        # Catch-all for unexpected errors - better to return an error than crash
        logger.error(f"Error fetching code: {e}")
        return JsonResponse({
            'error': f'An error occurred: {str(e)}'
        }, status=500)


def view_code(request, file_id):
    """
    Display a code file we've already fetched from GitHub.

    Pretty straightforward - just grab the file from the database and render it.
    Using get_object_or_404 means we automatically show a 404 page if someone
    tries to view a file ID that doesn't exist (instead of crashing).
    """
    code_file = get_object_or_404(CodeFile, id=file_id)

    context = {
        'code_file': code_file,
        'repository': code_file.repository,
    }

    return render(request, 'github_integration/code_view.html', context)