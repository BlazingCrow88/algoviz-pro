"""
Code Complexity Analyzer using Python's Abstract Syntax Tree (AST).

Analyzes Python source code to calculate complexity metrics indicating code
quality and maintainability. Uses AST parsing (not regex) for semantic
understanding of code structure.

Metrics calculated:
- Cyclomatic Complexity: Independent paths through code
- Lines of Code: Total, code, comments, blank
- Function Metrics: Per-function complexity, parameters, lines
- Nesting Depth: Control structure nesting levels
- Maintainability Index: Overall quality score (0-100)

Thresholds based on software engineering research (McCabe, Miller's Law).
"""
import ast
from typing import Dict, List, Any, Union


class ComplexityAnalyzer:
    """
    Analyzes Python code complexity using AST parsing.

    Why a class: Maintains state (accumulated metrics) while walking AST.
    Cleaner than passing dict to every helper function.

    Usage: Initialize → analyze(code) → get results dict
    """

    def __init__(self):
        """Initialize with empty metrics."""
        self.metrics: Dict[str, Any] = {}
        self.reset()

    def reset(self) -> None:
        """
        Reset all metrics to initial state.

        Why needed: Analyzing multiple files in sequence requires fresh
        metrics for each to avoid accumulation.
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
        Main analysis method - returns comprehensive metrics dictionary.

        Analysis phases:
        1. Line-based analysis (counts, comments)
        2. AST parsing (syntax tree)
        3. Tree walking (gather metrics)
        4. Derived calculations (maintainability, recommendations)

        Args:
            source_code: Python code as string

        Returns:
            dict: All calculated metrics

        Raises:
            SyntaxError: Invalid Python syntax
        """
        self.reset()

        # Line-based analysis (before AST so we get counts even with syntax errors)
        self._analyze_lines(source_code)

        try:
            tree = ast.parse(source_code)
            self._analyze_ast(tree)

            # Calculate derived metrics
            self.metrics['cyclomatic_complexity'] = self._calculate_total_complexity()

            if self.metrics['num_functions'] > 0:
                self.metrics['avg_function_complexity'] = round(
                    self.metrics['cyclomatic_complexity'] / self.metrics['num_functions'],
                    2
                )
            else:
                self.metrics['avg_function_complexity'] = 0

            self.metrics['recommendations'] = self._generate_recommendations()
            self.metrics['maintainability_index'] = self._calculate_maintainability_index()

            return self.metrics

        except SyntaxError as e:
            raise SyntaxError(f"Invalid Python syntax: {str(e)}")

    def _analyze_lines(self, source_code: str) -> None:
        """
        Analyze line-based metrics.

        Categorizes each line as code, comment, or blank. Runs before AST
        parsing so line counts available even with syntax errors.

        Note: Lines with inline comments increment both code_lines and
        comment_lines, so they can sum to more than total_lines.
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
                if '#' in line:  # Inline comment
                    self.metrics['comment_lines'] += 1

    def _analyze_ast(self, tree: ast.AST) -> None:
        """
        Walk AST and collect metrics.

        Uses ast.walk() for depth-first traversal. Counts functions, classes,
        and imports while analyzing each.
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self.metrics['num_functions'] += 1
                func_metrics = self._analyze_function(node)
                self.metrics['functions'].append(func_metrics)

            elif isinstance(node, ast.ClassDef):
                self.metrics['num_classes'] += 1
                class_metrics = self._analyze_class(node)
                self.metrics['classes'].append(class_metrics)

            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                import_info = self._get_import_info(node)
                if import_info:
                    self.metrics['imports'].append(import_info)

    def _analyze_function(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """
        Analyze single function metrics.

        Measures: name, location, parameters, LOC, complexity, nesting.
        Research shows functions with >10 complexity or >4 nesting have
        significantly more bugs.
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
        """
        Analyze class definition.

        Extracts structural info: name, methods, location.
        """
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
        Calculate McCabe cyclomatic complexity.

        Measures independent paths through code. Formula: decision points + 1.

        Decision points: if, for, while, except, and/or operators, comprehensions.

        Thresholds (McCabe, 1976):
        - 1-10: Simple, easy to test
        - 11-20: Moderate complexity
        - 21+: High complexity, refactor recommended

        Research shows functions with complexity >10 have exponentially more bugs.
        """
        complexity = 1  # Base path

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # and/or operators: each operand is decision point
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.ListComp, ast.DictComp, ast.SetComp)):
                complexity += 1

        return complexity

    @staticmethod
    def _calculate_max_depth(node: ast.AST, current_depth: int = 0) -> int:
        """
        Calculate maximum nesting depth.

        Measures how deeply control structures are nested. Deep nesting
        exceeds human working memory (Miller's 7±2 rule).

        Thresholds:
        - 0-2: Easy to understand
        - 3-4: Moderate
        - 5+: Hard to follow, refactor recommended

        Implementation: Recursive depth-first traversal, incrementing depth
        at nesting constructs (if, for, while, with, try, function/class defs).
        """
        max_depth = current_depth

        nesting_nodes = (
            ast.If, ast.For, ast.While, ast.With, ast.Try,
            ast.FunctionDef, ast.ClassDef
        )

        for child in ast.iter_child_nodes(node):
            if isinstance(child, nesting_nodes):
                child_depth = ComplexityAnalyzer._calculate_max_depth(child, current_depth + 1)
            else:
                child_depth = ComplexityAnalyzer._calculate_max_depth(child, current_depth)

            max_depth = max(max_depth, child_depth)

        return max_depth

    @staticmethod
    def _count_function_lines(node: ast.FunctionDef) -> int:
        """Count lines in function using AST line numbers (Python 3.8+)."""
        if not hasattr(node, 'end_lineno') or node.end_lineno is None:
            return 1
        return node.end_lineno - node.lineno + 1

    @staticmethod
    def _get_import_info(node: Union[ast.Import, ast.ImportFrom]) -> Dict[str, Any]:
        """
        Extract import information.

        Tracks dependencies - useful for spotting excessive imports.
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
        Sum cyclomatic complexity across all functions.

        Total = 1 (module base) + sum of function complexities.
        """
        total = 1
        for func in self.metrics['functions']:
            total += func['complexity']
        return total

    def _calculate_maintainability_index(self) -> float:
        """
        Calculate maintainability index (0-100, higher = better).

        Simplified formula: MI = 100 - (complexity_per_line * 100)

        Thresholds:
        - 76-100: Highly maintainable
        - 51-75: Moderate
        - 26-50: Low maintainability
        - 0-25: Unmaintainable

        Note: Using simplified version. Full Microsoft/SEI formula includes
        Halstead Volume which requires extensive operator/operand counting.
        Our version captures key concept: complexity relative to size.
        """
        loc = max(self.metrics['code_lines'], 1)
        cc = self.metrics['cyclomatic_complexity']

        complexity_ratio = cc / loc
        mi = 100 - (complexity_ratio * 100)
        mi = max(0, min(100, mi))

        return round(mi, 2)

    def _generate_recommendations(self) -> List[str]:
        """
        Generate actionable recommendations based on metrics.

        Thresholds based on industry research:
        - Overall complexity >50: Too high
        - Function complexity >10: Refactor needed (McCabe threshold)
        - Nesting depth >4: Exceeds working memory
        - Function length >50 lines: Violates Single Responsibility
        """
        recommendations = []

        if self.metrics['cyclomatic_complexity'] > 50:
            recommendations.append(
                "⚠️ High overall complexity. Consider breaking down into smaller functions."
            )

        complex_functions = [f for f in self.metrics['functions'] if f['complexity'] > 10]
        if complex_functions:
            func_names = ', '.join(f['name'] for f in complex_functions[:3])
            recommendations.append(
                f"⚠️ {len(complex_functions)} function(s) have high complexity (>10). "
                f"Consider refactoring: {func_names}"
            )

        if self.metrics['max_nesting_depth'] > 4:
            recommendations.append(
                f"⚠️ Maximum nesting depth is {self.metrics['max_nesting_depth']}. "
                "Consider extracting nested logic into separate functions."
            )

        long_functions = [f for f in self.metrics['functions'] if f['num_lines'] > 50]
        if long_functions:
            recommendations.append(
                f"⚠️ {len(long_functions)} function(s) are long (>50 lines). "
                "Consider breaking them down."
            )

        if self.metrics['code_lines'] > 100 and self.metrics['num_functions'] < 3:
            recommendations.append(
                "💡 Code could benefit from more modularization. "
                "Consider extracting repeated logic into functions."
            )

        if not recommendations:
            recommendations.append(
                "✅ Code shows good structure and maintainability!"
            )

        return recommendations

    def generate_report(self) -> str:
        """
        Generate human-readable text report.

        Formats all metrics for console/text display. Alternative to raw
        metrics dict for comprehensive overview.
        """
        if not self.metrics:
            return "No analysis performed yet."

        report = []
        report.append("=" * 60)
        report.append("CODE COMPLEXITY ANALYSIS REPORT")
        report.append("=" * 60)
        report.append("")

        report.append("OVERALL METRICS:")
        report.append(f"  Total Lines: {self.metrics['total_lines']}")
        report.append(f"  Code Lines: {self.metrics['code_lines']}")
        report.append(f"  Comment Lines: {self.metrics['comment_lines']}")
        report.append(f"  Blank Lines: {self.metrics['blank_lines']}")
        report.append(f"  Cyclomatic Complexity: {self.metrics['cyclomatic_complexity']}")
        report.append(f"  Maintainability Index: {self.metrics['maintainability_index']}/100")
        report.append("")

        report.append("CODE STRUCTURE:")
        report.append(f"  Functions: {self.metrics['num_functions']}")
        report.append(f"  Classes: {self.metrics['num_classes']}")
        report.append(f"  Max Nesting Depth: {self.metrics['max_nesting_depth']}")
        report.append("")

        if self.metrics['functions']:
            report.append("FUNCTION DETAILS:")
            for func in self.metrics['functions']:
                report.append(f"  {func['name']}:")
                report.append(f"    Lines: {func['num_lines']}")
                report.append(f"    Parameters: {func['num_params']}")
                report.append(f"    Complexity: {func['complexity']}")
                report.append(f"    Max Depth: {func['max_depth']}")
            report.append("")

        report.append("RECOMMENDATIONS:")
        for rec in self.metrics['recommendations']:
            report.append(f"  {rec}")
        report.append("")

        report.append("=" * 60)

        return "\n".join(report)