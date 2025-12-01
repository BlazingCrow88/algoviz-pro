"""
Code Complexity Analyzer using Python's Abstract Syntax Tree (AST) module.

What this does: Analyzes Python source code to calculate complexity metrics
that indicate code quality and maintainability. Think of it as an automated
code reviewer that spots overly complex functions.

Why AST instead of regex: We parse the code into a tree structure rather than
using string matching. AST gives us semantic understanding - we can tell the
difference between a function definition and a function call, between a comment
and a string that happens to contain '#', etc. Regex would be fragile and miss
tons of edge cases.

How AST works: Python's ast module parses source code into a tree where each
node represents a construct (function, if statement, loop, etc.). We walk this
tree and count decision points, nesting levels, etc.

Example AST for "if x > 5: return True":
Module
  └── If
      ├── test: Compare (x > 5)
      └── body: Return (True)

The metrics we calculate:
- Cyclomatic Complexity: How many independent paths through the code
- Lines of Code: Total, code, comments, blank
- Function Metrics: Complexity per function, parameter counts, line counts
- Nesting Depth: How deeply nested control structures are
- Maintainability Index: Overall code quality score (0-100)

Why these metrics matter: Research shows that functions with complexity > 10
have exponentially more bugs. Deep nesting (>4 levels) is hard to understand.
Long functions (>50 lines) should be split up. These aren't arbitrary rules -
they're based on decades of software engineering research.

Real-world use: Tools like SonarQube, Code Climate, and PyLint use similar
metrics to flag problematic code in production systems. We're building a
simplified version for educational purposes.

Implementation challenge: The AST module was new to me - took a while to
understand how to walk the tree and distinguish different node types. The
recursive depth calculation was particularly tricky to get right.
"""
import ast
from typing import Dict, List, Any, Union


class ComplexityAnalyzer:
    """
    Analyzes Python code complexity using Abstract Syntax Tree parsing.

    This is the core of our analytics app - it takes raw Python source code
    and returns detailed metrics about its complexity and quality.

    Why a class instead of functions: We need to maintain state (accumulated
    metrics) as we walk the AST. A class with instance variables is cleaner
    than passing a dict around to every helper function.

    Design pattern: Initialize → reset() → analyze() → get metrics
    The reset() method is important because we might analyze multiple files
    in sequence and need fresh metrics for each one.

    Usage example:
        analyzer = ComplexityAnalyzer()
        code = open('script.py').read()
        results = analyzer.analyze(code)
        print(f"Complexity: {results['cyclomatic_complexity']}")
        print(f"Maintainability: {results['maintainability_index']}/100")
    """

    def __init__(self):
        """
        Initialize the analyzer with empty metrics.

        We start with a clean slate - all counters at zero, empty lists.
        The actual analysis happens in analyze() method.
        """
        self.metrics: Dict[str, Any] = {}
        self.reset()  # Set up initial empty metrics

    def reset(self) -> None:
        """
        Reset all metrics to initial state.

        Why we need this: If we analyze multiple files in sequence, we need
        fresh metrics for each one. Without reset(), metrics would accumulate
        across files which would give wrong results.

        Called by: __init__() and analyze() to ensure clean state
        """
        self.metrics = {
            'cyclomatic_complexity': 0,  # Total complexity (McCabe metric)
            'total_lines': 0,  # Every line including blank and comments
            'code_lines': 0,  # Just actual code
            'comment_lines': 0,  # Lines starting with # (or inline comments)
            'blank_lines': 0,  # Empty lines
            'num_functions': 0,  # Count of function definitions
            'num_classes': 0,  # Count of class definitions
            'max_nesting_depth': 0,  # Deepest nesting level found
            'functions': [],  # List of dicts with per-function metrics
            'classes': [],  # List of dicts with per-class info
            'imports': [],  # What modules are imported
        }

    def analyze(self, source_code: str) -> Dict[str, Any]:
        """
        Main analysis method - this is what callers use.

        Takes raw Python source code as a string and returns a comprehensive
        dictionary of metrics. This is the public API of the class.

        The analysis happens in several phases:
        1. Line-based analysis (count lines, comments, etc.)
        2. AST parsing (convert code to syntax tree)
        3. Tree walking (visit every node, gather metrics)
        4. Derived calculations (maintainability index, recommendations)

        Args:
            source_code: Python code as a string (what you'd read from a file)

        Returns:
            dict: All calculated metrics ready for display or further processing

        Raises:
            SyntaxError: If source code has invalid Python syntax
                        (missing colons, mismatched parens, etc.)

        Error handling strategy: Let SyntaxError bubble up with helpful message.
        The view layer will catch it and show user-friendly error to the user.
        Better to fail fast with clear error than return bogus metrics.

        Example usage:
            try:
                results = analyzer.analyze(user_code)
                print(f"Your code has complexity: {results['cyclomatic_complexity']}")
            except SyntaxError as e:
                print(f"Sorry, your code has a syntax error: {e}")
        """
        self.reset()  # Start fresh - don't carry over metrics from previous analysis

        # PHASE 1: Line-based analysis
        # This is simple string processing - count lines, identify comments
        # We do this BEFORE AST parsing because we want line counts even if
        # the code has syntax errors (AST parsing would fail)
        self._analyze_lines(source_code)

        try:
            # PHASE 2: Parse source code into Abstract Syntax Tree
            # This is where Python's parser checks syntax and builds the tree
            # If code has syntax errors, this line throws SyntaxError
            tree = ast.parse(source_code)

            # PHASE 3: Walk the AST and collect metrics
            # Visit every node in the tree (functions, classes, loops, etc.)
            # and accumulate counts
            self._analyze_ast(tree)

            # PHASE 4: Calculate derived metrics

            # Sum up complexity from all functions
            self.metrics['cyclomatic_complexity'] = self._calculate_total_complexity()

            # Average complexity per function (0 if no functions)
            if self.metrics['num_functions'] > 0:
                self.metrics['avg_function_complexity'] = round(
                    self.metrics['cyclomatic_complexity'] / self.metrics['num_functions'],
                    2
                )
            else:
                self.metrics['avg_function_complexity'] = 0

            # Generate human-readable recommendations
            # Things like "function X is too complex" or "code looks good!"
            self.metrics['recommendations'] = self._generate_recommendations()

            # Calculate maintainability index (0-100 scale, higher = better)
            self.metrics['maintainability_index'] = self._calculate_maintainability_index()

            return self.metrics

        except SyntaxError as e:
            # Wrap Python's SyntaxError with more helpful message
            # Original message might be cryptic like "invalid syntax"
            # We add context to help user understand what went wrong
            raise SyntaxError(f"Invalid Python syntax: {str(e)}")

    def _analyze_lines(self, source_code: str) -> None:
        """
        Analyze line-based metrics (LOC counts).

        This is simple string processing - no AST needed. We categorize each
        line as code, comment, or blank. This runs before AST parsing so we
        get line counts even if the code has syntax errors.

        Line classification rules:
        - Blank: Empty or only whitespace
        - Comment: Starts with # after stripping whitespace
        - Code: Everything else (including lines with inline comments)

        Edge cases handled:
        - Inline comments: "x = 5  # set x" counts as both code AND comment
        - Multiline strings: Counted as code (AST would see them as strings)
        - Empty file: All counts are 0 (no crash)

        Implementation note: We split by '\n' which works for Unix/Mac.
        Windows files use '\r\n' but Python's string operations handle that
        automatically. If we needed to be extra careful, we'd use splitlines().
        """
        lines = source_code.split('\n')
        self.metrics['total_lines'] = len(lines)

        for line in lines:
            # Remove leading/trailing whitespace to check what's actually there
            stripped = line.strip()

            if not stripped:
                # Empty line (just whitespace or truly empty)
                self.metrics['blank_lines'] += 1
            elif stripped.startswith('#'):
                # Line starts with # (after whitespace) = pure comment line
                self.metrics['comment_lines'] += 1
            else:
                # Has actual code on it
                self.metrics['code_lines'] += 1

                # Check for inline comments: "x = 5  # explanation"
                # This line counts as BOTH code and comment
                if '#' in line:
                    self.metrics['comment_lines'] += 1

        # Note: A line like "x = 5  # comment" increments both code_lines and
        # comment_lines, so they can sum to more than total_lines. That's intentional.

    def _analyze_ast(self, tree: ast.AST) -> None:
        """
        Walk the Abstract Syntax Tree and collect metrics.

        This is where the magic happens - we visit every node in the tree
        (functions, classes, imports, etc.) and gather statistics about them.

        Why ast.walk(): It's a generator that visits every node in the tree
        in no particular order (depth-first traversal). We don't care about
        order - we just want to count things and analyze functions/classes.

        Alternative: ast.NodeVisitor pattern (define visit_FunctionDef, etc.)
        but ast.walk() is simpler for our use case since we're just counting.

        What we're looking for:
        - FunctionDef nodes: Analyze each function's complexity
        - ClassDef nodes: Count classes and their methods
        - Import/ImportFrom nodes: Track dependencies

        We ignore other nodes (expressions, assignments, etc.) because we only
        care about high-level structure for our metrics.
        """
        # Walk visits every node in the tree exactly once
        for node in ast.walk(tree):

            # Check what type of node this is
            # Using isinstance instead of type() to handle subclasses

            if isinstance(node, ast.FunctionDef):
                # Found a function definition
                self.metrics['num_functions'] += 1

                # Analyze this specific function (complexity, lines, etc.)
                func_metrics = self._analyze_function(node)

                # Add to our list of function metrics
                self.metrics['functions'].append(func_metrics)

            elif isinstance(node, ast.ClassDef):
                # Found a class definition
                self.metrics['num_classes'] += 1

                # Analyze this specific class (methods, etc.)
                class_metrics = self._analyze_class(node)

                # Add to our list of class info
                self.metrics['classes'].append(class_metrics)

            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                # Found an import statement (import X or from X import Y)
                import_info = self._get_import_info(node)
                if import_info:  # Only add if we got valid info
                    self.metrics['imports'].append(import_info)

    def _analyze_function(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """
        Analyze a single function and return its metrics.

        This calculates complexity, line count, and nesting depth for one
        specific function. Called by _analyze_ast() for each function found.

        What we measure for each function:
        - Name: So we can identify it in reports ("refactor function X")
        - Line number: Where it starts in the file
        - Parameter count: More params = more complex (usually)
        - Lines of code: Long functions (>50 lines) should be split
        - Cyclomatic complexity: Independent paths through function
        - Max nesting depth: How deeply nested the control flow is

        Why these metrics: Research shows that complex functions have more bugs.
        Functions with >10 complexity or >4 nesting depth are hard to test and
        maintain. We flag these for refactoring.

        Args:
            node: AST node representing a function definition

        Returns:
            dict: Metrics specific to this function
        """
        func_info = {
            'name': node.name,  # Function name as string
            'line_number': node.lineno,  # Line where function starts (1-indexed)
            'num_params': len(node.args.args),  # Count function parameters
            'num_lines': self._count_function_lines(node),  # How many lines
            'complexity': self._calculate_cyclomatic_complexity(node),  # McCabe complexity
            'max_depth': self._calculate_max_depth(node),  # Deepest nesting
        }

        # Update global max nesting depth if this function is deeper
        # We track both per-function AND overall max depth
        if func_info['max_depth'] > self.metrics['max_nesting_depth']:
            self.metrics['max_nesting_depth'] = func_info['max_depth']

        return func_info

    @staticmethod
    def _analyze_class(node: ast.ClassDef) -> Dict[str, Any]:
        """
        Analyze a class definition.

        Extracts basic info about a class - its name and what methods it has.
        We don't do deep complexity analysis on classes (yet), just gather
        structural info.

        Why static method: Doesn't need access to self.metrics, so making it
        static signals that it's a pure function (same inputs always give same
        outputs). Also slightly faster (no self parameter).

        Args:
            node: AST node representing a class definition

        Returns:
            dict: Class name, method count, method names
        """
        # Find all methods in the class (functions defined in class body)
        # node.body contains all statements inside the class
        # We filter for FunctionDef nodes (method definitions)
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]

        # Extract just the method names (list of strings)
        method_names = [m.name for m in methods]

        return {
            'name': node.name,  # Class name
            'line_number': node.lineno,  # Where class starts
            'num_methods': len(methods),  # How many methods (including __init__)
            'method_names': method_names,  # List of method names for display
        }

    @staticmethod
    def _calculate_cyclomatic_complexity(node: ast.AST) -> int:
        """
        Calculate McCabe cyclomatic complexity for a code node.

        WHAT IS CYCLOMATIC COMPLEXITY:
        Measures the number of independent paths through the code. Higher
        complexity = more paths = harder to test = more likely to have bugs.

        Formula: Complexity = Number of decision points + 1

        Decision points are places where execution can branch:
        - if statements (2 paths: True or False)
        - for/while loops (2 paths: execute body or skip)
        - except clauses (2 paths: exception or no exception)
        - Boolean operators (and/or create additional paths)
        - Comprehensions (list/dict/set comprehensions add a path)

        Example:
            def simple():           # Complexity = 1 (base)
                return 5

            def with_if(x):         # Complexity = 2 (base + if)
                if x > 0:
                    return True
                return False

            def complex(x, y):      # Complexity = 4
                if x > 0:           # +1 (if)
                    for i in range(x):  # +1 (for)
                        if i == y:      # +1 (if)
                            return i
                return None

        WHY IT MATTERS:
        - Complexity 1-10: Simple, easy to test
        - Complexity 11-20: Moderate, needs attention
        - Complexity 21+: Complex, should refactor

        Research by Thomas McCabe (1976) showed that functions with complexity
        >10 had exponentially more bugs. This has been validated across
        millions of lines of code in industry.

        Implementation note: We walk the entire subtree under this node,
        counting decision points. Using ast.walk() visits every node exactly
        once in depth-first order.

        Args:
            node: AST node to analyze (usually a FunctionDef)

        Returns:
            int: Cyclomatic complexity (minimum 1)
        """
        complexity = 1  # Base complexity (linear code path)

        # Walk every node in the subtree
        for child in ast.walk(node):

            # Control flow statements add decision points
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                # if/while/for each add one decision point (execute or skip)
                complexity += 1

            # Exception handlers are decision points
            elif isinstance(child, ast.ExceptHandler):
                # except clause: exception thrown or not
                complexity += 1

            # Boolean operators create multiple paths
            elif isinstance(child, ast.BoolOp):
                # and/or operators: each operand is a decision point
                # "if a and b and c" has 3 decision points
                # We add (number of values - 1) because first value is already
                # counted by the surrounding if statement
                complexity += len(child.values) - 1

            # Comprehensions are loops (decision points)
            elif isinstance(child, (ast.ListComp, ast.DictComp, ast.SetComp)):
                # [x for x in range(10)] is essentially a loop
                complexity += 1

        return complexity

    @staticmethod
    def _calculate_max_depth(node: ast.AST, current_depth: int = 0) -> int:
        """
        Calculate maximum nesting depth in a code section.

        WHAT IS NESTING DEPTH:
        How many levels deep control structures are nested. Each if/for/while/etc
        increases depth by 1.

        Example:
            def shallow():              # depth 0 (function itself doesn't count)
                x = 5                   # depth 0
                return x

            def deep():                 # depth 0
                for i in range(10):     # depth 1
                    if i > 5:           # depth 2
                        for j in range(i):  # depth 3
                            if j == 2:      # depth 4
                                print(j)    # depth 4

        WHY IT MATTERS:
        - Depth 0-2: Easy to understand
        - Depth 3-4: Moderate, still manageable
        - Depth 5+: Hard to follow, should refactor

        Deep nesting makes code hard to read and understand. Human working
        memory can only hold 7±2 items (Miller's Law), so deeply nested code
        exceeds our cognitive capacity.

        Best practice: Extract nested logic into helper functions. Instead of:
            for x in data:
                if x > 0:
                    for y in x.items:
                        if y.valid:
                            process(y)

        Refactor to:
            for x in data:
                if x > 0:
                    process_items(x.items)

        IMPLEMENTATION:
        This is a RECURSIVE function (calls itself). We walk the tree depth-first,
        increasing depth when we hit nesting constructs, tracking the maximum
        depth we ever reach.

        Recursion was tricky to get right - had to think carefully about when
        to increment current_depth vs just pass it through. The key insight is
        that only nesting_nodes increase depth; other nodes pass depth unchanged.

        Args:
            node: Current AST node being analyzed
            current_depth: Depth at this node (0 at function start)

        Returns:
            int: Maximum depth found in this subtree
        """
        max_depth = current_depth  # Start with current depth

        # These node types increase nesting depth
        nesting_nodes = (
            ast.If,           # if/elif/else statements
            ast.For,          # for loops
            ast.While,        # while loops
            ast.With,         # with statements (context managers)
            ast.Try,          # try/except blocks
            ast.FunctionDef,  # Nested function definitions
            ast.ClassDef      # Nested class definitions (rare but possible)
        )

        # Visit each direct child of this node
        # Using iter_child_nodes (not walk) because we control recursion
        for child in ast.iter_child_nodes(node):

            if isinstance(child, nesting_nodes):
                # This child increases depth - recurse with depth + 1
                child_depth = ComplexityAnalyzer._calculate_max_depth(child, current_depth + 1)
            else:
                # Other nodes don't increase depth - recurse with same depth
                child_depth = ComplexityAnalyzer._calculate_max_depth(child, current_depth)

            # Track the maximum depth we've seen
            max_depth = max(max_depth, child_depth)

        return max_depth

    @staticmethod
    def _count_function_lines(node: ast.FunctionDef) -> int:
        """
        Count lines of code in a function.

        Uses the AST node's line number attributes. Python 3.8+ added end_lineno
        to track where functions end, making this trivial.

        Edge case: Very old Python or weird code might not have end_lineno.
        We fallback to 1 rather than crashing.

        Args:
            node: Function definition node

        Returns:
            int: Number of lines (inclusive of def and return)
        """
        # Check if we have end_lineno (Python 3.8+)
        if not hasattr(node, 'end_lineno') or node.end_lineno is None:
            # Fallback for old Python or weird cases
            return 1

        # Calculate line span: end - start + 1 (inclusive)
        # Example: function on lines 10-15 = 15 - 10 + 1 = 6 lines
        return node.end_lineno - node.lineno + 1

    @staticmethod
    def _get_import_info(node: Union[ast.Import, ast.ImportFrom]) -> Dict[str, Any]:
        """
        Extract import information from import statements.

        Tracks what modules/packages the code depends on. Useful for seeing
        dependencies and flagging if too many imports (might indicate code
        doing too much).

        Two types of imports:
        - import os, sys  (ast.Import)
        - from os import path  (ast.ImportFrom)

        Args:
            node: Import or ImportFrom node

        Returns:
            dict: Import info (type, modules/names)
        """
        if isinstance(node, ast.Import):
            # Regular import: "import os, sys"
            return {
                'type': 'import',
                'modules': [alias.name for alias in node.names]
            }
        elif isinstance(node, ast.ImportFrom):
            # From import: "from os import path, getcwd"
            return {
                'type': 'from_import',
                'module': node.module or '',  # Module being imported from
                'names': [alias.name for alias in node.names]  # What's imported
            }
        return {}  # Shouldn't hit this but playing it safe

    def _calculate_total_complexity(self) -> int:
        """
        Sum cyclomatic complexity across all functions.

        Total complexity = 1 (module base) + sum of all function complexities

        Why +1 for module: The module itself is one execution path (running
        the file top to bottom). Each function adds its own complexity.

        Returns:
            int: Total cyclomatic complexity for entire file
        """
        total = 1  # Base complexity for module-level code

        # Add complexity from each function
        for func in self.metrics['functions']:
            total += func['complexity']

        return total

    def _calculate_maintainability_index(self) -> float:
        """
        Calculate maintainability index (code quality score 0-100).

        WHAT IS MAINTAINABILITY INDEX:
        A single number that represents overall code quality. Higher = better.
        - 0-25: Unmaintainable (needs urgent refactoring)
        - 26-50: Low maintainability (needs work)
        - 51-75: Moderate maintainability (acceptable)
        - 76-100: Highly maintainable (good code!)

        FULL FORMULA (Microsoft/SEI):
        MI = 171 - 5.2 * ln(HV) - 0.23 * CC - 16.2 * ln(LOC)
        Where:
        - HV = Halstead Volume (measures "information content")
        - CC = Cyclomatic Complexity
        - LOC = Lines of Code

        OUR SIMPLIFIED VERSION:
        We don't calculate full Halstead Volume (requires operator/operand
        counting which is complex). Instead, we use a simplified formula
        based on complexity-to-LOC ratio:

        MI = 100 - (complexity_per_line * 100)

        This gives similar results: low complexity per line = high MI,
        high complexity per line = low MI.

        Why simplified: Full Halstead Volume requires counting every operator
        and operand in the code, which is complicated and not essential for
        this educational project. Our simplified version captures the key idea:
        complex code relative to its size is hard to maintain.

        Implementation note: We clamp the result to [0, 100] range to avoid
        negative numbers or values over 100.

        Returns:
            float: Maintainability index (0-100, higher = better)
        """
        # Avoid division by zero if there's no code
        loc = max(self.metrics['code_lines'], 1)
        cc = self.metrics['cyclomatic_complexity']

        # Calculate complexity per line of code
        # Low ratio = simple code, High ratio = complex code
        complexity_ratio = cc / loc

        # Convert to 0-100 scale (higher = better)
        # Subtract from 100 so high complexity gives low MI
        mi = 100 - (complexity_ratio * 100)

        # Clamp to [0, 100] range
        # max(0, ...) ensures we don't go negative
        # min(100, ...) ensures we don't go over 100
        mi = max(0, min(100, mi))

        return round(mi, 2)  # Round to 2 decimal places

    def _generate_recommendations(self) -> List[str]:
        """
        Generate actionable recommendations based on metrics.

        This is where we turn raw numbers into human-readable advice.
        Instead of just showing "complexity: 57", we say "High complexity,
        consider refactoring".

        Thresholds are based on industry research:
        - Complexity >50: Definitely too high (McCabe recommended 10)
        - Complexity >10 per function: Needs refactoring
        - Nesting depth >4: Hard to understand (exceeds working memory)
        - Functions >50 lines: Should be split up

        These aren't arbitrary - they come from decades of software
        engineering research and have been validated on millions of lines
        of production code.

        Returns:
            list: String recommendations (emojis make them friendlier!)
        """
        recommendations = []

        # Check overall complexity
        if self.metrics['cyclomatic_complexity'] > 50:
            recommendations.append(
                "⚠️ High overall complexity. Consider breaking down into smaller functions."
            )

        # Check individual function complexity
        # We use >10 because McCabe's research showed that's where bugs increase exponentially
        complex_functions = [f for f in self.metrics['functions'] if f['complexity'] > 10]
        if complex_functions:
            # Show up to 3 function names (don't overwhelm user with long list)
            func_names = ', '.join(f['name'] for f in complex_functions[:3])
            recommendations.append(
                f"⚠️ {len(complex_functions)} function(s) have high complexity (>10). "
                f"Consider refactoring: {func_names}"
            )

        # Check nesting depth
        # >4 levels exceeds human working memory (Miller's 7±2 rule)
        if self.metrics['max_nesting_depth'] > 4:
            recommendations.append(
                f"⚠️ Maximum nesting depth is {self.metrics['max_nesting_depth']}. "
                "Consider extracting nested logic into separate functions."
            )

        # Check long functions
        # >50 lines is when functions typically do too much (violation of Single Responsibility)
        long_functions = [f for f in self.metrics['functions'] if f['num_lines'] > 50]
        if long_functions:
            recommendations.append(
                f"⚠️ {len(long_functions)} function(s) are long (>50 lines). "
                "Consider breaking them down."
            )

        # Check for lack of modularization
        # If you have 100+ lines but < 3 functions, you're probably not using functions enough
        if self.metrics['code_lines'] > 100 and self.metrics['num_functions'] < 3:
            recommendations.append(
                "💡 Code could benefit from more modularization. "
                "Consider extracting repeated logic into functions."
            )

        # Positive feedback if everything looks good!
        # Users appreciate knowing when they did well
        if not recommendations:
            recommendations.append(
                "✅ Code shows good structure and maintainability!"
            )

        return recommendations

    def generate_report(self) -> str:
        """
        Generate human-readable text report of the analysis.

        This formats all the metrics into a nice report that can be printed
        to console or displayed in a text area. Used for debugging and for
        users who want a comprehensive overview.

        Alternative: We also return raw metrics dict from analyze(), so views
        can format data however they want (JSON, HTML table, etc.). This
        text report is just one possible presentation.

        Returns:
            str: Formatted multi-line report with all metrics
        """
        if not self.metrics:
            return "No analysis performed yet."

        # Build report as list of strings, join at the end
        # This is more efficient than string concatenation in a loop
        report = []

        # Header
        report.append("=" * 60)
        report.append("CODE COMPLEXITY ANALYSIS REPORT")
        report.append("=" * 60)
        report.append("")

        # Overall metrics
        report.append("OVERALL METRICS:")
        report.append(f"  Total Lines: {self.metrics['total_lines']}")
        report.append(f"  Code Lines: {self.metrics['code_lines']}")
        report.append(f"  Comment Lines: {self.metrics['comment_lines']}")
        report.append(f"  Blank Lines: {self.metrics['blank_lines']}")
        report.append(f"  Cyclomatic Complexity: {self.metrics['cyclomatic_complexity']}")
        report.append(f"  Maintainability Index: {self.metrics['maintainability_index']}/100")
        report.append("")

        # Structure
        report.append("CODE STRUCTURE:")
        report.append(f"  Functions: {self.metrics['num_functions']}")
        report.append(f"  Classes: {self.metrics['num_classes']}")
        report.append(f"  Max Nesting Depth: {self.metrics['max_nesting_depth']}")
        report.append("")

        # Function details
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

        # Footer
        report.append("=" * 60)

        # Join all lines with newlines
        return "\n".join(report)