"""
Searching algorithm implementations with step-by-step visualization.

Implementation note: Uses generator functions (yield) to capture every step of
the search process for visualization. Had to be careful about when to copy arrays
to avoid breaking visualization state.

Algorithms implemented:
- Binary Search: O(log n) but REQUIRES sorted data
- Linear Search: O(n) but works on ANY data
"""
from typing import List, Dict, Any, Generator
import time


class SearchingAlgorithm:
    """
    Base class for searching algorithms.

    Why a base class: Avoids code duplication. Both BinarySearch and LinearSearch
    need to track comparisons and execution time.
    """

    def __init__(self):
        """Initialize performance tracking counters."""
        self.comparisons = 0
        self.start_time = None

    def reset_stats(self):
        """
        Reset counters before starting a new search.

        Without resetting, multiple searches would accumulate stats and give
        wrong counts. Learned this during testing!
        """
        self.comparisons = 0
        self.start_time = time.time()

    def get_elapsed_time_ms(self):
        """Calculate how long the search has been running in milliseconds."""
        if self.start_time is None:
            return 0.0
        return (time.time() - self.start_time) * 1000


class BinarySearch(SearchingAlgorithm):
    """
    Binary Search - divide and conquer search algorithm.

    CRITICAL REQUIREMENT: Array MUST be sorted. Binary search assumes ordered
    data and uses that to eliminate half the search space each comparison.

    Why it's O(log n): Each comparison eliminates HALF the remaining elements.
    - 100 elements: max 7 comparisons
    - 1 million elements: max 20 comparisons

    Implementation choice: Iterative (loop) instead of recursive because it's
    more space-efficient (O(1) vs O(log n) call stack) and easier to visualize.
    """

    def search(
            self,
            arr: List[int],
            target: int
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Search for target in sorted array using binary search.

        Algorithm: Start with pointers at array ends. Calculate middle, compare
        to target, adjust pointers to eliminate half the search space. Repeat
        until found or pointers cross.

        Args:
            arr: List of integers IN SORTED ORDER (unsorted gives wrong results!)
            target: Value to search for

        Yields:
            dict: State at each step for visualization
        """
        self.reset_stats()
        left = 0
        right = len(arr) - 1

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
                left = mid + 1  # Already checked mid

            else:
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
                right = mid - 1  # Already checked mid

        # Exhausted search space without finding target
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
    Linear Search - sequential element-by-element search.

    Algorithm: Check every element from start to end until target is found
    or array is exhausted.

    Why it's O(n): Worst case checks every element.

    When linear search is BETTER than binary search:
    - Unsorted data (binary search requires sorting first - O(n log n) overhead)
    - Small datasets (<50 elements) - simpler code, better cache performance
    - Linked lists (binary search needs random access)
    - Target likely near beginning (best case O(1))
    """

    def search(
            self,
            arr: List[int],
            target: int
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Search for target by checking each element sequentially.

        Advantage: Works on UNSORTED data.
        Disadvantage: Slower for large sorted datasets.

        Args:
            arr: List of integers (CAN be unsorted)
            target: Value to search for

        Yields:
            dict: State at each comparison
        """
        self.reset_stats()

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

        # Checked every element without finding target
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