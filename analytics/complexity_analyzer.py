"""
Code Complexity Analyzer using Python's AST module.

This is the core of the analytics app - it takes Python code and calculates
complexity metrics to help identify potential problem areas. I used AST (Abstract
Syntax Tree) because it lets me analyze code structure without actually executing it,
which is way safer and more reliable than trying to parse code with regex.
"""
import ast
from typing import Dict, List, Any, Union


class ComplexityAnalyzer:
    """
    Analyzes Python code complexity using Abstract Syntax Tree (AST).

    I built this to calculate the main metrics professors and code reviewers care about:
    cyclomatic complexity (how many decision paths exist), lines of code, nesting depth,
    and function-specific stats. The goal is to catch overly complex code before it
    becomes unmaintainable.

    Example:
        >>> analyzer = ComplexityAnalyzer()
        >>> code = "def hello(): return 'world'"
        >>> results = analyzer.analyze(code)
        >>> print(results['cyclomatic_complexity'])
    """

    def __init__(self):
        """Set up a fresh analyzer with empty metrics."""
        self.metrics: Dict[str, Any] = {}
        self.reset()

    def reset(self) -> None:
        """
        Clear out all metrics back to zero.
        I call this at the start of each analysis so old results don't pollute new ones.
        """
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
        Main analysis entry point - this orchestrates all the complexity calculations.

        I split this into multiple helper methods (_analyze_lines, _analyze_ast, etc.)
        to keep things organized and testable. The flow is: reset metrics, analyze lines,
        parse AST, calculate complexity, then generate recommendations.

        Args:
            source_code: Python source code as string

        Returns:
            dict: Dictionary containing all calculated metrics

        Raises:
            SyntaxError: If source code has syntax errors (can't analyze broken code)
        """
        self.reset()

        # Count lines first since it doesn't require valid syntax
        self._analyze_lines(source_code)

        try:
            # Parse into AST - this is where syntax errors would show up
            tree = ast.parse(source_code)

            # Walk through the tree and collect metrics
            self._analyze_ast(tree)

            # Sum up complexity from all functions
            self.metrics['cyclomatic_complexity'] = self._calculate_total_complexity()

            # Calculate average to show if complexity is spread out or concentrated
            if self.metrics['num_functions'] > 0:
                self.metrics['avg_function_complexity'] = round(
                    self.metrics['cyclomatic_complexity'] / self.metrics['num_functions'],
                    2
                )
            else:
                self.metrics['avg_function_complexity'] = 0

            # Generate helpful suggestions based on what we found
            self.metrics['recommendations'] = self._generate_recommendations()

            # Overall quality score - higher is better
            self.metrics['maintainability_index'] = self._calculate_maintainability_index()

            return self.metrics

        except SyntaxError as e:
            # Re-raise with a clearer message for the user
            raise SyntaxError(f"Invalid Python syntax: {str(e)}")

    def _analyze_lines(self, source_code: str) -> None:
        """
        Count different types of lines (code, comments, blank).
        This gives a basic size metric before we dive into the AST.
        """
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
                # Also count inline comments since they're still documentation
                if '#' in line:
                    self.metrics['comment_lines'] += 1

    def _analyze_ast(self, tree: ast.AST) -> None:
        """
        Walk through the entire AST and collect structural information.
        ast.walk() is perfect here because it hits every node without me having
        to manually traverse the tree recursively.
        """
        for node in ast.walk(tree):
            # Track function definitions and analyze each one individually
            if isinstance(node, ast.FunctionDef):
                self.metrics['num_functions'] += 1
                func_metrics = self._analyze_function(node)
                self.metrics['functions'].append(func_metrics)

            # Track class definitions
            elif isinstance(node, ast.ClassDef):
                self.metrics['num_classes'] += 1
                class_metrics = self._analyze_class(node)
                self.metrics['classes'].append(class_metrics)

            # Track imports to show dependencies
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                import_info = self._get_import_info(node)
                if import_info:
                    self.metrics['imports'].append(import_info)

    def _analyze_function(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """
        Dig into individual functions to get detailed metrics.

        This is where the really useful stuff happens - finding which specific functions
        are too complex. I track complexity, length, params, and nesting because those
        are the main indicators of hard-to-maintain code.
        """
        func_info = {
            'name': node.name,
            'line_number': node.lineno,
            'num_params': len(node.args.args),
            'num_lines': self._count_function_lines(node),
            'complexity': self._calculate_cyclomatic_complexity(node),
            'max_depth': self._calculate_max_depth(node),
        }

        # Keep track of the worst nesting we've seen across all functions
        if func_info['max_depth'] > self.metrics['max_nesting_depth']:
            self.metrics['max_nesting_depth'] = func_info['max_depth']

        return func_info

    @staticmethod
    def _analyze_class(node: ast.ClassDef) -> Dict[str, Any]:
        """Pull out basic class info - mainly just counting methods for now."""
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
        Calculate McCabe cyclomatic complexity - basically counting decision points.

        The formula is: number of decision points + 1
        More decisions = more test cases needed = harder to understand.

        I count if/while/for as +1 each, boolean operators (and/or) add complexity,
        and exception handlers too since they're alternate code paths.
        """
        complexity = 1  # Start at 1 (the straight-through path)

        for child in ast.walk(node):
            # Each control structure adds a decision point
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1

            # Exception handlers are alternate paths
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1

            # Boolean operators create multiple paths (if x and y and z = 3 paths)
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

            # Comprehensions are compact but still add complexity
            elif isinstance(child, (ast.ListComp, ast.DictComp, ast.SetComp)):
                complexity += 1

        return complexity

    @staticmethod
    def _calculate_max_depth(node: ast.AST, current_depth: int = 0) -> int:
        """
        Find the deepest level of nesting in the code.

        This is recursive because nesting is naturally a tree structure.
        Each time we hit an if/for/while/etc, we go one level deeper.
        Deeply nested code is hard to read, so this metric flags potential issues.
        """
        max_depth = current_depth

        nesting_nodes = (ast.If, ast.For, ast.While, ast.With,
                        ast.Try, ast.FunctionDef, ast.ClassDef)

        for child in ast.iter_child_nodes(node):
            # Recurse deeper when we hit nesting structures
            if isinstance(child, nesting_nodes):
                child_depth = ComplexityAnalyzer._calculate_max_depth(child, current_depth + 1)
            else:
                child_depth = ComplexityAnalyzer._calculate_max_depth(child, current_depth)

            max_depth = max(max_depth, child_depth)

        return max_depth

    @staticmethod
    def _count_function_lines(node: ast.FunctionDef) -> int:
        """
        Count how many lines a function spans.
        Newer Python versions give us end_lineno, older ones don't - so we handle both.
        """
        if not hasattr(node, 'end_lineno') or node.end_lineno is None:
            return 1
        return node.end_lineno - node.lineno + 1

    @staticmethod
    def _get_import_info(node: Union[ast.Import, ast.ImportFrom]) -> Dict[str, Any]:
        """
        Extract what modules/packages are being imported.
        I distinguish between 'import x' and 'from x import y' since they're different.
        """
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
        """
        Add up complexity from all functions plus the module-level code.
        Starting at 1 accounts for the main execution path of the module.
        """
        total = 1  # Base complexity for module
        for func in self.metrics['functions']:
            total += func['complexity']
        return total

    def _calculate_maintainability_index(self) -> float:
        """
        Generate an overall quality score from 0-100 (higher is better).

        The real MI formula uses Halstead volume and is pretty complex, so I simplified it
        to just ratio of complexity to lines of code. If you have high complexity in few
        lines, that's hard to maintain, so the score drops.
        """
        loc = max(self.metrics['code_lines'], 1)  # Avoid division by zero
        cc = self.metrics['cyclomatic_complexity']

        # Higher complexity per line = lower maintainability
        complexity_ratio = cc / loc
        mi = max(0, min(100, 100 - (complexity_ratio * 100)))

        return round(mi, 2)

    def _generate_recommendations(self) -> List[str]:
        """
        Look at the metrics and suggest improvements.

        I use thresholds based on common best practices: complexity >10 per function
        is considered high, >50 overall is concerning, nesting >4 gets hard to follow,
        and functions >50 lines usually try to do too much.
        """
        recommendations = []

        # Check overall complexity
        if self.metrics['cyclomatic_complexity'] > 50:
            recommendations.append(
                "⚠️ High overall complexity. Consider breaking down into smaller functions."
            )

        # Flag individual problem functions
        complex_functions = [f for f in self.metrics['functions'] if f['complexity'] > 10]
        if complex_functions:
            func_names = ', '.join(f['name'] for f in complex_functions[:3])
            recommendations.append(
                f"⚠️ {len(complex_functions)} function(s) have high complexity (>10). "
                f"Consider refactoring: {func_names}"
            )

        # Check for deep nesting
        if self.metrics['max_nesting_depth'] > 4:
            recommendations.append(
                f"⚠️ Maximum nesting depth is {self.metrics['max_nesting_depth']}. "
                "Consider extracting nested logic into separate functions."
            )

        # Check for long functions
        long_functions = [f for f in self.metrics['functions'] if f['num_lines'] > 50]
        if long_functions:
            recommendations.append(
                f"⚠️ {len(long_functions)} function(s) are long (>50 lines). "
                "Consider breaking them down."
            )

        # Suggest more modularization if it's mostly flat code
        if self.metrics['code_lines'] > 100 and self.metrics['num_functions'] < 3:
            recommendations.append(
                "💡 Code could benefit from more modularization. "
                "Consider extracting repeated logic into functions."
            )

        # Give positive feedback when things look good
        if not recommendations:
            recommendations.append(
                "✅ Code shows good structure and maintainability!"
            )

        return recommendations

    def generate_report(self) -> str:
        """
        Format all the metrics into a readable text report.
        This gets displayed in the web interface so users can understand the analysis.
        """
        if not self.metrics:
            return "No analysis performed yet."

        # Build the report section by section for clarity
        report = [
            "=" * 60,
            "CODE COMPLEXITY ANALYSIS REPORT",
            "=" * 60,
            "",
            "OVERALL METRICS:",
            f"  Total Lines: {self.metrics['total_lines']}",
            f"  Code Lines: {self.metrics['code_lines']}",
            f"  Comment Lines: {self.metrics['comment_lines']}",
            f"  Blank Lines: {self.metrics['blank_lines']}",
            f"  Cyclomatic Complexity: {self.metrics['cyclomatic_complexity']}",
            f"  Maintainability Index: {self.metrics['maintainability_index']}/100",
            "",
            "CODE STRUCTURE:",
            f"  Functions: {self.metrics['num_functions']}",
            f"  Classes: {self.metrics['num_classes']}",
            f"  Max Nesting Depth: {self.metrics['max_nesting_depth']}",
            ""
        ]

        # Show details for each function if there are any
        if self.metrics['functions']:
            report.append("FUNCTION DETAILS:")
            for func in self.metrics['functions']:
                report.append(f"  {func['name']}:")
                report.append(f"    Lines: {func['num_lines']}")
                report.append(f"    Parameters: {func['num_params']}")
                report.append(f"    Complexity: {func['complexity']}")
                report.append(f"    Max Depth: {func['max_depth']}")
            report.append("")

        # Add our generated recommendations at the end
        report.append("RECOMMENDATIONS:")
        for rec in self.metrics['recommendations']:
            report.append(f"  {rec}")
        report.append("")

        report.append("=" * 60)

        return "\n".join(report)