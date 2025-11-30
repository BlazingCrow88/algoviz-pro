"""
Tests for GitHub API integration.

Basic test suite to make sure the GitHub client initializes properly and has
all the required components. These are mostly sanity checks to catch obvious
issues before we start making actual API calls.
"""
from django.test import TestCase
from github_integration.api_client import GitHubAPIClient


class GitHubAPIClientTests(TestCase):
    """
    Test the GitHub API client.

    I'm keeping these tests pretty basic since we can't really test the actual
    API calls without either hitting GitHub's real API (which would burn through
    rate limits) or setting up mocks (which seemed overkill for this project).
    These tests at least verify the client sets up correctly.
    """

    def test_client_initialization(self):
        """
        Make sure the client can be created without errors.

        This caught an issue early on where I had a typo in the __init__ method
        and the whole thing would crash on startup. Now if someone breaks the
        constructor, this test will fail immediately.
        """
        client = GitHubAPIClient()
        self.assertIsNotNone(client)
        # Verify the main methods exist - would catch accidental deletions or typos
        self.assertTrue(hasattr(client, 'search_repositories'))
        self.assertTrue(hasattr(client, '_make_request'))

    def test_client_has_session(self):
        """
        Verify the requests session gets created.

        The session is what handles connection pooling and keeps our headers
        consistent across requests. If this is None, every API call will fail.
        """
        client = GitHubAPIClient()
        self.assertIsNotNone(client.session)

    def test_client_headers_set(self):
        """
        Check that required GitHub API headers are present.

        GitHub rejects requests without proper Accept and User-Agent headers.
        I learned this the hard way when I kept getting 403 errors during testing.
        This test makes sure we're always sending the headers GitHub expects.
        """
        client = GitHubAPIClient()
        headers = client.session.headers
        self.assertIn('Accept', headers)  # GitHub requires application/vnd.github.v3+json
        self.assertIn('User-Agent', headers)  # GitHub rejects requests without this