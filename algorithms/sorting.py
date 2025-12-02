"""
Sorting algorithm implementations with step-by-step visualization.

Why this file exists: This is the core of the whole project - implementing
classic sorting algorithms from scratch (not just calling Python's sorted()).

Implementation challenge: The tricky part was making these algorithms PAUSABLE
for visualization. Normal sorting functions just return the sorted array, but
I needed to show every comparison and swap as it happens. This required using
Python generators (yield instead of return), which took me a while to get right.

Originally tried
making the algorithms return a list of all states, but that used too much memory
for large arrays and didn't allow streaming the visualization.

All three algorithms share a common pattern:
1. Inherit from SortingAlgorithm base class (for stat tracking)
2. Implement sort() as a generator function
3. Yield state dicts showing current array, what we're comparing, etc.
4. Track comparisons and swaps for performance analysis

"""
from typing import List, Dict, Any, Generator
import time


class SortingAlgorithm:
    """
    Base class for all sorting algorithms - avoids code duplication.

    Why a base class: All three sorting algorithms need to track the same stats
    (comparisons, swaps, execution time). Rather than copy-paste this code three
    times, I put it in a base class and inherit from it.

    """

    def __init__(self):
        """
        Initialize performance tracking counters.

        These counters let us measure how much work the algorithm does:
        - comparisons: How many times do we check if a < b?
        - swaps: How many times do we exchange two elements?
        - start_time: When did we start? (for measuring execution time)

        All start at zero/None and get reset each time sort() is called.
        """
        self.comparisons = 0  # Total element comparisons made
        self.swaps = 0  # Total element swaps made
        self.start_time = None  # Timestamp when sorting started

    def reset_stats(self):
        """
        Reset all counters before starting a new sort.

        Why this matters: If we don't reset, stats from previous sorts accumulate,
        and we get wrong totals. Took me a while to debug this - was seeing
        comparison counts in the thousands for a 10-element array until I realized
        I forgot to reset between test runs!

        """
        self.comparisons = 0
        self.swaps = 0
        self.start_time = time.time()  # Get current timestamp

    def get_elapsed_time_ms(self):
        """
        Calculate how long the algorithm has been running.

        Returns:
            float: Milliseconds elapsed since reset_stats() was called.
                   Returns 0.0 if sorting hasn't started yet.

        Implementation note: time.time() returns seconds as a float, so we
        multiply by 1000 to convert to milliseconds.
        """
        if self.start_time is None:
            return 0.0  # Haven't started yet
        return (time.time() - self.start_time) * 1000


class BubbleSort(SortingAlgorithm):
    """
    Bubble Sort - the simplest sorting algorithm (and usually the slowest).

    The basic idea: Repeatedly step through the array, compare adjacent elements,
    and swap them if they're in the wrong order. Each pass "bubbles" the largest
    unsorted element to its final position at the end of the array.

    """

    def sort(self, arr: List[int]) -> Generator[Dict[str, Any], None, None]:
        """
        Sort array using bubble sort, yielding state at each step for visualization.

        Generator pattern: This function YIELDS instead of RETURNING. Each yield
        pauses execution and sends a state dictionary to the caller. The caller
        (visualization code) can then display that state and request the next one.

        Why generators instead of returning a list of states:
        1. Memory efficient: Don't need to store all states in memory at once
        2. Streaming: Can start visualizing before algorithm finishes
        3. Lazy evaluation: Only compute states as needed

        The state dictionary we yield contains everything needed for visualization:
        - array: Current state of the array (always a COPY, never reference)
        - comparing: Which indices we're currently comparing
        - swapped: Which indices just got swapped
        - sorted_region: Which indices are in their final position
        - comparisons/swaps: Running totals
        - message: Human-readable description

        Args:
            arr: List of integers to sort (gets COPIED, not modified)

        Yields:
            dict: State information at each significant step

        """
        self.reset_stats()  # Start fresh - zero out counters and start timer
        n = len(arr)

        # CRITICAL: Copy the array so we don't modify the original
        # If we didn't copy, the user's original array would get sorted as a side
        # effect, which violates the principle of least surprise. Plus, we need
        # to yield copies of the array at each step anyway.
        arr = arr.copy()

        # Outer loop: Each iteration bubbles one element to its final position
        # After i iterations, the last i elements are in their final sorted positions
        for i in range(n):
            # Track if we made any swaps this pass
            # If we don't swap anything, the array is sorted and we can exit early
            swapped = False

            # Inner loop: Compare adjacent pairs
            # Stop at n-i-1 because the last i elements are already in final position
            # Example: If n=5 and i=2, we only need to check indices 0,1,2 (stop at 3)
            # because indices 3 and 4 are already sorted from previous passes
            for j in range(0, n - i - 1):
                self.comparisons += 1  # Count every comparison for stats

                # Yield state showing which two elements we're comparing
                # The visualization can highlight these indices on screen
                yield {
                    'array': arr.copy(),  # MUST copy - visualization needs a snapshot
                    'comparing': [j, j + 1],  # Indices of elements being compared
                    'sorted_region': list(range(n - i, n)),  # Last i elements are done
                    'comparisons': self.comparisons,
                    'swaps': self.swaps,
                    'time_ms': self.get_elapsed_time_ms(),
                    'message': f'Comparing {arr[j]} and {arr[j + 1]}',
                    'step_type': 'compare'  # Helps visualization color-code the step
                }

                # Check if these two elements are in wrong order
                if arr[j] > arr[j + 1]:
                    # Swap using Python's tuple unpacking
                    # More elegant than: temp = arr[j]; arr[j] = arr[j+1]; arr[j+1] = temp
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
                    self.swaps += 1
                    swapped = True  # Remember we made a swap this pass

                    # Yield state showing the swap just happened
                    yield {
                        'array': arr.copy(),
                        'swapped': [j, j + 1],  # Which indices just swapped
                        'sorted_region': list(range(n - i, n)),
                        'comparisons': self.comparisons,
                        'swaps': self.swaps,
                        'time_ms': self.get_elapsed_time_ms(),
                        'message': f'Swapped {arr[j + 1]} and {arr[j]}! Array now: {arr}',
                        'step_type': 'swap'
                    }

            # Early termination optimization: If we went through an entire pass
            # without swapping anything, the array must be sorted already
            # This is what makes best-case complexity O(n) instead of O(n²)
            if not swapped:
                break  # Exit outer loop early

        # Algorithm complete - yield final sorted state
        yield {
            'array': arr,  # Final sorted array
            'sorted_region': list(range(n)),  # All elements are now sorted
            'comparisons': self.comparisons,
            'swaps': self.swaps,
            'time_ms': self.get_elapsed_time_ms(),
            'message': f'Sorting complete! Made {self.comparisons} comparisons and {self.swaps} swaps.',
            'complete': True,  # Signal to visualization that we're done
            'step_type': 'complete'
        }


class MergeSort(SortingAlgorithm):
    """
    Merge Sort - the "divide and conquer" algorithm with guaranteed O(n log n).

    The strategy: Recursively split the array in half until you have arrays of
    size 1 (which are trivially sorted), then merge them back together in sorted
    order. It's like organizing a shuffled deck by splitting it into smaller piles,
    sorting each pile, then merging them back together.

    When NOT to use Merge Sort:
    - Limited memory: O(n) extra space can be prohibitive
    - Small arrays: Overhead of recursion not worth it (use Insertion Sort)
    - Need the fastest average case: Quick Sort is usually faster in practice
    """

    def sort(self, arr: List[int]) -> Generator[Dict[str, Any], None, None]:
        """
        Sort array using merge sort, yielding visualization states.

        The recursive structure makes this harder to visualize than Bubble Sort
        because we need to track what's happening at multiple levels of recursion
        simultaneously. Using "yield from" lets us delegate to recursive calls
        and still capture all their yielded states.

        Args:
            arr: List of integers to sort

        Yields:
            dict: State information showing divide and merge operations
        """
        self.reset_stats()
        arr = arr.copy()  # Don't modify original

        # Yield initial state
        yield {
            'array': arr.copy(),
            'message': 'Starting Merge Sort - will divide and conquer!',
            'comparisons': 0,
            'swaps': 0,  # Merge Sort doesn't really "swap", but we track it anyway
            'time_ms': self.get_elapsed_time_ms(),
            'step_type': 'start'
        }

        # Perform the recursive merge sort
        # "yield from" is CRITICAL here - it yields all values from the generator
        # Without "yield from", we'd just yield the generator object itself!
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
        Recursive divide-and-conquer sorting function.

        This is where the actual algorithm logic lives. We recursively split
        the array in half until we get subarrays of size 1, then merge them
        back together in sorted order.

        Args:
            arr: The array we're sorting (modified in place)
            left: Start index of subarray to sort
            right: End index of subarray to sort (inclusive)

        Yields:
            dict: States showing the divide and merge process
        """
        # Base case: if left >= right, we have 0 or 1 elements (already sorted)
        if left < right:
            # Find middle point to divide array in half
            # Using integer division // to get whole number
            mid = (left + right) // 2

            # Yield state showing we're about to divide this subarray
            yield {
                'array': arr.copy(),
                'dividing': list(range(left, right + 1)),  # Highlight region being divided
                'message': f'Dividing range [{left}:{right}] at index {mid}',
                'comparisons': self.comparisons,
                'time_ms': self.get_elapsed_time_ms(),
                'step_type': 'divide'
            }

            # Recursively sort the left half [left...mid]
            # "yield from" propagates all yields from the recursive call up to our caller
            yield from self._merge_sort_recursive(arr, left, mid)

            # Recursively sort the right half [mid+1...right]
            yield from self._merge_sort_recursive(arr, mid + 1, right)

            # Now that both halves are sorted, merge them together
            yield from self._merge(arr, left, mid, right)

    def _merge(self, arr: List[int], left: int, mid: int, right: int) -> Generator:
        """
        Merge two sorted subarrays into one sorted subarray.

        This is the "conquer" part of divide-and-conquer. We have two sorted
        subarrays ([left...mid] and [mid+1...right]) and need to combine them
        into one sorted subarray.

        The merging algorithm:
        1. Copy both subarrays to temporary arrays
        2. Compare first elements of each temp array
        3. Take the smaller one and put it in the main array
        4. Repeat until one temp array is empty
        5. Copy any remaining elements from the other temp array

        Args:
            arr: The main array containing both subarrays
            left: Start of first sorted subarray
            mid: End of first sorted subarray (start of second is mid+1)
            right: End of second sorted subarray

        Yields:
            dict: States during the merge process
        """
        # Create temporary copies of the two subarrays we're merging
        # Left subarray: arr[left...mid]
        left_arr = arr[left:mid + 1]
        # Right subarray: arr[mid+1...right]
        right_arr = arr[mid + 1:right + 1]

        # Initialize pointers
        i = j = 0  # Pointers for left_arr and right_arr
        k = left   # Pointer for main array (where we're writing merged result)

        # Main merge loop: Compare elements from both subarrays and take smaller one
        # Continues while both subarrays have elements remaining
        while i < len(left_arr) and j < len(right_arr):
            self.comparisons += 1  # Count the comparison

            # Compare current elements from both subarrays
            # "<=" instead of "<" maintains stability (left comes first if equal)
            if left_arr[i] <= right_arr[j]:
                arr[k] = left_arr[i]  # Take from left subarray
                i += 1  # Move left pointer forward
            else:
                arr[k] = right_arr[j]  # Take from right subarray
                j += 1  # Move right pointer forward
            k += 1  # Move main array pointer forward

            # Yield state showing merge in progress
            yield {
                'array': arr.copy(),
                'merging': list(range(left, right + 1)),  # Highlight region being merged
                'message': f'Merging subarrays [{left}:{mid}] and [{mid + 1}:{right}]',
                'comparisons': self.comparisons,
                'time_ms': self.get_elapsed_time_ms(),
                'step_type': 'merge'
            }

        # Copy any remaining elements from left subarray (if any)
        # This happens when right subarray was exhausted first
        while i < len(left_arr):
            arr[k] = left_arr[i]
            i += 1
            k += 1

        # Copy any remaining elements from right subarray (if any)
        # This happens when left subarray was exhausted first
        while j < len(right_arr):
            arr[k] = right_arr[j]
            j += 1
            k += 1


class QuickSort(SortingAlgorithm):
    """
    Quick Sort - usually the fastest sorting algorithm in practice.

    The strategy: Pick a "pivot" element, rearrange the array so elements less
    than pivot come before it and elements greater come after it (partitioning),
    then recursively sort the two partitions.

    WHY IT'S USUALLY O(n log n):
    - Good pivot: If pivot splits array roughly in half each time, we get
      log₂(n) levels of recursion (just like merge sort)
    - Each level does n work (partitioning touches all elements)
    - Total: n × log n = O(n log n)

    WHY IT CAN BE O(n²):
    - Bad pivot: If pivot is always smallest/largest element, we get n levels
      of recursion instead of log n

    When NOT to use Quick Sort:
    - Need guaranteed O(n log n): Use Merge Sort instead
    - Need stability: Use Merge Sort or Timsort
    - Already sorted data: Worst case unless using randomized pivot
    - Critical systems: O(n²) worst case could be catastrophic
    """

    def sort(self, arr: List[int]) -> Generator[Dict[str, Any], None, None]:
        """
        Sort array using quick sort, yielding visualization states.

        The challenge with Quick Sort visualization: Unlike Merge Sort which
        creates new subarrays, Quick Sort partitions in place. This makes it
        more memory-efficient but slightly harder to visualize because we're
        rearranging elements within the same array.

        Args:
            arr: List of integers to sort

        Yields:
            dict: State information showing partitioning and recursion
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

        # Perform the recursive quick sort
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
        Recursive quick sort implementation.

        This follows the standard Quick Sort algorithm: partition, then recursively
        sort the two partitions.

        GENERATOR RETURN VALUE CHALLENGE: This was tricky! Python generators can
        RETURN a value (not just yield), but accessing that value requires catching
        StopIteration. The _partition generator returns the pivot index, which we
        need for the recursive calls.

        Args:
            arr: Array being sorted (modified in place)
            low: Start of partition to sort
            high: End of partition to sort

        Yields:
            dict: States during partitioning and recursion

        Base case: low >= high means partition has 0 or 1 elements (sorted)
        """
        # Base case: partition is empty or has one element
        if low < high:
            # Partition the array and get the pivot's final position
            # This part took me a while to figure out - generators can return values!
            partition_generator = self._partition(arr, low, high)
            pivot_index = None

            try:
                # Yield all visualization states from partitioning
                while True:
                    yield next(partition_generator)
            except StopIteration as e:
                # When the generator ends, it returns the pivot index via exception
                # This is Python's way of returning from a generator
                pivot_index = e.value

            # Now recursively sort the two partitions
            # Everything before pivot is less than pivot
            # Everything after pivot is greater than pivot
            # Pivot itself is in its final sorted position
            if pivot_index is not None:
                yield from self._quick_sort_recursive(arr, low, pivot_index - 1)
                yield from self._quick_sort_recursive(arr, pivot_index + 1, high)

    def _partition(self, arr: List[int], low: int, high: int) -> Generator:
        """
        Partition array around pivot (Lomuto partition scheme).

        How it works:
        - i tracks the "boundary" between small and large elements
        - j scans through the array
        - When we find element < pivot, swap it to the left side and increment i
        - At the end, swap pivot into its final position

        Args:
            arr: Array to partition
            low: Start of partition
            high: End of partition (contains pivot)

        Yields:
            dict: States during partitioning process

        Returns:
            int: Final index where pivot ended up (via StopIteration.value)
        """
        # Choose last element as pivot (simple but not optimal)
        # Better implementations use median-of-three or random pivot
        pivot = arr[high]

        # i is the index of the last element we know is < pivot
        # Starts at low-1 because we haven't found any yet
        i = low - 1

        # Yield state showing we selected this pivot
        yield {
            'array': arr.copy(),
            'pivot': high,
            'message': f'Selected pivot: {pivot} at index {high}',
            'comparisons': self.comparisons,
            'swaps': self.swaps,
            'time_ms': self.get_elapsed_time_ms(),
            'step_type': 'pivot'
        }

        # Scan through partition (excluding pivot)
        for j in range(low, high):
            self.comparisons += 1  # Count comparison

            # Yield state showing comparison
            yield {
                'array': arr.copy(),
                'pivot': high,
                'comparing': [j, high],  # Comparing current element to pivot
                'message': f'Comparing {arr[j]} with pivot {pivot}',
                'comparisons': self.comparisons,
                'swaps': self.swaps,
                'time_ms': self.get_elapsed_time_ms(),
                'step_type': 'compare'
            }

            # If element is smaller than pivot, move it to left partition
            if arr[j] < pivot:
                i += 1  # Expand the "small elements" region
                # Swap current element with first element in "large" region
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

        # Put pivot in its final position
        # i+1 is the first element >= pivot, so swap pivot there
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

        # Return pivot's final index
        # This gets accessed via StopIteration.value in the recursive function
        return i + 1