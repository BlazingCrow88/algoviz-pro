"""
Searching algorithm implementations with step-by-step visualization.

Why searching algorithms matter: Half of programming is finding things in data
structures. Understanding when to use binary vs linear search is fundamental CS.

Implementation note: All these algorithms use generator functions (yield instead
of return) so we can capture every step of the search process for visualization.
This was trickier than I expected - I had to be careful about when to copy arrays
and when yielding was safe without breaking the visualization state.

Algorithms implemented:
- Binary Search: O(log n) but REQUIRES sorted data
- Linear Search: O(n) but works on ANY data
"""
from typing import List, Dict, Any, Generator
import time


class SearchingAlgorithm:
    """
    Base class for searching algorithms - similar pattern to SortingAlgorithm.

    Why a base class: Avoids code duplication. Both BinarySearch and LinearSearch
    need to track comparisons and execution time, so we define it once here.
    """

    def __init__(self):
        """
        Initialize performance tracking counters.

        These start at zero and get reset each time search() is called,
        so we can track stats for individual search operations.
        """
        self.comparisons = 0  # How many elements did we check?
        self.start_time = None  # When did the search start?

    def reset_stats(self):
        """
        Reset counters before starting a new search.

        Why this matters: Without resetting, multiple searches would accumulate
        stats, and we'd get wrong counts. Learned this the hard way when testing!

        Also sets start_time to current moment so we can calculate execution time.
        """
        self.comparisons = 0
        self.start_time = time.time()  # Captures current timestamp

    def get_elapsed_time_ms(self):
        """
        Calculate how long the search has been running.

        Returns:
            float: Milliseconds since search started, or 0 if not started yet
        """
        if self.start_time is None:
            return 0.0
        # time.time() returns seconds, multiply by 1000 for milliseconds
        return (time.time() - self.start_time) * 1000


class BinarySearch(SearchingAlgorithm):
    """
    Binary Search - the classic "divide and conquer" search algorithm.

    The big idea: If you're searching a phone book for "Smith", you don't start
    at the beginning - you open to the middle, see if Smith comes before or after,
    then eliminate half the book. Repeat until found.

    THE CRITICAL REQUIREMENT: Array MUST be sorted. This is non-negotiable.
    Binary search assumes the data is ordered and uses that property to make
    decisions about which half to search.

    Why it's O(log n): Each comparison eliminates HALF the remaining elements.
    - 100 elements: max 7 comparisons (log₂ 100 ≈ 6.64)
    - 1 million elements: max 20 comparisons (log₂ 1,000,000 ≈ 19.93)
    This is why binary search is so much faster than linear search for large datasets.

    Implementation choice: Using iterative (loop) instead of recursive approach
    because it's more space-efficient (O(1) instead of O(log n) for the call stack)
    and easier to visualize step-by-step.

    """

    def search(
            self,
            arr: List[int],
            target: int
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Search for target value in a sorted array using binary search.

        How it works: It starts with left pointer at 0, and right pointer at last index.
        Then it calculates middle, compares target to middle value, adjust pointers to
        eliminate half the search space. This repeats until found or pointers cross.

        Args:
            arr: List of integers IN SORTED ORDER (ascending)
                 If array isn't sorted, binary search gives wrong results!
            target: The value we're searching for

        Yields:
            dict: State at each step showing:
                - What we're comparing
                - Which half of array we're searching
                - Current left/right/mid-pointers
                - Whether we found it

        Generator pattern: Using yield instead of return lets us pause execution
        at each comparison so the visualization can display the current state.
        """
        self.reset_stats()
        left = 0  # Start of search range
        right = len(arr) - 1  # End of search range

        # Show initial state before any comparisons
        yield {
            'array': arr.copy(),  # Copy so visualization captures this snapshot
            'target': target,
            'search_range': list(range(left, right + 1)),  # Show whole array initially
            'message': f'Starting binary search for {target} in sorted array',
            'comparisons': 0,
            'time_ms': self.get_elapsed_time_ms(),
            'step_type': 'start'
        }

        # Main search loop - continues while search range is valid
        # When left > right, we've eliminated all possibilities
        while left <= right:
            # Calculate middle index
            # Using // (integer division) ensures mid is always an integer
            mid = (left + right) // 2
            self.comparisons += 1

            # Show what we're comparing at this step
            yield {
                'array': arr.copy(),
                'target': target,
                'search_range': list(range(left, right + 1)),  # Current search space
                'mid': mid,  # Highlight the middle element we're checking
                'message': f'Checking middle element: arr[{mid}] = {arr[mid]}',
                'comparisons': self.comparisons,
                'time_ms': self.get_elapsed_time_ms(),
                'step_type': 'compare'
            }

            # Case 1: Found it!
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
                return  # Stop searching - we found it

            # Case 2: Target is larger than middle, so it must be in right half
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
                # Eliminate left half by moving left pointer
                # +1 because we already checked mid
                left = mid + 1

            # Case 3: Target is smaller than middle, so it must be in left half
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
                # Eliminate right half by moving right pointer
                # -1 because we already checked mid
                right = mid - 1

        # If we get here, left > right, meaning we've exhausted the search space
        # without finding the target
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
    Linear Search - the simplest search algorithm (and sometimes the best choice!).

    The idea: Just check every element one by one from start to end. When you
    find the target, stop. If you reach the end without finding it, it's not there.

    Why it's O(n): In the worst case, we check every single element (n comparisons).
    If the array has 1000 elements, we might make up to 1000 comparisons.

    "But wait," you might ask, "isn't binary search always better since it's O(log n)?"

    NO! Here's when linear search is actually BETTER:
    1. **Unsorted data**: Binary search REQUIRES sorted data. If your data isn't
       sorted and won't be sorted, linear search is your only option (or you need
       to sort first, which costs O(n log n) - might not be worth it for one search).

    2. **Small datasets**: For arrays with < 50 elements, linear search is often
       faster in practice because it's simpler (no division calculations, better
       cache performance, simpler code = fewer CPU cycles per comparison).

    3. **Linked lists**: Binary search needs random access (jumping to middle),
       which linked lists don't provide. Linear search works fine with sequential
       access.

    4. **Already found early**: If the target is likely to be near the beginning,
       linear search's best case O(1) beats binary search's O(log n).

    """

    def search(
            self,
            arr: List[int],
            target: int
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Search for target by checking each element sequentially.

        Simple algorithm: Start at index 0, check if it matches target.
        If not, move to index 1, check again. Continue until found, or
        we reach the end of the array.

        Advantage: Works on UNSORTED data (unlike binary search).
        Disadvantage: Slower for large sorted datasets.

        Args:
            arr: List of integers (CAN be unsorted - that's the point!)
            target: Value we're looking for

        Yields:
            dict: State at each comparison showing which index we're checking

        """
        self.reset_stats()

        # Initial state before starting the search
        yield {
            'array': arr.copy(),
            'target': target,
            'message': f'Starting linear search for {target}',
            'comparisons': 0,
            'time_ms': self.get_elapsed_time_ms(),
            'step_type': 'start'
        }

        # Check each element one by one
        for i in range(len(arr)):
            self.comparisons += 1

            # Show which element we're currently checking
            yield {
                'array': arr.copy(),
                'target': target,
                'checking_index': i,  # Highlight this position in visualization
                'message': f'Checking arr[{i}] = {arr[i]}',
                'comparisons': self.comparisons,
                'time_ms': self.get_elapsed_time_ms(),
                'step_type': 'compare'
            }

            # Check if this is the element we're looking for
            if arr[i] == target:
                # Found it! Stop searching.
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
                return  # Exit the generator - no need to check remaining elements

        # If we get here, we checked every element and didn't find the target
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
