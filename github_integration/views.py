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
    """
    if request.method == 'POST':
        query = request.POST.get('query', '').strip()
        language = request.POST.get('language', 'python')
        sort = request.POST.get('sort', 'stars')

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
                max_results=20
            )

            # Show rate limit so user knows how many requests left (60/hour unauth)
            rate_limit = client.get_rate_limit()

            return render(request, 'github_integration/search.html', {
                'repositories': repositories,
                'query': query,
                'rate_limit': rate_limit,
            })

        except RateLimitError as e:
            return render(request, 'github_integration/search.html', {
                'error': str(e),  # Message includes time until reset
                'query': query,
            })

        except GitHubAPIError as e:
            return render(request, 'github_integration/search.html', {
                'error': f'GitHub API error: {str(e)}',
                'query': query,
            })

    # GET request - show empty search form
    return render(request, 'github_integration/search.html')


def repository_detail(request, owner, repo):
    """
    Display detailed information about a GitHub repository.

    Flow: Fetch from GitHub → cache in DB → list Python files → show cached files

    Args:
        owner: Repository owner (username or org)
        repo: Repository name
    """
    try:
        client = GitHubAPIClient()
        repo_data = client.get_repository(owner, repo)

        # get_or_create: If exists get it, if not create with defaults
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
            # Update existing repo with fresh data (stars/forks change over time)
            repository.description = repo_data.get('description', '')
            repository.stars = repo_data.get('stargazers_count', 0)
            repository.forks = repo_data.get('forks_count', 0)
            repository.save()

        # Limit to 20 files to avoid excessive API calls
        python_files = client.get_python_files(owner, repo, max_files=20)
        fetched_files = CodeFile.objects.filter(repository=repository)

        context = {
            'repository': repository,
            'repo_data': repo_data,
            'python_files': python_files,
            'fetched_files': fetched_files,
        }

        return render(request, 'github_integration/repo_detail.html', context)

    except RepositoryNotFoundError:
        return render(request, 'github_integration/repo_detail.html', {
            'error': f'Repository {owner}/{repo} not found'
        })

    except GitHubAPIError as e:
        return render(request, 'github_integration/repo_detail.html', {
            'error': f'Error fetching repository: {str(e)}'
        })


@require_http_methods(["POST"])
def fetch_code(request):
    """
    Fetch code file from GitHub and store in database.

    Flow: Fetch from GitHub → save to CodeFile → redirect to viewer

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

        owner = data.get('owner')
        repo = data.get('repo')
        path = data.get('path')

        if not all([owner, repo, path]):
            return redirect('github_integration:search')

        full_name = f"{owner}/{repo}"
        repository, _ = Repository.objects.get_or_create(
            full_name=full_name,
            defaults={
                'name': repo,
                'owner': owner,
                'url': f'https://github.com/{full_name}',
            }
        )

        client = GitHubAPIClient()
        content = client.get_file_content(owner, repo, path)

        # update_or_create: update if exists, create if not (prevents duplicates)
        code_file, created = CodeFile.objects.update_or_create(
            repository=repository,
            path=path,
            defaults={
                'name': path.split('/')[-1],
                'content': content,
                'size': len(content),
            }
        )

        repository.update_last_fetched()

        # Use named URL instead of hardcoding path
        return redirect('github_integration:view_code', file_id=code_file.id)

    except RepositoryNotFoundError:
        logger.error(f"File not found: {owner}/{repo}/{path}")
        return redirect('github_integration:repo_detail', owner=owner, repo=repo)

    except GitHubAPIError as e:
        logger.error(f'GitHub API error: {e}')
        return redirect('github_integration:repo_detail', owner=owner, repo=repo)

    except Exception as e:
        logger.error(f"Error fetching code: {e}")
        return redirect('github_integration:search')


def view_code(request, file_id):
    """
    Display a fetched code file with syntax highlighting.

    Shows cached code from our database (not fetching from GitHub again).
    Fast and doesn't use API rate limit.
    """
    # get_object_or_404: Returns 404 page instead of crashing with DoesNotExist
    code_file = get_object_or_404(CodeFile, id=file_id)

    context = {
        'code_file': code_file,
        'repository': code_file.repository,
    }

    return render(request, 'github_integration/code_view.html', context)