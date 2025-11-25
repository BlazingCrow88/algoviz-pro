from django.test import TestCase
from .complexity_analyzer import ComplexityAnalyzer


class ComplexityAnalyzerTests(TestCase):
    """Test code complexity analysis."""

    def test_simple_function(self):
        """Test analyzing a simple function."""
        code = """
def hello():
    return "world"
"""
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze(code)

        self.assertEqual(result['cyclomatic_complexity'], 2)  # 1 for module + 1 for function
        self.assertEqual(result['num_functions'], 1)
        self.assertEqual(result['num_classes'], 0)

    def test_complex_function(self):
        """Test analyzing complex function with branches."""
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

        # Should have higher complexity due to branches
        self.assertGreater(result['cyclomatic_complexity'], 3)

    def test_syntax_error(self):
        """Test handling syntax errors."""
        code = "def broken("
        analyzer = ComplexityAnalyzer()

        with self.assertRaises(SyntaxError):
            analyzer.analyze(code)