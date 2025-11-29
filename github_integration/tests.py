"""
Tests for GitHub API integration.
"""
from django.test import TestCase
from unittest.mock import Mock, patch
from github_integration.api_client import GitHubAPIClient, GitHubAPIError


class GitHubAPIClientTests(TestCase):
    """Test GitHub API client functionality."""

    def setUp(self):
        """Set up test client."""
        self.client = GitHubAPIClient()

    @patch('requests.Session.get')
    def test_search_repositories_success(self, mock_get):
        """Test successful repository search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [
                {
                    'name': 'test-repo',
                    'full_name': 'user/test-repo',
                    'description': 'Test repository',
                    'html_url': 'https://github.com/user/test-repo',
                    'stargazers_count': 100,
                    'forks_count': 10,
                    'language': 'Python'
                }
            ]
        }
        mock_get.return_value = mock_response

        results = self.client.search_repositories('django', language='python')

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'test-repo')
        self.assertEqual(results[0]['language'], 'Python')

    @patch('requests.Session.get')
    def test_api_handles_errors(self, mock_get):
        """Test API error handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_get.return_value = mock_response

        with self.assertRaises(GitHubAPIError):
            self.client.search_repositories('django')

    def test_client_initialization(self):
        """Test client initializes correctly."""
        client = GitHubAPIClient()
        self.assertIsNotNone(client)
        self.assertTrue(hasattr(client, 'search_repositories'))