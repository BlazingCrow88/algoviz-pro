"""
Searching algorithm implementations with step-by-step visualization support.

This module implements classic searching algorithms with the ability to yield
intermediate states for visualization purposes.

Algorithms included:
- Binary Search (O(log n))
- Linear Search (O(n))
- Breadth-First Search (O(V+E))
"""
from typing import List, Dict, Any, Generator, Optional
from collections import deque
import time


class SearchingAlgorithm:
    """
    Base class for all searching algorithms.

    Provides common functionality for tracking search performance.

    Attributes:
        comparisons: Number of element comparisons performed
        start_time: When the algorithm started executing
    """

    def __init__(self):
        """Initialize counters for tracking algorithm performance."""
        self.comparisons = 0
        self.start_time = None

    def reset_stats(self):
        """Reset all performance counters to zero."""
        self.comparisons = 0
        self.start_time = time.time()

    def get_elapsed_time_ms(self):
        """Get elapsed time since algorithm started in milliseconds."""
        if self.start_time is None:
            return 0.0
        return (time.time() - self.start_time) * 1000


class BinarySearch(SearchingAlgorithm):
    """
    Binary Search implementation with step-by-step visualization.

    Binary search finds a target value in a sorted array by repeatedly
    dividing the search interval in half.

    Algorithm Description:
        1. Compare target with middle element
        2. If match found, return index
        3. If target is less than middle, search left half
        4. If target is greater, search right half
        5. Repeat until found or interval is empty

    Time Complexity:
        - Best Case: O(1) when target is at middle
        - Average Case: O(log n)
        - Worst Case: O(log n)

    Space Complexity: O(1) for iterative, O(log n) for recursive

    Requirements: Array must be sorted

    When to use:
        - Large sorted datasets
        - When fast search time is critical
        - Random access data structure (arrays)

    Example:
        >>> searcher = BinarySearch()
        >>> arr = [1, 2, 5, 8, 9, 12, 15]
        >>> for state in searcher.search(arr, 8):
        ...     print(state['message'])
    """

    def search(
            self,
            arr: List[int],
            target: int
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Search for target in sorted array using binary search.

        Args:
            arr: Sorted list of integers
            target: Value to search for

        Yields:
            dict: State information for visualization containing:
                - array: Current array
                - target: Target value
                - left: Left boundary of search
                - right: Right boundary of search
                - mid: Current middle index
                - comparisons: Total comparisons made
                - found: Whether target was found
                - found_index: Index where target was found (if applicable)
                - message: Description of current step
        """
        self.reset_stats()
        left = 0
        right = len(arr) - 1

        # Initial state
        yield {
            'array': arr.copy(),
            'target': target,
            'search_range': list(range(left, right + 1)),
            'message': f'Starting binary search for {target} in sorted array',
            'comparisons': 0,
            'time_ms': self.get_elapsed_time_ms(),
            'step_type': 'start'
        }

        while left <= right:
            mid = (left + right) // 2
            self.comparisons += 1

            # Yield state showing current middle element
            yield {
                'array': arr.copy(),
                'target': target,
                'search_range': list(range(left, right + 1)),
                'mid': mid,
                'message': f'Checking middle element: arr[{mid}] = {arr[mid]}',
                'comparisons': self.comparisons,
                'time_ms': self.get_elapsed_time_ms(),
                'step_type': 'compare'
            }

            if arr[mid] == target:
                # Found the target!
                yield {
                    'array': arr.copy(),
                    'target': target,
                    'found': True,
                    'found_index': mid,
                    'message': f'Found {target} at index {mid}!',
                    'comparisons': self.comparisons,
                    'time_ms': self.get_elapsed_time_ms(),
                    'complete': True,
                    'step_type': 'found'
                }
                return

            elif arr[mid] < target:
                # Target is in right half
                yield {
                    'array': arr.copy(),
                    'target': target,
                    'search_range': list(range(left, right + 1)),
                    'mid': mid,
                    'message': f'{arr[mid]} < {target}, searching right half',
                    'comparisons': self.comparisons,
                    'time_ms': self.get_elapsed_time_ms(),
                    'step_type': 'eliminate_left'
                }
                left = mid + 1

            else:
                # Target is in left half
                yield {
                    'array': arr.copy(),
                    'target': target,
                    'search_range': list(range(left, right + 1)),
                    'mid': mid,
                    'message': f'{arr[mid]} > {target}, searching left half',
                    'comparisons': self.comparisons,
                    'time_ms': self.get_elapsed_time_ms(),
                    'step_type': 'eliminate_right'
                }
                right = mid - 1

        # Target not found
        yield {
            'array': arr.copy(),
            'target': target,
            'found': False,
            'message': f'{target} not found in array',
            'comparisons': self.comparisons,
            'time_ms': self.get_elapsed_time_ms(),
            'complete': True,
            'step_type': 'not_found'
        }


class LinearSearch(SearchingAlgorithm):
    """
    Linear Search implementation with step-by-step visualization.

    Linear search sequentially checks each element until the target is found
    or the entire array has been searched.

    Algorithm Description:
        1. Start at the beginning of the array
        2. Compare each element with target
        3. If match found, return index
        4. Continue until found or end of array

    Time Complexity:
        - Best Case: O(1) when target is first element
        - Average Case: O(n)
        - Worst Case: O(n) when target is last or not present

    Space Complexity: O(1)

    When to use:
        - Small datasets
        - Unsorted data
        - When simplicity is more important than speed
        - Sequential access data structures (linked lists)

    Advantages:
        - Works on unsorted data
        - Simple to implement
        - No preprocessing required
    """

    def search(
            self,
            arr: List[int],
            target: int
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Search for target using linear search.

        Args:
            arr: List of integers (can be unsorted)
            target: Value to search for

        Yields:
            dict: State information for visualization
        """
        self.reset_stats()

        # Initial state
        yield {
            'array': arr.copy(),
            'target': target,
            'message': f'Starting linear search for {target}',
            'comparisons': 0,
            'time_ms': self.get_elapsed_time_ms(),
            'step_type': 'start'
        }

        for i in range(len(arr)):
            self.comparisons += 1

            # Yield comparison state
            yield {
                'array': arr.copy(),
                'target': target,
                'checking_index': i,
                'message': f'Checking arr[{i}] = {arr[i]}',
                'comparisons': self.comparisons,
                'time_ms': self.get_elapsed_time_ms(),
                'step_type': 'compare'
            }

            if arr[i] == target:
                # Found!
                yield {
                    'array': arr.copy(),
                    'target': target,
                    'found': True,
                    'found_index': i,
                    'message': f'Found {target} at index {i}!',
                    'comparisons': self.comparisons,
                    'time_ms': self.get_elapsed_time_ms(),
                    'complete': True,
                    'step_type': 'found'
                }
                return

        # Not found
        yield {
            'array': arr.copy(),
            'target': target,
            'found': False,
            'message': f'{target} not found in array',
            'comparisons': self.comparisons,
            'time_ms': self.get_elapsed_time_ms(),
            'complete': True,
            'step_type': 'not_found'
        }


class BreadthFirstSearch:
    """
    Breadth-First Search (BFS) for graph traversal.

    BFS explores a graph level by level, visiting all neighbors of a node
    before moving to the next level.

    Time Complexity: O(V + E) where V = vertices, E = edges
    Space Complexity: O(V) for the queue

    When to use:
        - Finding the shortest path in unweighted graphs
        - Level-order traversal
        - Testing if graph is bipartite
        - Finding connected components
    """

    def __init__(self):
        """Initialize BFS algorithm."""
        self.visited = set()
        self.start_time = None

    def search(
            self,
            graph: Dict[int, List[int]],
            start: int,
            target: Optional[int] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Perform BFS on graph starting from start node.

        Args:
            graph: Adjacency list representation {node: [neighbors]}
            start: Starting node
            target: Optional target node to find

        Yields:
            dict: State information for visualization
        """
        self.start_time = time.time()
        self.visited = set()
        queue = deque([start])
        parent = {start: None}
        level = {start: 0}

        # Initial state
        yield {
            'graph': graph,
            'start': start,
            'target': target,
            'queue': list(queue),
            'visited': list(self.visited),
            'message': f'Starting BFS from node {start}',
            'step_type': 'start'
        }

        while queue:
            node = queue.popleft()

            if node not in self.visited:
                self.visited.add(node)

                # Yield visiting state
                yield {
                    'graph': graph,
                    'current_node': node,
                    'queue': list(queue),
                    'visited': list(self.visited),
                    'level': level[node],
                    'message': f'Visiting node {node} at level {level[node]}',
                    'step_type': 'visit'
                }

                # Check if we found target
                if target is not None and node == target:
                    # Reconstruct path
                    path = []
                    current = node
                    while current is not None:
                        path.append(current)
                        current = parent[current]
                    path.reverse()

                    yield {
                        'graph': graph,
                        'found': True,
                        'target': target,
                        'path': path,
                        'visited': list(self.visited),
                        'message': f'Found target {target}! Path: {path}',
                        'complete': True,
                        'step_type': 'found'
                    }
                    return

                # Add unvisited neighbors to queue
                for neighbor in graph.get(node, []):
                    if neighbor not in self.visited and neighbor not in queue:
                        queue.append(neighbor)
                        parent[neighbor] = node
                        level[neighbor] = level[node] + 1

                        yield {
                            'graph': graph,
                            'current_node': node,
                            'neighbor': neighbor,
                            'queue': list(queue),
                            'visited': list(self.visited),
                            'message': f'Adding neighbor {neighbor} to queue',
                            'step_type': 'enqueue'
                        }

        # Traversal complete
        if target is None:
            yield {
                'graph': graph,
                'visited': list(self.visited),
                'message': 'BFS traversal complete',
                'complete': True,
                'step_type': 'complete'
            }
        else:
            yield {
                'graph': graph,
                'found': False,
                'target': target,
                'visited': list(self.visited),
                'message': f'Target {target} not found in graph',
                'complete': True,
                'step_type': 'not_found'
            }