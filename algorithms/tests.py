"""
Unit tests for algorithm implementations.

Tests sorting and searching algorithms for correctness and edge cases.
"""
from django.test import TestCase
from algorithms.sorting import BubbleSort, MergeSort, QuickSort
from algorithms.searching import BinarySearch, LinearSearch


class SortingAlgorithmTests(TestCase):
    """Test all sorting algorithms."""

    def test_bubble_sort_correctness(self):
        """Bubble sort produces correct sorted array."""
        sorter = BubbleSort()
        result = list(sorter.sort([5, 2, 8, 1, 9]))
        final_array = result[-1]['array']
        self.assertEqual(final_array, [1, 2, 5, 8, 9])

    def test_merge_sort_correctness(self):
        """Merge sort produces correct sorted array."""
        sorter = MergeSort()
        result = list(sorter.sort([5, 2, 8, 1, 9]))
        final_array = result[-1]['array']
        self.assertEqual(final_array, [1, 2, 5, 8, 9])

    def test_quick_sort_correctness(self):
        """Quick sort produces correct sorted array."""
        sorter = QuickSort()
        result = list(sorter.sort([5, 2, 8, 1, 9]))
        final_array = result[-1]['array']
        self.assertEqual(final_array, [1, 2, 5, 8, 9])

    def test_empty_array(self):
        """Sorting empty array doesn't crash."""
        sorter = BubbleSort()
        result = list(sorter.sort([]))
        self.assertIsNotNone(result)
        self.assertTrue(len(result) > 0)

    def test_single_element(self):
        """Sorting single element works correctly."""
        sorter = BubbleSort()
        result = list(sorter.sort([42]))
        final_array = result[-1]['array']
        self.assertEqual(final_array, [42])

    def test_already_sorted(self):
        """Already sorted array remains sorted."""
        sorter = BubbleSort()
        result = list(sorter.sort([1, 2, 3, 4, 5]))
        final_array = result[-1]['array']
        self.assertEqual(final_array, [1, 2, 3, 4, 5])

    def test_reverse_sorted(self):
        """Reverse sorted array (worst case) works."""
        sorter = QuickSort()
        result = list(sorter.sort([5, 4, 3, 2, 1]))
        final_array = result[-1]['array']
        self.assertEqual(final_array, [1, 2, 3, 4, 5])

    def test_duplicates(self):
        """Handles duplicate values correctly."""
        sorter = MergeSort()
        result = list(sorter.sort([5, 2, 5, 1, 2]))
        final_array = result[-1]['array']
        self.assertEqual(final_array, [1, 2, 2, 5, 5])

    def test_large_array(self):
        """Handles larger arrays (performance test)."""
        sorter = MergeSort()
        large_array = list(range(100, 0, -1))  # 100 to 1
        result = list(sorter.sort(large_array))
        final_array = result[-1]['array']
        self.assertEqual(final_array, list(range(1, 101)))


class SearchingAlgorithmTests(TestCase):
    """Test searching algorithms."""

    def test_binary_search_found(self):
        """Binary search finds target in sorted array."""
        searcher = BinarySearch()
        result = list(searcher.search([1, 2, 5, 8, 9], 5))
        final_state = result[-1]
        self.assertTrue(final_state['found'])
        self.assertEqual(final_state['found_index'], 2)

    def test_binary_search_not_found(self):
        """Binary search when target is not present."""
        searcher = BinarySearch()
        result = list(searcher.search([1, 2, 5, 8, 9], 7))
        final_state = result[-1]
        self.assertFalse(final_state['found'])

    def test_binary_search_first_element(self):
        """Binary search finds first element."""
        searcher = BinarySearch()
        result = list(searcher.search([1, 2, 5, 8, 9], 1))
        final_state = result[-1]
        self.assertTrue(final_state['found'])
        self.assertEqual(final_state['found_index'], 0)

    def test_binary_search_last_element(self):
        """Binary search finds last element."""
        searcher = BinarySearch()
        result = list(searcher.search([1, 2, 5, 8, 9], 9))
        final_state = result[-1]
        self.assertTrue(final_state['found'])
        self.assertEqual(final_state['found_index'], 4)

    def test_linear_search_found(self):
        """Linear search finds target."""
        searcher = LinearSearch()
        result = list(searcher.search([5, 2, 8, 1, 9], 8))
        final_state = result[-1]
        self.assertTrue(final_state['found'])
        self.assertEqual(final_state['found_index'], 2)

    def test_linear_search_not_found(self):
        """Linear search when target is not present."""
        searcher = LinearSearch()
        result = list(searcher.search([5, 2, 8, 1, 9], 7))
        final_state = result[-1]
        self.assertFalse(final_state['found'])

    def test_linear_search_unsorted(self):
        """Linear search works on unsorted arrays."""
        searcher = LinearSearch()
        result = list(searcher.search([9, 1, 5, 2, 8], 5))
        final_state = result[-1]
        self.assertTrue(final_state['found'])

    def test_search_comparison_counts(self):
        """Verify comparison counts are tracked."""
        binary = BinarySearch()
        linear = LinearSearch()

        arr = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        binary_result = list(binary.search(arr, 10))
        linear_result = list(linear.search(arr, 10))

        binary_comps = binary_result[-1]['comparisons']
        linear_comps = linear_result[-1]['comparisons']

        # Binary should use fewer comparisons
        self.assertLess(binary_comps, linear_comps)