"""
Tests for code complexity analyzer.

Verifies that the ComplexityAnalyzer correctly calculates cyclomatic complexity,
function counts, and handles edge cases like syntax errors.

Run tests: python manage.py test analytics
"""
from django.test import TestCase
from analytics.complexity_analyzer import ComplexityAnalyzer


class ComplexityAnalyzerTests(TestCase):
    """
    Test suite for ComplexityAnalyzer.

    These tests verify the analyzer correctly calculates McCabe complexity
    and handles both valid code and syntax errors gracefully.
    """

    def test_simple_function(self):
        """
        Test analyzing a simple function with no branches.

        Expected complexity: 2 (1 for module + 1 for function base)
        A function with no if/while/for has complexity 1, plus the module
        base of 1, gives total of 2.
        """
        code = """
def hello():
    return "world"
"""
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze(code)

        # Module base (1) + function base (1) = 2
        self.assertEqual(result['cyclomatic_complexity'], 2)
        self.assertEqual(result['num_functions'], 1)
        self.assertEqual(result['num_classes'], 0)

    def test_complex_function(self):
        """
        Test analyzing a function with multiple branches.

        Each if/elif adds to complexity. This function has if + elif,
        so complexity should be > 3 (module + function + 2 branches).
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

        # Should have higher complexity due to branches (if + elif)
        # Exact value: 1 (module) + 1 (function) + 2 (if/elif) = 4
        self.assertGreater(result['cyclomatic_complexity'], 3)

    def test_syntax_error(self):
        """
        Test that analyzer properly raises SyntaxError for invalid code.

        Important for defensive programming - we should fail gracefully
        with clear errors rather than crash or return bogus metrics.
        """
        code = "def broken("  # Missing closing paren and body
        analyzer = ComplexityAnalyzer()

        # Should raise SyntaxError (not crash or return invalid results)
        with self.assertRaises(SyntaxError):
            analyzer.analyze(code)