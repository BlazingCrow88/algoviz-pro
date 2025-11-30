"""
Unit tests for algorithm implementations.

Tests sorting and searching algorithms for correctness and edge cases.
Ensures algorithms handle defensive programming scenarios including
empty arrays, single elements, duplicates, and worst-case inputs.
"""
from django.test import TestCase
from algorithms.sorting import BubbleSort, MergeSort, QuickSort
from algorithms.searching import BinarySearch, LinearSearch


class SortingAlgorithmTests(TestCase):
    """
    Test all sorting algorithms for correctness and edge cases.

    Each sorting algorithm must handle:
    - Standard cases (unsorted arrays)
    - Edge cases (empty, single element)
    - Best cases (already sorted)
    - Worst cases (reverse sorted)
    - Duplicate values (stability considerations)
    """

    def test_bubble_sort_correctness(self):
        """
        Verify bubble sort produces correctly sorted output.

        Tests basic functionality with a standard unsorted array
        to ensure the algorithm's comparison and swap logic works.
        """
        sorter = BubbleSort()
        result = list(sorter.sort([5, 2, 8, 1, 9]))
        final_array = result[-1]['array']
        self.assertEqual(final_array, [1, 2, 5, 8, 9])

    def test_merge_sort_correctness(self):
        """
        Verify merge sort produces correctly sorted output.

        Tests the divide-and-conquer approach with a standard
        unsorted array to ensure merge logic is correct.
        """
        sorter = MergeSort()
        result = list(sorter.sort([5, 2, 8, 1, 9]))
        final_array = result[-1]['array']
        self.assertEqual(final_array, [1, 2, 5, 8, 9])

    def test_quick_sort_correctness(self):
        """
        Verify quick sort produces correctly sorted output.

        Tests the partition-based approach to ensure pivot selection
        and partitioning logic works correctly.
        """
        sorter = QuickSort()
        result = list(sorter.sort([5, 2, 8, 1, 9]))
        final_array = result[-1]['array']
        self.assertEqual(final_array, [1, 2, 5, 8, 9])

    def test_empty_array(self):
        """
        Test empty array handling (critical edge case).

        Empty arrays are a common edge case that can cause index errors
        if not handled properly. This ensures defensive programming and
        that the algorithm doesn't crash when given no input.
        """
        sorter = BubbleSort()
        result = list(sorter.sort([]))
        self.assertIsNotNone(result)
        self.assertTrue(len(result) > 0)

    def test_single_element(self):
        """
        Test single-element array (trivial base case).

        Single elements are already sorted and represent the simplest
        valid input. This tests that the algorithm handles the base
        case without unnecessary operations.
        """
        sorter = BubbleSort()
        result = list(sorter.sort([42]))
        final_array = result[-1]['array']
        self.assertEqual(final_array, [42])

    def test_already_sorted(self):
        """
        Test already-sorted array (best-case scenario).

        Tests bubble sort's early termination optimization. When the
        array is already sorted, no swaps should occur and the algorithm
        should exit early, demonstrating O(n) best-case performance.
        """
        sorter = BubbleSort()
        result = list(sorter.sort([1, 2, 3, 4, 5]))
        final_array = result[-1]['array']
        self.assertEqual(final_array, [1, 2, 3, 4, 5])

    def test_reverse_sorted(self):
        """
        Test reverse-sorted array (worst-case scenario).

        Reverse-sorted arrays represent the worst case for many algorithms,
        requiring maximum comparisons and swaps. This ensures the algorithm
        handles the most challenging input correctly.
        """
        sorter = QuickSort()
        result = list(sorter.sort([5, 4, 3, 2, 1]))
        final_array = result[-1]['array']
        self.assertEqual(final_array, [1, 2, 3, 4, 5])

    def test_duplicates(self):
        """
        Test array with duplicate values (stability test).

        Duplicate values test whether the algorithm handles equal elements
        correctly. For stable sorts like merge sort, this verifies that
        relative order of equal elements is preserved.
        """
        sorter = MergeSort()
        result = list(sorter.sort([5, 2, 5, 1, 2]))
        final_array = result[-1]['array']
        self.assertEqual(final_array, [1, 2, 2, 5, 5])

    def test_large_array(self):
        """
        Test with larger dataset (performance validation).

        Ensures the algorithm scales correctly with input size and
        doesn't have implementation bugs that only appear with larger
        datasets (e.g., stack overflow, memory issues).
        """
        sorter = MergeSort()
        large_array = list(range(100, 0, -1))  # 100 elements in reverse order
        result = list(sorter.sort(large_array))
        final_array = result[-1]['array']
        self.assertEqual(final_array, list(range(1, 101)))


class SearchingAlgorithmTests(TestCase):
    """
    Test searching algorithms for correctness and edge cases.

    Validates both binary search (requires sorted input) and linear search
    (works on any input) with various scenarios to ensure robust implementation.
    """

    def test_binary_search_found(self):
        """
        Test binary search successfully finds target in middle of array.

        Verifies the divide-and-conquer search logic works correctly
        when the target exists in the sorted array.
        """
        searcher = BinarySearch()
        result = list(searcher.search([1, 2, 5, 8, 9], 5))
        final_state = result[-1]
        self.assertTrue(final_state['found'])
        self.assertEqual(final_state['found_index'], 2)

    def test_binary_search_not_found(self):
        """
        Test binary search when target doesn't exist.

        Ensures the algorithm correctly reports when a value is not
        present, rather than returning incorrect results or crashing.
        """
        searcher = BinarySearch()
        result = list(searcher.search([1, 2, 5, 8, 9], 7))
        final_state = result[-1]
        self.assertFalse(final_state['found'])

    def test_binary_search_first_element(self):
        """
        Test binary search finds first element (edge case).

        First element is an edge case that tests boundary handling
        in the binary search logic (left boundary condition).
        """
        searcher = BinarySearch()
        result = list(searcher.search([1, 2, 5, 8, 9], 1))
        final_state = result[-1]
        self.assertTrue(final_state['found'])
        self.assertEqual(final_state['found_index'], 0)

    def test_binary_search_last_element(self):
        """
        Test binary search finds last element (edge case).

        Last element tests the right boundary handling in binary search,
        ensuring the algorithm doesn't miss edge values.
        """
        searcher = BinarySearch()
        result = list(searcher.search([1, 2, 5, 8, 9], 9))
        final_state = result[-1]
        self.assertTrue(final_state['found'])
        self.assertEqual(final_state['found_index'], 4)

    def test_linear_search_found(self):
        """
        Test linear search finds target in unsorted array.

        Verifies basic linear search functionality with unsorted data,
        demonstrating that it works without requiring sorted input.
        """
        searcher = LinearSearch()
        result = list(searcher.search([5, 2, 8, 1, 9], 8))
        final_state = result[-1]
        self.assertTrue(final_state['found'])
        self.assertEqual(final_state['found_index'], 2)

    def test_linear_search_not_found(self):
        """
        Test linear search when target is absent.

        Ensures linear search correctly reports when searching for
        a value that doesn't exist in the array.
        """
        searcher = LinearSearch()
        result = list(searcher.search([5, 2, 8, 1, 9], 7))
        final_state = result[-1]
        self.assertFalse(final_state['found'])

    def test_linear_search_unsorted(self):
        """
        Test linear search works on unsorted arrays.

        Unlike binary search, linear search doesn't require sorted input.
        This demonstrates its key advantage for unsorted data.
        """
        searcher = LinearSearch()
        result = list(searcher.search([9, 1, 5, 2, 8], 5))
        final_state = result[-1]
        self.assertTrue(final_state['found'])

    def test_search_comparison_counts(self):
        """
        Verify binary search is more efficient than linear search.

        Tests that binary search (O(log n)) makes fewer comparisons
        than linear search (O(n)), demonstrating the performance
        difference between the two algorithms.
        """
        binary = BinarySearch()
        linear = LinearSearch()

        arr = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        binary_result = list(binary.search(arr, 10))
        linear_result = list(linear.search(arr, 10))

        binary_comps = binary_result[-1]['comparisons']
        linear_comps = linear_result[-1]['comparisons']

        # Binary should use fewer comparisons (O(log n) vs O(n))
        self.assertLess(binary_comps, linear_comps)