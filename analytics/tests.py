from django.test import TestCase
from analytics.complexity_analyzer import ComplexityAnalyzer


class ComplexityAnalyzerTests(TestCase):
    """
    Tests for the complexity analyzer.

    I focused on testing the core calculation logic and edge cases that could
    break the analyzer. These tests helped me catch bugs during development,
    especially around how complexity is counted.
    """

    def test_simple_function(self):
        """
        Test the baseline case - a dead simple function with no complexity.

        This verifies the base complexity calculation: module gets 1, each function
        adds 1, so total should be 2. If this fails, something is fundamentally
        wrong with how we're counting. I use this as a sanity check that the
        analyzer is working at all.
        """
        code = """
def hello():
    return "world"
"""
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze(code)

        # Base complexity: 1 for the module itself + 1 for the function
        self.assertEqual(result['cyclomatic_complexity'], 2)
        self.assertEqual(result['num_functions'], 1)
        self.assertEqual(result['num_classes'], 0)

    def test_complex_function(self):
        """
        Test that branching logic increases complexity like it should.

        Each if/elif adds a decision point, which should bump up the complexity.
        I use assertGreater instead of assertEqual because I care that complexity
        increases with branches, not the exact number (which could change if I
        tweak the algorithm). This test caught a bug early on where I wasn't
        counting elif statements properly.
        """
        code = """
def complex_func(x):
    if x > 10:
        return "big"
    elif x > 5:
        return "medium"
    else:
        return "small"
"""
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze(code)

        # Should be higher than the simple case due to if/elif branches
        # Using > 3 instead of exact value since the important thing is that
        # branching increases complexity
        self.assertGreater(result['cyclomatic_complexity'], 3)

    def test_syntax_error(self):
        """
        Make sure the analyzer handles broken code gracefully.

        Users might paste incomplete or invalid Python, so the analyzer needs to
        raise a clear SyntaxError instead of crashing. This is defensive programming -
        the app should never break because of bad user input.
        """
        code = "def broken("
        analyzer = ComplexityAnalyzer()

        # Should raise SyntaxError, not crash or return garbage results
        with self.assertRaises(SyntaxError):
            analyzer.analyze(code)