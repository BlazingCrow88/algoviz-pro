"""
Sorting algorithm implementations with step-by-step visualization.

Implementation challenge: Made algorithms PAUSABLE for visualization using Python
generators (yield). Originally tried returning list of all states, but that used
too much memory. Generators allow streaming visualization as algorithm runs.

All algorithms share common pattern:
1. Inherit from SortingAlgorithm (stat tracking)
2. Implement sort() as generator
3. Yield state dicts for visualization
4. Track comparisons and swaps
"""
from typing import List, Dict, Any, Generator
import time


class SortingAlgorithm:
    """
    Base class for sorting algorithms.

    Why a base class: All algorithms need same stat tracking (comparisons,
    swaps, execution time). Avoids duplicating this code three times.
    """

    def __init__(self):
        """Initialize performance tracking counters."""
        self.comparisons = 0
        self.swaps = 0
        self.start_time = None

    def reset_stats(self):
        """
        Reset counters before starting new sort.

        Without resetting, stats from previous sorts accumulate. Discovered
        this bug during testing when seeing thousands of comparisons for
        10-element arrays!
        """
        self.comparisons = 0
        self.swaps = 0
        self.start_time = time.time()

    def get_elapsed_time_ms(self):
        """Calculate milliseconds elapsed since sorting started."""
        if self.start_time is None:
            return 0.0
        return (time.time() - self.start_time) * 1000


class BubbleSort(SortingAlgorithm):
    """
    Bubble Sort - simplest sorting algorithm.

    Algorithm: Repeatedly step through array, compare adjacent elements,
    swap if wrong order. Each pass bubbles largest unsorted element to end.

    Time Complexity: O(n²) average/worst, O(n) best (already sorted)
    Space Complexity: O(1)
    """

    def sort(self, arr: List[int]) -> Generator[Dict[str, Any], None, None]:
        """
        Sort array using bubble sort, yielding states for visualization.

        Why generators: Memory efficient, allows streaming visualization,
        only computes states as needed.

        Args:
            arr: List to sort (gets copied, not modified)

        Yields:
            dict: State showing array, comparing indices, swaps, stats
        """
        self.reset_stats()
        n = len(arr)
        arr = arr.copy()  # Don't modify original

        for i in range(n):
            swapped = False  # Track if any swaps this pass

            # Only check up to n-i-1 because last i elements already sorted
            for j in range(0, n - i - 1):
                self.comparisons += 1

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

                if arr[j] > arr[j + 1]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
                    self.swaps += 1
                    swapped = True

                    yield {
                        'array': arr.copy(),
                        'swapped': [j, j + 1],
                        'sorted_region': list(range(n - i, n)),
                        'comparisons': self.comparisons,
                        'swaps': self.swaps,
                        'time_ms': self.get_elapsed_time_ms(),
                        'message': f'Swapped {arr[j + 1]} and {arr[j]}',
                        'step_type': 'swap'
                    }

            # Early termination: no swaps means array is sorted
            if not swapped:
                break

        yield {
            'array': arr,
            'sorted_region': list(range(n)),
            'comparisons': self.comparisons,
            'swaps': self.swaps,
            'time_ms': self.get_elapsed_time_ms(),
            'message': f'Complete! {self.comparisons} comparisons, {self.swaps} swaps',
            'complete': True,
            'step_type': 'complete'
        }


class MergeSort(SortingAlgorithm):
    """
    Merge Sort - divide and conquer with guaranteed O(n log n).

    Algorithm: Recursively split array in half until size 1, then merge back
    together in sorted order.

    Time Complexity: O(n log n) all cases
    Space Complexity: O(n) - requires extra memory for merging

    Trade-offs: Guaranteed performance but needs extra memory. Not ideal for
    small arrays (recursion overhead) or memory-constrained systems.
    """

    def sort(self, arr: List[int]) -> Generator[Dict[str, Any], None, None]:
        """
        Sort array using merge sort, yielding visualization states.

        Uses "yield from" to delegate to recursive calls and capture all their states.
        """
        self.reset_stats()
        arr = arr.copy()

        yield {
            'array': arr.copy(),
            'message': 'Starting Merge Sort',
            'comparisons': 0,
            'swaps': 0,
            'time_ms': self.get_elapsed_time_ms(),
            'step_type': 'start'
        }

        yield from self._merge_sort_recursive(arr, 0, len(arr) - 1)

        yield {
            'array': arr,
            'sorted_region': list(range(len(arr))),
            'message': f'Complete! {self.comparisons} comparisons',
            'comparisons': self.comparisons,
            'time_ms': self.get_elapsed_time_ms(),
            'complete': True,
            'step_type': 'complete'
        }

    def _merge_sort_recursive(self, arr: List[int], left: int, right: int) -> Generator:
        """
        Recursive divide-and-conquer sorting.

        Split array in half until size 1, then merge back in sorted order.
        """
        if left < right:
            mid = (left + right) // 2

            yield {
                'array': arr.copy(),
                'dividing': list(range(left, right + 1)),
                'message': f'Dividing [{left}:{right}] at {mid}',
                'comparisons': self.comparisons,
                'time_ms': self.get_elapsed_time_ms(),
                'step_type': 'divide'
            }

            # Sort left and right halves
            yield from self._merge_sort_recursive(arr, left, mid)
            yield from self._merge_sort_recursive(arr, mid + 1, right)

            # Merge sorted halves
            yield from self._merge(arr, left, mid, right)

    def _merge(self, arr: List[int], left: int, mid: int, right: int) -> Generator:
        """
        Merge two sorted subarrays into one.

        Compares first elements of each subarray, takes smaller one, repeats
        until one subarray exhausted, then copies remaining elements.
        """
        left_arr = arr[left:mid + 1]
        right_arr = arr[mid + 1:right + 1]

        i = j = 0
        k = left

        while i < len(left_arr) and j < len(right_arr):
            self.comparisons += 1

            # Use <= instead of < to maintain stability
            if left_arr[i] <= right_arr[j]:
                arr[k] = left_arr[i]
                i += 1
            else:
                arr[k] = right_arr[j]
                j += 1
            k += 1

            yield {
                'array': arr.copy(),
                'merging': list(range(left, right + 1)),
                'message': f'Merging [{left}:{mid}] and [{mid + 1}:{right}]',
                'comparisons': self.comparisons,
                'time_ms': self.get_elapsed_time_ms(),
                'step_type': 'merge'
            }

        # Copy remaining elements
        while i < len(left_arr):
            arr[k] = left_arr[i]
            i += 1
            k += 1

        while j < len(right_arr):
            arr[k] = right_arr[j]
            j += 1
            k += 1


class QuickSort(SortingAlgorithm):
    """
    Quick Sort - usually fastest in practice.

    Algorithm: Pick pivot, partition array so elements < pivot come before and
    elements > pivot come after, recursively sort partitions.

    Time Complexity:
    - Average: O(n log n) when pivot splits array roughly in half
    - Worst: O(n²) when pivot is always smallest/largest (already sorted data)

    Space Complexity: O(log n) for recursion stack

    Trade-offs: Fast average case but unpredictable worst case. Not stable.
    Use when speed matters more than guaranteed performance.
    """

    def sort(self, arr: List[int]) -> Generator[Dict[str, Any], None, None]:
        """
        Sort array using quick sort, yielding visualization states.

        Partitions in place (unlike merge sort which creates subarrays).
        """
        self.reset_stats()
        arr = arr.copy()

        yield {
            'array': arr.copy(),
            'message': 'Starting Quick Sort',
            'comparisons': 0,
            'swaps': 0,
            'time_ms': self.get_elapsed_time_ms(),
            'step_type': 'start'
        }

        yield from self._quick_sort_recursive(arr, 0, len(arr) - 1)

        yield {
            'array': arr,
            'sorted_region': list(range(len(arr))),
            'message': f'Complete! {self.comparisons} comparisons, {self.swaps} swaps',
            'comparisons': self.comparisons,
            'swaps': self.swaps,
            'time_ms': self.get_elapsed_time_ms(),
            'complete': True,
            'step_type': 'complete'
        }

    def _quick_sort_recursive(self, arr: List[int], low: int, high: int) -> Generator:
        """
        Recursive quick sort: partition, then sort partitions.

        Generator return value handling: Partition generator returns pivot index
        via StopIteration.value when it ends.
        """
        if low < high:
            partition_generator = self._partition(arr, low, high)
            pivot_index = None

            try:
                while True:
                    yield next(partition_generator)
            except StopIteration as e:
                # Pivot index returned via exception
                pivot_index = e.value

            if pivot_index is not None:
                # Sort partitions (pivot already in final position)
                yield from self._quick_sort_recursive(arr, low, pivot_index - 1)
                yield from self._quick_sort_recursive(arr, pivot_index + 1, high)

    def _partition(self, arr: List[int], low: int, high: int) -> Generator:
        """
        Partition array around pivot (Lomuto scheme).

        Algorithm: i tracks boundary between small and large elements. When
        element < pivot found, swap to left side and increment i. Finally,
        swap pivot into position.

        Returns pivot's final index via StopIteration.value.
        """
        pivot = arr[high]  # Use last element as pivot
        i = low - 1  # Index of last element known to be < pivot

        yield {
            'array': arr.copy(),
            'pivot': high,
            'message': f'Selected pivot: {pivot}',
            'comparisons': self.comparisons,
            'swaps': self.swaps,
            'time_ms': self.get_elapsed_time_ms(),
            'step_type': 'pivot'
        }

        for j in range(low, high):
            self.comparisons += 1

            yield {
                'array': arr.copy(),
                'pivot': high,
                'comparing': [j, high],
                'message': f'Comparing {arr[j]} with pivot {pivot}',
                'comparisons': self.comparisons,
                'swaps': self.swaps,
                'time_ms': self.get_elapsed_time_ms(),
                'step_type': 'compare'
            }

            if arr[j] < pivot:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
                self.swaps += 1

                yield {
                    'array': arr.copy(),
                    'swapped': [i, j],
                    'pivot': high,
                    'message': f'Swapped {arr[j]} and {arr[i]}',
                    'comparisons': self.comparisons,
                    'swaps': self.swaps,
                    'time_ms': self.get_elapsed_time_ms(),
                    'step_type': 'swap'
                }

        # Place pivot in final position
        arr[i + 1], arr[high] = arr[high], arr[i + 1]
        self.swaps += 1

        yield {
            'array': arr.copy(),
            'swapped': [i + 1, high],
            'message': f'Pivot {pivot} in final position at {i + 1}',
            'comparisons': self.comparisons,
            'swaps': self.swaps,
            'time_ms': self.get_elapsed_time_ms(),
            'step_type': 'partition_complete'
        }

        return i + 1