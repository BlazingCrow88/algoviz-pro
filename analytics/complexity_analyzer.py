"""
Code Complexity Analyzer using Python's AST module.

This module analyzes Python source code to calculate various complexity metrics
including cyclomatic complexity, function metrics, and code quality indicators.
"""
import ast
from typing import Dict, List, Any, Union


class ComplexityAnalyzer:
    """
    Analyzes Python code complexity using Abstract Syntax Tree (AST).

    Calculates:
    - Cyclomatic Complexity (McCabe)
    - Lines of Code (LOC)
    - Number of functions/classes
    - Maximum nesting depth
    - Function-specific metrics

    Example:
        >>> analyzer = ComplexityAnalyzer()
        >>> code = "def hello(): return 'world'"
        >>> results = analyzer.analyze(code)
        >>> print(results['cyclomatic_complexity'])
    """

    def __init__(self):
        """Initialize the analyzer."""
        self.metrics: Dict[str, Any] = {}
        self.reset()

    def reset(self) -> None:
        """Reset all metrics to initial state."""
        self.metrics = {
            'cyclomatic_complexity': 0,
            'total_lines': 0,
            'code_lines': 0,
            'comment_lines': 0,
            'blank_lines': 0,
            'num_functions': 0,
            'num_classes': 0,
            'max_nesting_depth': 0,
            'functions': [],
            'classes': [],
            'imports': [],
        }

    def analyze(self, source_code: str) -> Dict[str, Any]:
        """
        Analyze Python source code and return complexity metrics.

        Args:
            source_code: Python source code as string

        Returns:
            dict: Dictionary containing all calculated metrics

        Raises:
            SyntaxError: If source code has syntax errors

        Example:
            >>> analyzer = ComplexityAnalyzer()
            >>> code = '''
            ... def fibonacci(n):
            ...     if n <= 1:
            ...         return n
            ...     return fibonacci(n-1) + fibonacci(n-2)
            ... '''
            >>> results = analyzer.analyze(code)
            >>> print(f"Complexity: {results['cyclomatic_complexity']}")
        """
        self.reset()

        # Analyze lines
        self._analyze_lines(source_code)

        try:
            # Parse AST
            tree = ast.parse(source_code)

            # Analyze AST
            self._analyze_ast(tree)

            # Calculate overall cyclomatic complexity
            self.metrics['cyclomatic_complexity'] = self._calculate_total_complexity()

            # Calculate average complexity per function
            if self.metrics['num_functions'] > 0:
                self.metrics['avg_function_complexity'] = round(
                    self.metrics['cyclomatic_complexity'] / self.metrics['num_functions'],
                    2
                )
            else:
                self.metrics['avg_function_complexity'] = 0

            # Generate recommendations
            self.metrics['recommendations'] = self._generate_recommendations()

            # Calculate maintainability index
            self.metrics['maintainability_index'] = self._calculate_maintainability_index()

            return self.metrics

        except SyntaxError as e:
            raise SyntaxError(f"Invalid Python syntax: {str(e)}")

    def _analyze_lines(self, source_code: str) -> None:
        """Analyze line-based metrics."""
        lines = source_code.split('\n')
        self.metrics['total_lines'] = len(lines)

        for line in lines:
            stripped = line.strip()

            if not stripped:
                self.metrics['blank_lines'] += 1
            elif stripped.startswith('#'):
                self.metrics['comment_lines'] += 1
            else:
                self.metrics['code_lines'] += 1
                # Check for inline comments
                if '#' in line:
                    self.metrics['comment_lines'] += 1

    def _analyze_ast(self, tree: ast.AST) -> None:
        """Analyze the Abstract Syntax Tree."""
        for node in ast.walk(tree):
            # Count functions
            if isinstance(node, ast.FunctionDef):
                self.metrics['num_functions'] += 1
                func_metrics = self._analyze_function(node)
                self.metrics['functions'].append(func_metrics)

            # Count classes
            elif isinstance(node, ast.ClassDef):
                self.metrics['num_classes'] += 1
                class_metrics = self._analyze_class(node)
                self.metrics['classes'].append(class_metrics)

            # Count imports
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                import_info = self._get_import_info(node)
                if import_info:
                    self.metrics['imports'].append(import_info)

    def _analyze_function(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """
        Analyze a function definition.

        Returns metrics specific to this function:
        - Name
        - Number of parameters
        - Lines of code
        - Cyclomatic complexity
        - Nesting depth
        """
        func_info = {
            'name': node.name,
            'line_number': node.lineno,
            'num_params': len(node.args.args),
            'num_lines': self._count_function_lines(node),
            'complexity': self._calculate_cyclomatic_complexity(node),
            'max_depth': self._calculate_max_depth(node),
        }

        # Update global max nesting depth
        if func_info['max_depth'] > self.metrics['max_nesting_depth']:
            self.metrics['max_nesting_depth'] = func_info['max_depth']

        return func_info

    @staticmethod
    def _analyze_class(node: ast.ClassDef) -> Dict[str, Any]:
        """Analyze a class definition."""
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        method_names = [m.name for m in methods]

        return {
            'name': node.name,
            'line_number': node.lineno,
            'num_methods': len(methods),
            'method_names': method_names,
        }

    @staticmethod
    def _calculate_cyclomatic_complexity(node: ast.AST) -> int:
        """
        Calculate McCabe cyclomatic complexity for a node.

        Cyclomatic complexity = Number of decision points + 1

        Decision points include:
        - if statements
        - for/while loops
        - except clauses
        - boolean operators (and, or)
        - comprehensions
        """
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            # Decision points
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1

            # Exception handlers
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1

            # Boolean operators in conditions
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

            # Comprehensions
            elif isinstance(child, (ast.ListComp, ast.DictComp, ast.SetComp)):
                complexity += 1

        return complexity

    @staticmethod
    def _calculate_max_depth(node: ast.AST, current_depth: int = 0) -> int:
        """
        Calculate maximum nesting depth.

        Depth increases for:
        - Function definitions
        - Class definitions
        - Control structures (if, for, while, with, try)
        """
        max_depth = current_depth

        nesting_nodes = (ast.If, ast.For, ast.While, ast.With,
                        ast.Try, ast.FunctionDef, ast.ClassDef)

        for child in ast.iter_child_nodes(node):
            # Increase depth for nesting structures
            if isinstance(child, nesting_nodes):
                child_depth = ComplexityAnalyzer._calculate_max_depth(child, current_depth + 1)
            else:
                child_depth = ComplexityAnalyzer._calculate_max_depth(child, current_depth)

            max_depth = max(max_depth, child_depth)

        return max_depth

    @staticmethod
    def _count_function_lines(node: ast.FunctionDef) -> int:
        """Count lines of code in a function."""
        if not hasattr(node, 'end_lineno') or node.end_lineno is None:
            return 1
        return node.end_lineno - node.lineno + 1

    @staticmethod
    def _get_import_info(node: Union[ast.Import, ast.ImportFrom]) -> Dict[str, Any]:
        """Extract import information."""
        if isinstance(node, ast.Import):
            return {
                'type': 'import',
                'modules': [alias.name for alias in node.names]
            }
        elif isinstance(node, ast.ImportFrom):
            return {
                'type': 'from_import',
                'module': node.module or '',
                'names': [alias.name for alias in node.names]
            }
        return {}

    def _calculate_total_complexity(self) -> int:
        """Calculate total cyclomatic complexity across all functions."""
        total = 1  # Base complexity for module
        for func in self.metrics['functions']:
            total += func['complexity']
        return total

    def _calculate_maintainability_index(self) -> float:
        """
        Calculate maintainability index (simplified version).

        MI = 171 - 5.2 * ln(HV) - 0.23 * CC - 16.2 * ln(LOC)

        Where:
        - HV = Halstead Volume (simplified: use LOC as proxy)
        - CC = Cyclomatic Complexity
        - LOC = Lines of Code

        Simplified version: Based on complexity and LOC ratio
        """
        loc = max(self.metrics['code_lines'], 1)
        cc = self.metrics['cyclomatic_complexity']

        # Simplified MI: 100 - (complexity_per_line * 20)
        complexity_ratio = cc / loc
        mi = max(0, min(100, 100 - (complexity_ratio * 100)))

        return round(mi, 2)

    def _generate_recommendations(self) -> List[str]:
        """Generate code quality recommendations based on metrics."""
        recommendations = []

        # Check cyclomatic complexity
        if self.metrics['cyclomatic_complexity'] > 50:
            recommendations.append(
                "⚠️ High overall complexity. Consider breaking down into smaller functions."
            )

        # Check individual function complexity
        complex_functions = [f for f in self.metrics['functions'] if f['complexity'] > 10]
        if complex_functions:
            func_names = ', '.join(f['name'] for f in complex_functions[:3])
            recommendations.append(
                f"⚠️ {len(complex_functions)} function(s) have high complexity (>10). "
                f"Consider refactoring: {func_names}"
            )

        # Check nesting depth
        if self.metrics['max_nesting_depth'] > 4:
            recommendations.append(
                f"⚠️ Maximum nesting depth is {self.metrics['max_nesting_depth']}. "
                "Consider extracting nested logic into separate functions."
            )

        # Check long functions
        long_functions = [f for f in self.metrics['functions'] if f['num_lines'] > 50]
        if long_functions:
            recommendations.append(
                f"⚠️ {len(long_functions)} function(s) are long (>50 lines). "
                "Consider breaking them down."
            )

        # Check for lack of functions
        if self.metrics['code_lines'] > 100 and self.metrics['num_functions'] < 3:
            recommendations.append(
                "💡 Code could benefit from more modularization. "
                "Consider extracting repeated logic into functions."
            )

        # Positive feedback
        if not recommendations:
            recommendations.append(
                "✅ Code shows good structure and maintainability!"
            )

        return recommendations

    def generate_report(self) -> str:
        """
        Generate a human-readable report of the analysis.

        Returns:
            str: Formatted text report
        """
        if not self.metrics:
            return "No analysis performed yet."

        report = ["=" * 60, "CODE COMPLEXITY ANALYSIS REPORT", "=" * 60, "", "OVERALL METRICS:",
                  f"  Total Lines: {self.metrics['total_lines']}", f"  Code Lines: {self.metrics['code_lines']}",
                  f"  Comment Lines: {self.metrics['comment_lines']}", f"  Blank Lines: {self.metrics['blank_lines']}",
                  f"  Cyclomatic Complexity: {self.metrics['cyclomatic_complexity']}",
                  f"  Maintainability Index: {self.metrics['maintainability_index']}/100", "", "CODE STRUCTURE:",
                  f"  Functions: {self.metrics['num_functions']}", f"  Classes: {self.metrics['num_classes']}",
                  f"  Max Nesting Depth: {self.metrics['max_nesting_depth']}", ""]

        # Overall metrics

        # Structure

        # Functions
        if self.metrics['functions']:
            report.append("FUNCTION DETAILS:")
            for func in self.metrics['functions']:
                report.append(f"  {func['name']}:")
                report.append(f"    Lines: {func['num_lines']}")
                report.append(f"    Parameters: {func['num_params']}")
                report.append(f"    Complexity: {func['complexity']}")
                report.append(f"    Max Depth: {func['max_depth']}")
            report.append("")

        # Recommendations
        report.append("RECOMMENDATIONS:")
        for rec in self.metrics['recommendations']:
            report.append(f"  {rec}")
        report.append("")

        report.append("=" * 60)

        return "\n".join(report)