"""
GitHub API Client for fetching repository and code data.

Handles all the GitHub API interactions for the project. The main challenge here
was dealing with GitHub's rate limits - you only get 60 requests/hour without
authentication, so I had to implement caching and retry logic to avoid constantly
hitting the limit during testing.

The exponential backoff was particularly important because sometimes GitHub's API
just times out randomly, especially when searching through large repos.
"""
import requests
import time
import logging
from typing import Dict, List, Optional, Any
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class GitHubAPIError(Exception):
    """Base exception for GitHub API errors."""
    pass


class RateLimitError(GitHubAPIError):
    """Raised when we hit GitHub's rate limit - happens more than you'd think!"""
    pass


class RepositoryNotFoundError(GitHubAPIError):
    """Raised when repository doesn't exist or isn't public."""
    pass


class GitHubAPIClient:
    """
    Handles all GitHub API requests for the app.

    I built this as a separate client class to keep all the API logic in one place
    instead of scattering requests throughout the views. Makes it way easier to handle
    errors and rate limiting consistently.

    The caching is crucial - without it, you'd burn through GitHub's rate limit in
    like 5 minutes of testing. I'm caching responses for 30 minutes by default since
    repo data doesn't change that frequently anyway.
    """

    def __init__(
            self,
            api_token: Optional[str] = None,
            base_url: str = None,
            timeout: int = None,
            cache_timeout: int = None
    ):
        """
        Set up the GitHub API client.

        The api_token is optional but highly recommended - it bumps your rate limit
        from 60 to 5000 requests per hour. Without it, you'll hit the limit constantly
        during development.
        """
        self.base_url = base_url or getattr(settings, 'GITHUB_API_BASE_URL', 'https://api.github.com')
        self.timeout = timeout or getattr(settings, 'GITHUB_API_TIMEOUT', 10)
        self.cache_timeout = cache_timeout or getattr(settings, 'GITHUB_CACHE_TIMEOUT', 1800)  # 30 minutes
        self.max_retries = getattr(settings, 'GITHUB_API_MAX_RETRIES', 3)
        self.retry_delay = getattr(settings, 'GITHUB_API_RETRY_DELAY', 1)

        # Using a session for connection pooling - more efficient than creating
        # a new connection for every request
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/vnd.github.v3+json',  # GitHub requires this header for their v3 API
            'User-Agent': 'AlgoViz-Pro/1.0'  # GitHub requires a user agent or they reject the request
        })

        if api_token:
            self.session.headers['Authorization'] = f'token {api_token}'

    def _make_request(
            self,
            endpoint: str,
            params: Optional[Dict] = None,
            use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Core request method that handles all the messy stuff like retries and caching.

        I made this a separate method so that I don't have to copy-paste retry logic and
        cache checks in every API call. The exponential backoff helps when GitHub's
        servers are being slow - starts at 1 second, then 2, then 4 if retries are needed.
        """
        url = f"{self.base_url}{endpoint}"
        cache_key = None

        # Check cache first to avoid unnecessary API calls
        if use_cache:
            cache_key = f"github_api:{endpoint}:{str(params)}"
            cached_response = cache.get(cache_key)
            if cached_response:
                logger.debug(f"Cache hit for {endpoint}")
                return cached_response

        # Try up to max_retries times before giving up
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout
                )

                # GitHub returns 403 for both auth failures AND rate limits, so we
                # need to check the specific headers to know which it is
                if response.status_code == 403:
                    rate_limit_remaining = response.headers.get('X-RateLimit-Remaining', '0')
                    if rate_limit_remaining == '0':
                        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                        wait_time = reset_time - int(time.time())
                        raise RateLimitError(
                            f"GitHub API rate limit exceeded. "
                            f"Resets in {wait_time} seconds."
                        )

                if response.status_code == 404:
                    raise RepositoryNotFoundError(
                        f"Resource not found: {endpoint}"
                    )

                response.raise_for_status()
                data = response.json()

                # Only cache successful responses
                if use_cache and cache_key:
                    cache.set(cache_key, data, self.cache_timeout)

                return data

            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    wait = self.retry_delay * (2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"Request timeout, retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise GitHubAPIError("Request timed out after multiple retries")

            except requests.exceptions.ConnectionError:
                if attempt < self.max_retries - 1:
                    wait = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Connection error, retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise GitHubAPIError("Connection failed after multiple retries")

            except requests.exceptions.RequestException as e:
                raise GitHubAPIError(f"Request failed: {str(e)}")

        raise GitHubAPIError("Request failed: Maximum retries exceeded")

    def get_rate_limit(self) -> Dict[str, Any]:
        """
        Check how many API calls we have left.

        Useful for debugging when things start failing - usually means we hit the limit.
        Don't cache this one since we want real-time data on our remaining requests.
        """
        try:
            data = self._make_request('/rate_limit', use_cache=False)
            return data['resources']['core']
        except Exception as e:
            logger.error(f"Failed to get rate limit: {e}")
            # Return zeros if we can't get rate limit info
            return {
                'limit': 0,
                'remaining': 0,
                'reset': 0,
                'used': 0
            }

    def search_repositories(
            self,
            query: str,
            language: str = 'python',
            sort: str = 'stars',
            max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search GitHub for repositories matching the query.

        I'm defaulting to Python repos sorted by stars since that's what we care about
        for this project - finding popular algorithm implementations. The language
        filter helps avoid getting repos in languages we can't analyze.
        """
        # Build the search query string that GitHub expects
        search_query = query
        if language:
            search_query += f" language:{language}"

        params = {
            'q': search_query,
            'sort': sort,
            'order': 'desc',
            'per_page': min(max_results, 100)  # GitHub's API maxes out at 100 per page
        }

        try:
            data = self._make_request('/search/repositories', params=params)
            repositories = data.get('items', [])

            # Pull out just the fields we actually need instead of storing everything
            # GitHub sends back. Keeps our database cleaner and reduces storage.
            results = []
            for repo in repositories[:max_results]:
                results.append({
                    'name': repo['name'],
                    'full_name': repo['full_name'],
                    'description': repo.get('description', 'No description'),
                    'html_url': repo['html_url'],
                    'stargazers_count': repo.get('stargazers_count', 0),
                    'forks_count': repo.get('forks_count', 0),
                    'language': repo.get('language', 'Unknown'),
                    'owner': {
                        'login': repo['owner']['login'],
                        'avatar_url': repo['owner']['avatar_url'],
                    },
                    'created_at': repo.get('created_at'),
                    'updated_at': repo.get('updated_at'),
                })

            return results

        except Exception as e:
            logger.error(f"Repository search failed: {e}")
            raise

    def get_repository(self, owner: str, repo_name: str) -> Dict[str, Any]:
        """
        Get detailed info about a specific repository.

        Used when we need more than just search results - like when actually
        fetching code files from a repo.
        """
        endpoint = f'/repos/{owner}/{repo_name}'
        return self._make_request(endpoint)

    def get_repository_contents(
            self,
            owner: str,
            repo_name: str,
            path: str = ''
    ) -> List[Dict[str, Any]]:
        """
        List files and folders in a repository directory.

        GitHub's API is a bit weird here - it returns a list for directories but
        a single dict for individual files, so I'm normalizing that to always
        return a list.
        """
        endpoint = f'/repos/{owner}/{repo_name}/contents/{path}'
        result = self._make_request(endpoint)

        # Normalize the response to always be a list for consistency
        if isinstance(result, list):
            return result
        else:
            return [result]

    def get_file_content(
            self,
            owner: str,
            repo_name: str,
            path: str,
            decode: bool = True
    ) -> str:
        """
        Fetch the actual content of a file from GitHub.

        GitHub sends file contents as base64 encoded by default (no idea why),
        so we need to decode it to get readable text. That's what the decode
        parameter is for.
        """
        endpoint = f'/repos/{owner}/{repo_name}/contents/{path}'
        data = self._make_request(endpoint)

        if decode and data.get('encoding') == 'base64':
            import base64
            decoded_content = base64.b64decode(data['content']).decode('utf-8')
            return decoded_content

        return data.get('content', '')

    def search_code(
            self,
            query: str,
            owner: str = None,
            repo_name: str = None,
            extension: str = 'py',
            max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for code snippets across GitHub.

        Really useful for finding algorithm implementations. The extension filter
        keeps us from getting results in random languages.
        """
        search_query = query
        if extension:
            search_query += f" extension:{extension}"
        if owner and repo_name:
            search_query += f" repo:{owner}/{repo_name}"

        params = {
            'q': search_query,
            'per_page': min(max_results, 100)
        }

        try:
            data = self._make_request('/search/code', params=params)
            return data.get('items', [])[:max_results]
        except Exception as e:
            logger.error(f"Code search failed: {e}")
            raise

    def get_python_files(
            self,
            owner: str,
            repo_name: str,
            path: str = '',
            max_files: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Recursively find all Python files in a repo.

        This was tricky to implement - had to make it recursive to handle nested
        directories, but also needed to limit it so we don't try to fetch like
        1000 files and blow through our API limits. That's why max_files exists.
        """
        python_files = []

        def scan_directory(current_path: str):
            # Stop if we've hit our file limit
            if len(python_files) >= max_files:
                return

            try:
                contents = self.get_repository_contents(owner, repo_name, current_path)

                for item in contents:
                    if len(python_files) >= max_files:
                        break

                    if item['type'] == 'file' and item['name'].endswith('.py'):
                        python_files.append({
                            'path': item['path'],
                            'name': item['name'],
                            'size': item.get('size', 0),
                            'download_url': item.get('download_url'),
                        })
                    elif item['type'] == 'dir':
                        # Dive into subdirectories to find more Python files
                        scan_directory(item['path'])

            except Exception as e:
                # Don't crash the whole scan if one directory fails
                logger.warning(f"Error scanning {current_path}: {e}")

        scan_directory(path)
        return python_files