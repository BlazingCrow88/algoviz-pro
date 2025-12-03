"""
GitHub API Client - handles all communication with GitHub's REST API.

Provides clean interface for searching repos, fetching files, and handling
GitHub's quirks (rate limiting, base64 encoding, pagination).

Rate limits: 60/hour unauthenticated, 5000/hour with token
GitHub API docs: https://docs.github.com/en/rest
"""
import requests
import time
import logging
from typing import Dict, List, Optional, Any
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class GitHubAPIError(Exception):
    """Base exception for all GitHub API errors."""
    pass


class RateLimitError(GitHubAPIError):
    """GitHub rate limit exceeded (60/hr unauthenticated, 5000/hr with token)."""
    pass


class RepositoryNotFoundError(GitHubAPIError):
    """Repository doesn't exist or is private."""
    pass


class GitHubAPIClient:
    """
    Client for GitHub REST API v3.

    Handles rate limiting, caching, retries, authentication, and error handling.
    Uses connection pooling for performance.

    Usage:
        client = GitHubAPIClient()
        repos = client.search_repositories('django')
        code = client.get_file_content('django', 'django', 'setup.py')
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
            api_token: GitHub token (increases rate limit to 5000/hour)
            base_url: API URL (default: https://api.github.com)
            timeout: Request timeout seconds (default: 10)
            cache_timeout: Cache duration seconds (default: 1800 = 30min)

        Design: All parameters optional with sensible defaults. Pull from Django
        settings for configurability without code changes.
        """
        # Get config from Django settings or use defaults
        self.base_url = base_url or getattr(settings, 'GITHUB_API_BASE_URL', 'https://api.github.com')
        self.timeout = timeout or getattr(settings, 'GITHUB_API_TIMEOUT', 10)
        self.cache_timeout = cache_timeout or getattr(settings, 'GITHUB_CACHE_TIMEOUT', 1800)
        self.max_retries = getattr(settings, 'GITHUB_API_MAX_RETRIES', 3)
        self.retry_delay = getattr(settings, 'GITHUB_API_RETRY_DELAY', 1)

        # Connection pooling for performance (reuses TCP connections)
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'AlgoViz-Pro/1.0'  # Required by GitHub
        })

        # Add auth token if provided
        if api_token:
            self.session.headers['Authorization'] = f'token {api_token}'

    def _make_request(
            self,
            endpoint: str,
            params: Optional[Dict] = None,
            use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Core request method - all API calls go through here.

        Flow: Check cache → Make request → Handle errors → Retry with exponential
        backoff → Cache success. Industry-standard retry pattern (AWS, GCP, etc).

        Why exponential backoff: Transient failures often resolve themselves.
        Retries at 1s, 2s, 4s give increasing time for recovery without hammering
        the API. Formula: retry_delay * (2 ** attempt_number).

        Why caching: GitHub data doesn't change fast. Cache key includes endpoint
        AND params so different queries don't collide. Lets us make same query 30x
        in an hour but only use 1 API request - critical for rate limits.

        Args:
            endpoint: API endpoint (e.g. '/search/repositories')
            params: Query parameters (e.g. {'q': 'django'})
            use_cache: Check cache first (False for rate_limit check)

        Returns:
            dict: Parsed JSON response

        Raises:
            RateLimitError: Hit rate limit
            RepositoryNotFoundError: 404 not found
            GitHubAPIError: Network/server errors
        """
        url = f"{self.base_url}{endpoint}"
        cache_key = None

        # Check cache to avoid API call
        if use_cache:
            cache_key = f"github_api:{endpoint}:{str(params)}"
            cached_response = cache.get(cache_key)
            if cached_response:
                logger.debug(f"Cache hit for {endpoint}")
                return cached_response

        # Retry loop with exponential backoff
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)

                # Handle rate limiting (HTTP 403)
                if response.status_code == 403:
                    rate_limit_remaining = response.headers.get('X-RateLimit-Remaining', '0')
                    if rate_limit_remaining == '0':
                        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                        wait_time = reset_time - int(time.time())
                        raise RateLimitError(
                            f"GitHub API rate limit exceeded. Resets in {wait_time} seconds."
                        )

                # Handle 404 with specific exception
                if response.status_code == 404:
                    raise RepositoryNotFoundError(f"Resource not found: {endpoint}")

                response.raise_for_status()

                # Parse and cache success
                data = response.json()
                if use_cache and cache_key:
                    cache.set(cache_key, data, self.cache_timeout)
                return data

            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    wait = self.retry_delay * (2 ** attempt)
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
        Check current rate limit status (requests remaining and reset time).

        Returns:
            dict: {'limit': 5000, 'remaining': 4850, 'reset': 1638360000, 'used': 150}

        Note: Doesn't use cache (use_cache=False) - we want real-time info.
        """
        try:
            data = self._make_request('/rate_limit', use_cache=False)
            return data['resources']['core']
        except Exception as e:
            logger.error(f"Failed to get rate limit: {e}")
            return {'limit': 0, 'remaining': 0, 'reset': 0, 'used': 0}

    def search_repositories(
            self,
            query: str,
            language: str = 'python',
            sort: str = 'stars',
            max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search GitHub repositories matching query.

        Automatically adds language filter since this is a Python algorithm tool.
        Query becomes "django language:python".

        Args:
            query: Search term (e.g. 'django', 'machine learning')
            language: Programming language filter (default: 'python')
            sort: Sort by 'stars', 'forks', or 'updated' (default: 'stars')
            max_results: Number of results to return (max 100)

        Returns:
            list: Repository dicts with relevant fields extracted

        Why extract fields: GitHub returns 100+ fields per repo. We only need ~10,
        so extract those into clean dicts. Isolates us from API changes.
        """
        # Build search query with language filter
        search_query = query
        if language:
            search_query += f" language:{language}"

        params = {
            'q': search_query,
            'sort': sort,
            'order': 'desc',
            'per_page': min(max_results, 100)
        }

        try:
            data = self._make_request('/search/repositories', params=params)
            repositories = data.get('items', [])

            # Extract only fields we care about
            results = []
            for repository in repositories[:max_results]:
                results.append({
                    'name': repository['name'],
                    'full_name': repository['full_name'],
                    'description': repository.get('description', 'No description'),
                    'html_url': repository['html_url'],
                    'stargazers_count': repository.get('stargazers_count', 0),
                    'forks_count': repository.get('forks_count', 0),
                    'language': repository.get('language', 'Unknown'),
                    'owner': {
                        'login': repository['owner']['login'],
                        'avatar_url': repository['owner']['avatar_url'],
                    },
                    'created_at': repository.get('created_at'),
                    'updated_at': repository.get('updated_at'),
                })
            return results

        except Exception as e:
            logger.error(f"Repository search failed: {e}")
            raise

    def get_repository(self, owner: str, repo_name: str) -> Dict[str, Any]:
        """
        Get detailed info about specific repository.

        Different from search_repositories() which finds many repos - this gets
        full details about one known repo.
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
        List contents of repository directory.

        Args:
            owner: Repository owner
            repo_name: Repository name
            path: Path within repo (empty string = root)

        Returns:
            list: Files and directories with name, type, path, size

        GitHub quirk: Returns LIST for directories but DICT for single files.
        We normalize by always returning a list.
        """
        endpoint = f'/repos/{owner}/{repo_name}/contents/{path}'
        result = self._make_request(endpoint)

        # Normalize to always return list
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
        Get contents of specific file from repository.

        Args:
            owner: Repository owner
            repo_name: Repository name
            path: File path within repository
            decode: Decode from base64 to text (default: True)

        Returns:
            str: File contents as text

        GitHub quirk: Returns file contents as base64-encoded strings (JSON can't
        represent raw binary). We auto-decode to UTF-8 for Python source code.
        """
        endpoint = f'/repos/{owner}/{repo_name}/contents/{path}'
        data = self._make_request(endpoint)

        # Decode from base64 if needed
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
        Search for code within repositories (searches actual file contents).

        Args:
            query: Code to search for (e.g. "def bubble_sort")
            owner: Optional repo owner filter
            repo_name: Optional repo name filter
            extension: File extension filter (default: 'py')
            max_results: Max results to return

        Returns:
            list: Code search results with path, repo, matches

        Warning: Code search has stricter rate limit - only 30 requests per minute
        (vs 5000/hour for other endpoints). Don't spam this.
        """
        search_query = query
        if extension:
            search_query += f" extension:{extension}"
        if owner and repo_name:
            search_query += f" repo:{owner}/{repo_name}"

        params = {'q': search_query, 'per_page': min(max_results, 100)}

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
        Recursively find all Python files in repository.

        Args:
            owner: Repository owner
            repo_name: Repository name
            path: Starting path (default: root)
            max_files: Max files to return (prevents too many API calls)

        Returns:
            list: Python files with path, name, size, download_url

        Why max_files: Some repos (like Django) have hundreds of Python files.
        Fetching all would exceed rate limits and overwhelm user. One API call
        per directory level - deeply nested repos add up fast.

        Implementation: Nested recursive function has access to python_files list
        from parent scope (closure pattern).
        """
        python_files = []

        def scan_directory(current_path: str):
            """Recursively scan directory for Python files."""
            # Stop if we've found enough
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
                        scan_directory(item['path'])  # Recurse into subdirectory

            except Exception as e:
                # Skip directories we can't access
                logger.warning(f"Error scanning {current_path}: {e}")

        scan_directory(path)
        return python_files