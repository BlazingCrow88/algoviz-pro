"""
Tests for GitHub API integration.
"""
from django.test import TestCase
from github_integration.api_client import GitHubAPIClient


class GitHubAPIClientTests(TestCase):
    """Test GitHub API client functionality."""

    def test_client_initialization(self):
        """Test client initializes correctly."""
        client = GitHubAPIClient()
        self.assertIsNotNone(client)
        self.assertTrue(hasattr(client, 'search_repositories'))
        self.assertTrue(hasattr(client, '_make_request'))

    def test_client_has_session(self):
        """Test client has requests session."""
        client = GitHubAPIClient()
        self.assertIsNotNone(client.session)

    def test_client_headers_set(self):
        """Test client has proper headers."""
        client = GitHubAPIClient()
        headers = client.session.headers
        self.assertIn('Accept', headers)
        self.assertIn('User-Agent', headers)