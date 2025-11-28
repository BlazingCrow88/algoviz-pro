"""
Sorting algorithm implementations with step-by-step visualization support.

This module implements classic sorting algorithms with the ability to yield
intermediate states for visualization purposes. Each algorithm tracks
comparisons and swaps to demonstrate performance characteristics.

All algorithms follow a common pattern:
1. Inherit from SortingAlgorithm base class
2. Implement sort() method as a generator
3. Yield state dictionaries at each significant step
4. Track comparisons and swaps

Time and space complexities are documented in each class docstring.
"""
from typing import List, Dict, Any, Generator
import time


class SortingAlgorithm:
    """
    Base class for all sorting algorithms.

    Provides common functionality for tracking algorithm performance
    including comparison counts, swap counts, and execution time.

    Attributes:
        comparisons: Number of element comparisons performed
        swaps: Number of element swaps performed
        start_time: When the algorithm started executing
    """

    def __init__(self):
        """Initialize counters for tracking algorithm performance."""
        self.comparisons = 0
        self.swaps = 0
        self.start_time = None

    def reset_stats(self):
        """Reset all performance counters to zero."""
        self.comparisons = 0
        self.swaps = 0
        self.start_time = time.time()

    def get_elapsed_time_ms(self):
        """
        Get elapsed time since algorithm started.

        Returns:
            float: Elapsed time in milliseconds
        """
        if self.start_time is None:
            return 0.0
        return (time.time() - self.start_time) * 1000


class BubbleSort(SortingAlgorithm):
    """
    Bubble Sort implementation with step-by-step visualization.

    Bubble sort repeatedly steps through the list, compares adjacent elements,
    and swaps them if they're in the wrong order. This process repeats until
    the list is sorted.

    Algorithm Description:
        1. Start at the beginning of the array
        2. Compare each pair of adjacent elements
        3. Swap them if they're in wrong order
        4. After each pass, the largest unsorted element "bubbles" to its position
        5. Repeat until no swaps are needed

    Time Complexity:
        - Best Case: O(n) when array is already sorted
        - Average Case: O(n²)
        - Worst Case: O(n²) when array is reverse sorted

    Space Complexity: O(1) - sorts in place, only uses constant extra space

    Stability: Yes - maintains relative order of equal elements

    When to use:
        - Small datasets (< 50 elements)
        - Nearly sorted data (takes advantage of early termination)
        - When simplicity is more important than efficiency
        - Educational purposes (easy to understand and visualize)
    """

    def sort(self, arr: List[int]) -> Generator[Dict[str, Any], None, None]:
        """
        Sort array using bubble sort, yielding visualization states.

        This generator yields a dictionary at each significant step showing:
        - Current array state
        - Indices being compared
        - Sorted region
        - Performance statistics
        - Descriptive message

        Args:
            arr: List of integers to sort

        Yields:
            dict: State information for visualization containing:
                - array: Current state of the array
                - comparing: Indices being compared (if applicable)
                - swapped: Indices that were swapped (if applicable)
                - sorted_region: List of indices that are in final position
                - comparisons: Total comparisons so far
                - swaps: Total swaps so far
                - message: Human-readable description of current step
                - complete: True when sorting is finished

        Example:
            >>> sorter = BubbleSort()
            >>> for state in sorter.sort([5, 2, 8, 1, 9]):
            ...     print(state['array'])
        """
        self.reset_stats()
        n = len(arr)
        arr = arr.copy()  # Don't modify original array

        # Outer loop - each pass bubbles one element to its final position
        for i in range(n):
            swapped = False

            # Inner loop - compare adjacent elements
            for j in range(0, n - i - 1):
                self.comparisons += 1

                # Yield state showing which elements we're comparing
                yield {
                    'array': arr.copy(),
                    'comparing': [j, j + 1],
                    'sorted_region': list(range(n - i, n)),
                    'comparisons': self.comparisons,
                    'swaps': self.swaps,
                    'time_ms': self.get_elapsed_time_ms(),
                    'message': f'Comparing {arr[j]} and {arr[j + 1]}',
                    'step_type': 'compare'
                }

                # Swap if elements are in wrong order
                if arr[j] > arr[j + 1]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
                    self.swaps += 1
                    swapped = True

                    # Yield state after swap
                    yield {
                        'array': arr.copy(),
                        'swapped': [j, j + 1],
                        'sorted_region': list(range(n - i, n)),
                        'comparisons': self.comparisons,
                        'swaps': self.swaps,
                        'time_ms': self.get_elapsed_time_ms(),
                        'message': f'Swapped {arr[j + 1]} and {arr[j]}! Array now: {arr}',
                        'step_type': 'swap'
                    }

            # Early termination - if no swaps occurred, array is sorted
            if not swapped:
                break

        # Final sorted state
        yield {
            'array': arr,
            'sorted_region': list(range(n)),
            'comparisons': self.comparisons,
            'swaps': self.swaps,
            'time_ms': self.get_elapsed_time_ms(),
            'message': f'Sorting complete! Made {self.comparisons} comparisons and {self.swaps} swaps.',
            'complete': True,
            'step_type': 'complete'
        }


class MergeSort(SortingAlgorithm):
    """
    Merge Sort implementation with step-by-step visualization.

    Merge sort is a divide-and-conquer algorithm that divides the input array
    into two halves, recursively sorts them, and then merges the sorted halves.

    Algorithm Description:
        1. Divide the unsorted list into n sublists, each containing one element
        2. Repeatedly merge sublists to produce new sorted sublists
        3. Continue until there is only one sublist remaining (the sorted list)

    Time Complexity:
        - Best Case: O(n log n)
        - Average Case: O(n log n)
        - Worst Case: O(n log n) - guaranteed performance!

    Space Complexity: O(n) - requires auxiliary array for merging

    Stability: Yes - maintains relative order of equal elements

    When to use:
        - Large datasets where guaranteed O(n log n) is needed
        - When stability is required
        - External sorting (when data doesn't fit in memory)
        - Linked lists (no random access needed)

    Advantages:
        - Predictable performance (always O(n log n))
        - Stable sorting
        - Works well with sequential access

    Disadvantages:
        - Requires O(n) extra space
        - Slower than quicksort in practice for arrays
    """

    def sort(self, arr: List[int]) -> Generator[Dict[str, Any], None, None]:
        """
        Sort array using merge sort, yielding visualization states.

        Args:
            arr: List of integers to sort

        Yields:
            dict: State information for visualization
        """
        self.reset_stats()
        arr = arr.copy()

        # Yield initial state
        yield {
            'array': arr.copy(),
            'message': 'Starting Merge Sort - will divide and conquer!',
            'comparisons': 0,
            'swaps': 0,
            'time_ms': self.get_elapsed_time_ms(),
            'step_type': 'start'
        }

        # Perform merge sort and yield from recursive calls
        yield from self._merge_sort_recursive(arr, 0, len(arr) - 1)

        # Final sorted state
        yield {
            'array': arr,
            'sorted_region': list(range(len(arr))),
            'message': f'Merge Sort complete! Made {self.comparisons} comparisons.',
            'comparisons': self.comparisons,
            'time_ms': self.get_elapsed_time_ms(),
            'complete': True,
            'step_type': 'complete'
        }

    def _merge_sort_recursive(self, arr: List[int], left: int, right: int) -> Generator:
        """
        Recursive helper for merge sort.

        Args:
            arr: The array being sorted (modified in place)
            left: Left boundary of current subarray
            right: Right boundary of current subarray

        Yields:
            dict: Visualization states during divide and merge
        """
        if left < right:
            mid = (left + right) // 2

            # Yield division step
            yield {
                'array': arr.copy(),
                'dividing': list(range(left, right + 1)),
                'message': f'Dividing range [{left}:{right}] at index {mid}',
                'comparisons': self.comparisons,
                'time_ms': self.get_elapsed_time_ms(),
                'step_type': 'divide'
            }

            # Recursively sort left half
            yield from self._merge_sort_recursive(arr, left, mid)

            # Recursively sort right half
            yield from self._merge_sort_recursive(arr, mid + 1, right)

            # Merge the sorted halves
            yield from self._merge(arr, left, mid, right)

    def _merge(self, arr: List[int], left: int, mid: int, right: int) -> Generator:
        """
        Merge two sorted subarrays into one sorted subarray.

        Args:
            arr: The array containing both subarrays
            left: Start of first subarray
            mid: End of first subarray
            right: End of second subarray

        Yields:
            dict: States during the merge process
        """
        # Create copies of the two subarrays to merge
        left_arr = arr[left:mid + 1]
        right_arr = arr[mid + 1:right + 1]

        i = j = 0  # Pointers for left_arr and right_arr
        k = left  # Pointer for merged array

        # Merge the two arrays
        while i < len(left_arr) and j < len(right_arr):
            self.comparisons += 1

            if left_arr[i] <= right_arr[j]:
                arr[k] = left_arr[i]
                i += 1
            else:
                arr[k] = right_arr[j]
                j += 1
            k += 1

            # Yield state showing merge progress
            yield {
                'array': arr.copy(),
                'merging': list(range(left, right + 1)),
                'message': f'Merging subarrays [{left}:{mid}] and [{mid + 1}:{right}]',
                'comparisons': self.comparisons,
                'time_ms': self.get_elapsed_time_ms(),
                'step_type': 'merge'
            }

        # Copy remaining elements from left_arr (if any)
        while i < len(left_arr):
            arr[k] = left_arr[i]
            i += 1
            k += 1

        # Copy remaining elements from right_arr (if any)
        while j < len(right_arr):
            arr[k] = right_arr[j]
            j += 1
            k += 1


class QuickSort(SortingAlgorithm):
    """
    Quick Sort implementation with step-by-step visualization.

    Quick sort is a divide-and-conquer algorithm that picks a pivot element
    and partitions the surrounding array, then recursively sorts the partitions.

    Algorithm Description:
        1. Choose a pivot element from the array
        2. Partition: rearrange array so elements less than pivot come before it,
           and elements greater come after it
        3. Recursively apply above steps to sub-arrays

    Time Complexity:
        - Best Case: O(n log n) when pivot divides array evenly
        - Average Case: O(n log n)
        - Worst Case: O(n²) when pivot is always smallest/largest element
                      (rare with good pivot selection)

    Space Complexity: O(log n) - recursion stack space

    Stability: No - does not maintain relative order of equal elements

    When to use:
        - Large datasets where average-case performance is sufficient
        - When in-place sorting is needed (low memory usage)
        - When stability is not required
        - General-purpose sorting (often fastest in practice)

    Advantages:
        - Very fast in practice (faster than merge sort for arrays)
        - In-place sorting (uses minimal extra memory)
        - Cache-friendly (good locality of reference)

    Disadvantages:
        - Worst-case O(n²) (though rare with random pivots)
        - Not stable
        - Recursive (can cause stack overflow for huge arrays)
    """

    def sort(self, arr: List[int]) -> Generator[Dict[str, Any], None, None]:
        """
        Sort array using quick sort, yielding visualization states.

        Args:
            arr: List of integers to sort

        Yields:
            dict: State information for visualization
        """
        self.reset_stats()
        arr = arr.copy()

        # Yield initial state
        yield {
            'array': arr.copy(),
            'message': 'Starting Quick Sort - will partition around pivots!',
            'comparisons': 0,
            'swaps': 0,
            'time_ms': self.get_elapsed_time_ms(),
            'step_type': 'start'
        }

        # Perform quick sort
        yield from self._quick_sort_recursive(arr, 0, len(arr) - 1)

        # Final sorted state
        yield {
            'array': arr,
            'sorted_region': list(range(len(arr))),
            'message': f'Quick Sort complete! Made {self.comparisons} comparisons and {self.swaps} swaps.',
            'comparisons': self.comparisons,
            'swaps': self.swaps,
            'time_ms': self.get_elapsed_time_ms(),
            'complete': True,
            'step_type': 'complete'
        }

    def _quick_sort_recursive(self, arr: List[int], low: int, high: int) -> Generator:
        """
        Recursive helper for quick sort.

        Args:
            arr: The array being sorted (modified in place)
            low: Starting index of partition
            high: Ending index of partition

        Yields:
            dict: Visualization states during partitioning and recursion
        """
        if low < high:
            # Partition array and get pivot index
            # We need to consume the generator and capture the return value
            partition_generator = self._partition(arr, low, high)
            pivot_index = None

            try:
                # Yield all steps from partition
                while True:
                    yield next(partition_generator)
            except StopIteration as e:
                # When generator ends, capture the return value
                pivot_index = e.value

            # Recursively sort elements before and after partition
            if pivot_index is not None:
                yield from self._quick_sort_recursive(arr, low, pivot_index - 1)
                yield from self._quick_sort_recursive(arr, pivot_index + 1, high)

    def _partition(self, arr: List[int], low: int, high: int) -> Generator:
        """
        Partition array around pivot (last element).

        After partitioning:
        - Elements less than pivot are on the left
        - Elements greater than pivot are on the right
        - Pivot is in its final sorted position

        Args:
            arr: The array to partition
            low: Starting index
            high: Ending index (pivot element)

        Yields:
            dict: States during partitioning

        Returns:
            int: Final position of the pivot element
        """
        pivot = arr[high]  # Choose last element as pivot
        i = low - 1  # Index of smaller element

        # Yield state showing pivot selection
        yield {
            'array': arr.copy(),
            'pivot': high,
            'message': f'Selected pivot: {pivot} at index {high}',
            'comparisons': self.comparisons,
            'swaps': self.swaps,
            'time_ms': self.get_elapsed_time_ms(),
            'step_type': 'pivot'
        }

        # Compare each element with pivot
        for j in range(low, high):
            self.comparisons += 1

            # Yield comparison state
            yield {
                'array': arr.copy(),
                'pivot': high,
                'comparing': [j, high],  # Make it an array like BubbleSort
                'message': f'Comparing {arr[j]} with pivot {pivot}',
                'comparisons': self.comparisons,
                'swaps': self.swaps,
                'time_ms': self.get_elapsed_time_ms(),
                'step_type': 'compare'
            }

            # If current element is smaller than pivot, swap it
            if arr[j] < pivot:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
                self.swaps += 1

                # Yield swap state
                yield {
                    'array': arr.copy(),
                    'swapped': [i, j],
                    'pivot': high,
                    'message': f'Swapped {arr[j]} and {arr[i]} (both less than pivot)',
                    'comparisons': self.comparisons,
                    'swaps': self.swaps,
                    'time_ms': self.get_elapsed_time_ms(),
                    'step_type': 'swap'
                }

        # Place pivot in its final position
        arr[i + 1], arr[high] = arr[high], arr[i + 1]
        self.swaps += 1

        # Yield final partition state
        yield {
            'array': arr.copy(),
            'swapped': [i + 1, high],
            'message': f'Placed pivot {pivot} in final position at index {i + 1}',
            'comparisons': self.comparisons,
            'swaps': self.swaps,
            'time_ms': self.get_elapsed_time_ms(),
            'step_type': 'partition_complete'
        }

        return i + 1