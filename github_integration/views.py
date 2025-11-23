"""
Views for the github_integration app.

Handles GitHub repository search, viewing, and code fetching.
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
    Search GitHub repositories and display results.

    GET: Show search form
    POST: Perform search and show results
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

            # Get rate limit info
            rate_limit = client.get_rate_limit()

            return render(request, 'github_integration/search.html', {
                'repositories': repositories,
                'query': query,
                'rate_limit': rate_limit,
            })

        except RateLimitError as e:
            return render(request, 'github_integration/search.html', {
                'error': str(e),
                'query': query,
            })

        except GitHubAPIError as e:
            return render(request, 'github_integration/search.html', {
                'error': f'GitHub API error: {str(e)}',
                'query': query,
            })

    # GET request - show search form
    return render(request, 'github_integration/search.html')


def repository_detail(request, owner, repo):
    """
    Display detailed information about a repository.

    Args:
        owner: Repository owner username
        repo: Repository name
    """
    try:
        client = GitHubAPIClient()
        repo_data = client.get_repository(owner, repo)

        # Get or create repository in database
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
            # Update existing repository data
            repository.description = repo_data.get('description', '')
            repository.stars = repo_data.get('stargazers_count', 0)
            repository.forks = repo_data.get('forks_count', 0)
            repository.save()

        # Get Python files in repository
        python_files = client.get_python_files(owner, repo, max_files=20)

        # Get files already fetched from this repository
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
@csrf_exempt
def fetch_code(request):
    """
    Fetch code file from GitHub and store in database.

    POST parameters:
        - owner: Repository owner
        - repo: Repository name
        - path: File path within repository

    Returns:
        JSON response with file content and metadata
    """
    try:
        # Parse request data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        owner = data.get('owner')
        repo = data.get('repo')
        path = data.get('path')

        if not all([owner, repo, path]):
            return JsonResponse({
                'error': 'Missing required parameters: owner, repo, path'
            }, status=400)

        # Get or create repository
        full_name = f"{owner}/{repo}"
        repository, _ = Repository.objects.get_or_create(
            full_name=full_name,
            defaults={
                'name': repo,
                'owner': owner,
                'url': f'https://github.com/{full_name}',
            }
        )

        # Fetch file content from GitHub
        client = GitHubAPIClient()
        content = client.get_file_content(owner, repo, path)

        # Store in database
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
            'created': created,
        })

    except RepositoryNotFoundError:
        return JsonResponse({
            'error': 'File not found in repository'
        }, status=404)

    except GitHubAPIError as e:
        return JsonResponse({
            'error': f'GitHub API error: {str(e)}'
        }, status=500)

    except Exception as e:
        logger.error(f"Error fetching code: {e}")
        return JsonResponse({
            'error': f'An error occurred: {str(e)}'
        }, status=500)


def view_code(request, file_id):
    """
    Display a fetched code file with syntax highlighting.

    Args:
        file_id: ID of CodeFile to display
    """
    code_file = get_object_or_404(CodeFile, id=file_id)

    context = {
        'code_file': code_file,
        'repository': code_file.repository,
    }

    return render(request, 'github_integration/code_view.html', context)