"""
Tests for GitHub API integration.

Basic unit tests to verify the GitHubAPIClient initializes correctly and
has required attributes. These are sanity checks - more comprehensive tests
would mock HTTP requests to test actual API behavior, error handling, and
retry logic, but that's beyond this project's scope.

Run tests: python manage.py test github_integration
"""
from django.test import TestCase
from github_integration.api_client import GitHubAPIClient


class GitHubAPIClientTests(TestCase):
    """
    Test suite for GitHubAPIClient initialization and basic structure.

    Note: These tests verify the client sets up correctly but don't test
    actual API calls (would require mocking to avoid hitting GitHub and
    using up our rate limit). In production, we'd add tests for error
    handling, caching, and retry logic.
    """

    def test_client_initialization(self):
        """
        Test that GitHubAPIClient initializes without errors.

        Verifies the object is created and has expected methods.
        If __init__ has bugs, this catches them early.
        """
        client = GitHubAPIClient()

        # Verify object exists
        self.assertIsNotNone(client)

        # Verify critical methods are present
        self.assertTrue(hasattr(client, 'search_repositories'))
        self.assertTrue(hasattr(client, '_make_request'))

    def test_client_has_session(self):
        """
        Test that client creates a requests.Session for connection pooling.

        The session is critical for performance - it reuses TCP connections
        instead of creating new ones for each request. Without it, API calls
        would be much slower.
        """
        client = GitHubAPIClient()
        self.assertIsNotNone(client.session)

    def test_client_headers_set(self):
        """
        Test that client sets required HTTP headers.

        GitHub API requires 'Accept' and 'User-Agent' headers. Without them,
        GitHub returns 403 Forbidden. This test ensures we set them in __init__.
        """
        client = GitHubAPIClient()
        headers = client.session.headers

        # Verify required headers are present
        self.assertIn('Accept', headers)
        self.assertIn('User-Agent', headers)