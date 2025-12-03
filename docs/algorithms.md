# Algorithm Complexity Reference

This document explains the time and space complexity of all algorithms
implemented in AlgoViz Pro. Includes reasoning behind each complexity
rating to help understand the implementations.

## Sorting Algorithms

### Bubble Sort

**What it does:**  
Simplest sorting algorithm - repeatedly compares adjacent elements and
swaps them if wrong order. Not the fastest but easy to understand.

**Time Complexity:**
- **Best Case: O(n)** - Already sorted, detected in one pass with optimization flag
- **Average Case: O(n²)** - Most random arrays
- **Worst Case: O(n²)** - Reverse sorted array

**Space Complexity: O(1)** - Sorts in place

**Why This Complexity:**  
Nested loop structure: outer loop runs n times, inner loop runs (n-i-1) times.
Total comparisons: n(n-1)/2, simplifies to O(n²).

**When to Use:**
- Small datasets (< 50 elements)
- Mostly sorted data
- Teaching/learning
- Code simplicity > performance

**Stability:** Yes - equal elements maintain original order

---

### Merge Sort

**What it does:**  
Divide-and-conquer: split array in half, recursively sort both halves,
merge back together in sorted order.

**Time Complexity:**
- **Best Case: O(n log n)**
- **Average Case: O(n log n)**
- **Worst Case: O(n log n)** - Guaranteed performance

**Space Complexity: O(n)** - Extra space for merge operation

**Why This Complexity:**  
Array divided log₂(n) times (binary tree depth), O(n) work per level to merge.
O(n) × O(log n) = O(n log n).

**When to Use:**
- Large datasets needing consistent performance
- Stable sort required
- Linked lists (doesn't need extra space)
- O(n log n) guarantee worth memory cost

**Stability:** Yes

---

### Quick Sort

**What it does:**  
Divide-and-conquer: pick pivot, partition array (elements < pivot left,
elements > pivot right), recursively sort both sides.

**Time Complexity:**
- **Best Case: O(n log n)** - Pivot splits evenly
- **Average Case: O(n log n)** - Random data
- **Worst Case: O(n²)** - Bad pivot selection (already sorted with poor pivot)

**Space Complexity: O(log n)** - Recursion call stack

**Why This Complexity:**  
- Best/Average: Good pivots create log n recursion levels with O(n) partitioning per level
- Worst: Bad pivots create unbalanced partitions, degenerating to n levels

**When to Use:**
- General purpose sorting
- Average case > worst case priority
- In-place sorting needed
- Arrays (good cache performance)

**Stability:** No - partitioning can reorder equal elements

**Note:** Basic implementation used for clarity. Could improve worst-case with
randomized pivot selection.

---

## Searching Algorithms

### Binary Search

**What it does:**  
Efficient search for sorted arrays. Repeatedly cut search space in half
until target found.

**Time Complexity:**
- **Best Case: O(1)** - Target is middle element
- **Average Case: O(log n)**
- **Worst Case: O(log n)**

**Space Complexity: O(1)** - Iterative version

**Why This Complexity:**  
Each comparison eliminates half remaining elements: n → n/2 → n/4 → n/8 → 1.
Takes log₂(n) steps. Searching 1 million items needs ~20 comparisons max.

**Requirements:** Array MUST be sorted

**When to Use:**
- Large sorted datasets
- Multiple searches on same data
- Search speed critical

---

### Linear Search

**What it does:**  
Check each element one by one until target found. Brute force but simple.

**Time Complexity:**
- **Best Case: O(1)** - First element is target
- **Average Case: O(n)** - Target in middle
- **Worst Case: O(n)** - Target last or doesn't exist

**Space Complexity: O(1)**

**Why This Complexity:**  
Might check every element in worst case.

**When to Use:**
- Small datasets
- Unsorted data (can't use binary search)
- One-time searches (not worth sorting first)
- Sequential access data structures (linked lists)

---

## Quick Comparison

| Algorithm      | Best       | Average    | Worst      | Space      | Stable |
|----------------|------------|------------|------------|------------|--------|
| Bubble Sort    | O(n)       | O(n²)      | O(n²)      | O(1)       | Yes    |
| Merge Sort     | O(n log n) | O(n log n) | O(n log n) | O(n)       | Yes    |
| Quick Sort     | O(n log n) | O(n log n) | O(n²)      | O(log n)   | No     |
| Binary Search  | O(1)       | O(log n)   | O(log n)   | O(1)       | N/A    |
| Linear Search  | O(1)       | O(n)       | O(n)       | O(n)       | N/A    |

---

## Implementation Details

All algorithms implemented with:

- **Generator functions** - Yield intermediate states for step-by-step visualization
- **Metrics tracking** - Count comparisons and swaps for performance analysis
- **Comprehensive docstrings** - Full documentation with complexity analysis
- **Edge case handling** - Empty arrays, single elements, duplicates
- **PEP 8 compliance** - Clean, readable code

Generator approach enabled visualization but added complexity compared to
standard implementations. Worth the trade-off.

---

## References

- *Introduction to Algorithms* by Cormen, Leiserson, Rivest, and Stein (CLRS)
- *The Algorithm Design Manual* by Steven Skiena
- VisuAlgo.net - Visualization inspiration
- INF601 class notes