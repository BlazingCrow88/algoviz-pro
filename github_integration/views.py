"""
Views for the GitHub integration app.

Handles GitHub repository search, viewing, and code fetching.
Uses GitHubAPIClient to interact with GitHub's API and caches results
in our database to avoid hitting rate limits.
"""
from django.shortcuts import render, get_object_or_404, redirect
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
    Search GitHub repositories and display results.

    GET: Show empty search form
    POST: Execute search and show results

    Design: Handles both form display and form processing in one view.
    Could be split into separate views, but this is simpler for our use case.
    """
    if request.method == 'POST':
        # Extract search parameters from form
        query = request.POST.get('query', '').strip()
        language = request.POST.get('language', 'python')
        sort = request.POST.get('sort', 'stars')

        # Validate required input
        if not query:
            return render(request, 'github_integration/search.html', {
                'error': 'Please enter a search query'
            })

        try:
            # Search GitHub using our API client
            client = GitHubAPIClient()
            repositories = client.search_repositories(
                query=query,
                language=language,
                sort=sort,
                max_results=20  # Limit to prevent overwhelming UI
            )

            # Show rate limit status so user knows how many requests left
            # Important because GitHub limits to 60/hour unauthenticated
            rate_limit = client.get_rate_limit()

            return render(request, 'github_integration/search.html', {
                'repositories': repositories,
                'query': query,  # Pre-fill search box with current query
                'rate_limit': rate_limit,
            })

        except RateLimitError as e:
            # User hit GitHub's rate limit - show clear message
            return render(request, 'github_integration/search.html', {
                'error': str(e),  # Message includes time until reset
                'query': query,
            })

        except GitHubAPIError as e:
            # Other GitHub errors (network, server error, etc.)
            return render(request, 'github_integration/search.html', {
                'error': f'GitHub API error: {str(e)}',
                'query': query,
            })

    # GET request - show empty search form
    return render(request, 'github_integration/search.html')


def repository_detail(request, owner, repo):
    """
    Display detailed information about a GitHub repository.

    This view:
    1. Fetches fresh data from GitHub API
    2. Saves/updates repository in our database (caching)
    3. Lists Python files in the repository
    4. Shows which files we've already fetched

    Args:
        owner: Repository owner (username or org)
        repo: Repository name
    """
    try:
        # Fetch fresh repository data from GitHub
        client = GitHubAPIClient()
        repo_data = client.get_repository(owner, repo)

        # Cache repository in database
        # get_or_create returns (object, created) tuple
        # If exists: get it. If not: create with defaults.
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
            # Repository already exists - update with fresh data
            # Stars and forks change over time, so we refresh them
            repository.description = repo_data.get('description', '')
            repository.stars = repo_data.get('stargazers_count', 0)
            repository.forks = repo_data.get('forks_count', 0)
            repository.save()

        # List Python files in the repository
        # Limit to 20 to avoid excessive API calls and cluttered UI
        python_files = client.get_python_files(owner, repo, max_files=20)

        # Show which files we've already fetched (cached in database)
        # Helps user see what's available without re-fetching
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
        # Network error, server error, etc.
        return render(request, 'github_integration/repo_detail.html', {
            'error': f'Error fetching repository: {str(e)}'
        })


@require_http_methods(["POST"])  # Only allow POST - this fetches/modifies data
def fetch_code(request):
    """
    Fetch a code file from GitHub and store it in our database.

    This is the bridge between GitHub and our analytics:
    1. Fetch file from GitHub API
    2. Save to CodeFile model
    3. Redirect to view_code page for display

    POST parameters:
        owner: Repository owner
        repo: Repository name
        path: File path within repository

    Returns:
        Redirect to code view page (success) or repository page (error)
    """
    try:
        # Handle both JSON (from JavaScript) and form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        # Extract required parameters
        owner = data.get('owner')
        repo = data.get('repo')
        path = data.get('path')

        # Validate all parameters present
        if not all([owner, repo, path]):
            return redirect('github_integration:search')

        # Get or create repository record
        # We need the Repository object to link the CodeFile to
        full_name = f"{owner}/{repo}"
        repository, _ = Repository.objects.get_or_create(
            full_name=full_name,
            defaults={
                'name': repo,
                'owner': owner,
                'url': f'https://github.com/{full_name}',
            }
        )

        # Fetch file content from GitHub API
        client = GitHubAPIClient()
        content = client.get_file_content(owner, repo, path)

        # Save to database (or update if already exists)
        # update_or_create: If exists, update. If not, create.
        # This prevents duplicate CodeFile records for same file
        code_file, created = CodeFile.objects.update_or_create(
            repository=repository,
            path=path,
            defaults={
                'name': path.split('/')[-1],  # Extract filename from path
                'content': content,
                'size': len(content),
            }
        )

        # Update repository's last_fetched timestamp
        repository.update_last_fetched()

        # Redirect to code viewer page
        # Using redirect() with named URL is better than hardcoding URL
        return redirect('github_integration:view_code', file_id=code_file.id)

    except RepositoryNotFoundError:
        # File doesn't exist or repository is private
        logger.error(f"File not found: {owner}/{repo}/{path}")
        return redirect('github_integration:repo_detail', owner=owner, repo=repo)

    except GitHubAPIError as e:
        # API error (network, server, etc.)
        logger.error(f'GitHub API error: {e}')
        return redirect('github_integration:repo_detail', owner=owner, repo=repo)

    except Exception as e:
        # Unexpected error - log it and redirect to safe page
        logger.error(f"Error fetching code: {e}")
        return redirect('github_integration:search')


def view_code(request, file_id):
    """
    Display a fetched code file with syntax highlighting.

    Shows the cached code from our database (not fetching from GitHub again).
    This is fast and doesn't use up our API rate limit.

    Args:
        file_id: Primary key of CodeFile to display
    """
    # get_object_or_404: Fetch CodeFile or return 404 page if doesn't exist
    # Better than .get() which would crash with DoesNotExist exception
    code_file = get_object_or_404(CodeFile, id=file_id)

    context = {
        'code_file': code_file,
        'repository': code_file.repository,  # For breadcrumb navigation
    }

    return render(request, 'github_integration/code_view.html', context)