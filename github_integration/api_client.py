"""
GitHub API Client for fetching repository and code data.

This module provides a comprehensive client for interacting with GitHub's REST API v3.
It includes error handling, rate limiting, caching, and retry logic.

Features:
- Repository search
- File content retrieval
- Rate limit handling
- Response caching
- Automatic retries with exponential backoff
- Comprehensive error handling

GitHub API Documentation: https://docs.github.com/en/rest
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
    """Raised when GitHub API rate limit is exceeded."""
    pass


class RepositoryNotFoundError(GitHubAPIError):
    """Raised when repository is not found."""
    pass


class GitHubAPIClient:
    """
    Client for interacting with GitHub REST API v3.

    This client handles all interactions with GitHub's API including:
    - Searching for repositories
    - Fetching repository details
    - Retrieving file contents
    - Managing rate limits
    - Caching responses

    Attributes:
        base_url: GitHub API base URL
        timeout: Request timeout in seconds
        cache_timeout: Cache duration in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries (seconds)
        session: Requests session for connection pooling

    Example:
        >>> client = GitHubAPIClient()
        >>> repos = client.search_repositories('django', max_results=10)
        >>> for repo in repos:
        ... print(repo['name'])
    """

    def __init__(
            self,
            api_token: Optional[str] = None,
            base_url: str = None,
            timeout: int = None,
            cache_timeout: int = None
    ):
        """
        Initialize GitHub API client.

        Args:
            api_token: Optional GitHub personal access token for higher rate limits
            base_url: GitHub API base URL (default from settings)
            timeout: Request timeout in seconds (default from settings)
            cache_timeout: Cache duration in seconds (default from settings)
        """
        self.base_url = base_url or getattr(settings, 'GITHUB_API_BASE_URL', 'https://api.github.com')
        self.timeout = timeout or getattr(settings, 'GITHUB_API_TIMEOUT', 10)
        self.cache_timeout = cache_timeout or getattr(settings, 'GITHUB_CACHE_TIMEOUT', 1800)
        self.max_retries = getattr(settings, 'GITHUB_API_MAX_RETRIES', 3)
        self.retry_delay = getattr(settings, 'GITHUB_API_RETRY_DELAY', 1)

        # Setup session with headers
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'AlgoViz-Pro/1.0'
        })

        # Add authentication token if provided
        if api_token:
            self.session.headers['Authorization'] = f'token {api_token}'

    def _make_request(
            self,
            endpoint: str,
            params: Optional[Dict] = None,
            use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Make HTTP request to GitHub API with retry logic and caching.

        Args:
            endpoint: API endpoint (e.g., '/search/repositories')
            params: Query parameters
            use_cache: Whether to use cached responses

        Returns:
            dict: JSON response from API

        Raises:
            RateLimitError: When rate limit is exceeded
            RepositoryNotFoundError: When resource is not found
            GitHubAPIError: For other API errors
        """
        url = f"{self.base_url}{endpoint}"

        # Check cache first
        if use_cache:
            cache_key = f"github_api:{endpoint}:{str(params)}"
            cached_response = cache.get(cache_key)
            if cached_response:
                logger.debug(f"Cache hit for {endpoint}")
                return cached_response

        # Retry logic with exponential backoff
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout
                )

                # Check rate limit
                if response.status_code == 403:
                    rate_limit_remaining = response.headers.get('X-RateLimit-Remaining', '0')
                    if rate_limit_remaining == '0':
                        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                        wait_time = reset_time - int(time.time())
                        raise RateLimitError(
                            f"GitHub API rate limit exceeded. "
                            f"Resets in {wait_time} seconds."
                        )

                # Check for 404
                if response.status_code == 404:
                    raise RepositoryNotFoundError(
                        f"Resource not found: {endpoint}"
                    )

                # Raise for other HTTP errors
                response.raise_for_status()

                # Parse JSON response
                data = response.json()

                # Cache successful response
                if use_cache:
                    cache.set(cache_key, data, self.cache_timeout)

                return data

            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    wait = self.retry_delay * (2 ** attempt)  # Exponential backoff
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

    def get_rate_limit(self) -> Dict[str, Any]:
        """
        Get current rate limit status.

        Returns:
            dict: Rate limit information containing:
                - limit: Maximum requests per hour
                - remaining: Remaining requests
                - reset: Unix timestamp when limit resets
                - used: Number of requests used

        Example:
            >>> client = GitHubAPIClient()
            >>> limits = client.get_rate_limit()
            >>> print(f"Remaining: {limits['remaining']}/{limits['limit']}")
        """
        try:
            data = self._make_request('/rate_limit', use_cache=False)
            return data['resources']['core']
        except Exception as e:
            logger.error(f"Failed to get rate limit: {e}")
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
        Search for GitHub repositories.

        Args:
            query: Search query (e.g., 'django', 'machine learning')
            language: Programming language filter (default: 'python')
            sort: Sort field ('stars', 'forks', 'updated')
            max_results: Maximum number of results to return

        Returns:
            list: List of repository dictionaries, each containing:
                - name: Repository name
                - full_name: Owner/repository
                - description: Repository description
                - html_url: GitHub URL
                - stargazers_count: Number of stars
                - language: Primary language
                - owner: Owner information

        Example:
            >>> client = GitHubAPIClient()
            >>> repos = client.search_repositories('django', max_results=5)
            >>> for repo in repos:
            ... print(f"{repo['full_name']}: {repo['stargazers_count']} stars")
        """
        # Build search query
        search_query = query
        if language:
            search_query += f" language:{language}"

        params = {
            'q': search_query,
            'sort': sort,
            'order': 'desc',
            'per_page': min(max_results, 100)  # GitHub max is 100
        }

        try:
            data = self._make_request('/search/repositories', params=params)
            repositories = data.get('items', [])

            # Extract relevant fields
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

    def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific repository.

        Args:
            owner: Repository owner (username or organization)
            repo: Repository name

        Returns:
            dict: Repository information

        Raises:
            RepositoryNotFoundError: If repository doesn't exist

        Example:
            >>> client = GitHubAPIClient()
            >>> repo = client.get_repository('django', 'django')
            >>> print(repo['description'])
        """
        endpoint = f'/repos/{owner}/{repo}'
        return self._make_request(endpoint)

    def get_repository_contents(
            self,
            owner: str,
            repo: str,
            path: str = ''
    ) -> List[Dict[str, Any]]:
        """
        Get contents of a repository directory.

        Args:
            owner: Repository owner
            repo: Repository name
            path: Path within repository (empty for root)

        Returns:
            list: List of files and directories

        Example:
            >>> client = GitHubAPIClient()
            >>> contents = client.get_repository_contents('django', 'django', 'django')
            >>> for item in contents:
            ... print(f"{item['name']} ({item['type']})")
        """
        endpoint = f'/repos/{owner}/{repo}/contents/{path}'
        return self._make_request(endpoint)

    def get_file_content(
            self,
            owner: str,
            repo: str,
            path: str,
            decode: bool = True
    ) -> str:
        """
        Get content of a specific file.

        Args:
            owner: Repository owner
            repo: Repository name
            path: File path within repository
            decode: Whether to decode base64 content

        Returns:
            str: File content (decoded if decode=True)

        Example:
            >>> client = GitHubAPIClient()
            >>> content = client.get_file_content('django', 'django', 'setup.py')
            >>> print(content[:100])
        """
        endpoint = f'/repos/{owner}/{repo}/contents/{path}'
        data = self._make_request(endpoint)

        if decode and data.get('encoding') == 'base64':
            import base64
            content = base64.b64decode(data['content']).decode('utf-8')
            return content

        return data.get('content', '')

    def search_code(
            self,
            query: str,
            owner: str = None,
            repo: str = None,
            extension: str = 'py',
            max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for code within repositories.

        Args:
            query: Code search query
            owner: Optional repository owner filter
            repo: Optional repository name filter
            extension: File extension filter (default: 'py')
            max_results: Maximum results to return

        Returns:
            list: List of code search results

        Example:
            >>> client = GitHubAPIClient()
            >>> results = client.search_code('def bubble_sort', extension='py')
            >>> for result in results:
            ... print(result['path'])
        """
        # Build search query
        search_query = query
        if extension:
            search_query += f" extension:{extension}"
        if owner and repo:
            search_query += f" repo:{owner}/{repo}"

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
            repo: str,
            path: str = '',
            max_files: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Recursively find all Python files in a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            path: Starting path (default: root)
            max_files: Maximum number of files to return

        Returns:
            list: List of Python file paths and metadata

        Example:
            >>> client = GitHubAPIClient()
            >>> files = client.get_python_files('django', 'django')
            >>> for file in files[:5]:
            ... print(file['path'])
        """
        python_files = []

        def scan_directory(current_path: str):
            if len(python_files) >= max_files:
                return

            try:
                contents = self.get_repository_contents(owner, repo, current_path)

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
                        # Recursively scan subdirectories
                        scan_directory(item['path'])

            except Exception as e:
                logger.warning(f"Error scanning {current_path}: {e}")

        scan_directory(path)
        return python_files