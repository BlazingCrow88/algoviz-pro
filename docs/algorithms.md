# Algorithm Complexity Reference

This document explains the time and space complexity of all algorithms
implemented in AlgoViz Pro. I've included the reasoning behind each 
complexity rating since that helped me understand them better while coding.

## Sorting Algorithms

### Bubble Sort

**What it does:**  
Probably the simplest sorting algorithm - it just keeps going through
the list comparing adjacent elements and swapping them if they're in the
wrong order. Not the fastest, but super easy to understand and implement.

**Time Complexity:**
- **Best Case: O(n)** - If the array is already sorted, we can detect this
in one pass (I added an optimization flag for this)
- **Average Case: O(n²)** - Most random arrays end up here
- **Worst Case: O(n²)** - When the array is sorted backwards, maximum pain

**Space Complexity: O(1)** - Sorts in place, only needs a couple 
temp variables

**Why This Complexity:**  
The nested loop structure is what kills performance. Outer loop runs n times,
inner loop runs (n-i-1) times each iteration. So we get n(n-1)/2 comparisons
total, which simplifies to O(n²). Not great for large datasets.

**When to Use:**
- Small datasets (maybe < 50 elements)
- Data that's mostly sorted already
- Teaching/learning purposes
- When code simplicity > performance

**Stability:** Yes - equal elements stay in their original order

---

### Merge Sort

**What it does:**  
Classic divide-and-conquer approach. Split the array in half, recursively
sort both halves, then merge them back together in sorted order. 
This was actually pretty fun to implement with generators.

**Time Complexity:**
- **Best Case: O(n log n)**
- **Average Case: O(n log n)**
- **Worst Case: O(n log n)** - This is the big advantage - 
guaranteed performance no matter what!

**Space Complexity: O(n)** - Need extra space for the merge operation
(trade-off for speed)

**Why This Complexity:**  
We divide the array log₂(n) times (think of it as a binary tree depth),
and at each level we do O(n) work to merge everything. 
So it's O(n) work × O(log n) levels = O(n log n). 
The math actually works out pretty nicely.

**When to Use:**
- Larger datasets where you need consistent performance
- When you need the sort to be stable
- Working with linked lists (actually doesn't need extra space there)
- When O(n log n) guarantee is worth the memory cost

**Stability:** Yes

---

### Quick Sort

**What it does:**  
Another divide-and-conquer algorithm. Pick a pivot element, 
partition the array so everything less than pivot is on the left 
and everything greater is on the right, then recursively sort both sides.
Usually faster than merge sort in practice.

**Time Complexity:**
- **Best Case: O(n log n)** - Pivot splits the array evenly
- **Average Case: O(n log n)** - What you typically get with random data
- **Worst Case: O(n²)** - If you're unlucky with pivot selection 
(sorted array with bad pivot choice)

**Space Complexity: O(log n)** - From the recursion call stack

**Why This Complexity:**  
- Best/Average: Good pivot selection creates log n levels of recursion with
O(n) partitioning work per level
- Worst: Bad pivots create unbalanced partitions, degenerating to n levels
instead of log n. This is why pivot selection matters!

**When to Use:**
- General purpose sorting (Python's built-in sort uses a variant of this)
- When you care about average case more than worst case
- Need in-place sorting
- Working with arrays (good cache performance)

**Stability:** No - the partitioning can reorder equal elements

**Note:** There are ways to improve worst-case like randomized pivot selection,
but I stuck with the basic version for clarity.

---

## Searching Algorithms

### Binary Search

**What it does:**  
Super efficient search for sorted arrays. Keep cutting the search space 
in half until you find what you're looking for (or don't).
Like the "guess a number" game strategy.

**Time Complexity:**
- **Best Case: O(1)** - Lucky! Target is right in the middle
- **Average Case: O(log n)**
- **Worst Case: O(log n)**

**Space Complexity: O(1)** - Iterative version just needs a few variables

**Why This Complexity:**  
Each comparison eliminates half the remaining elements. 
So we go from n elements → n/2 → n/4 → n/8 → ... → 1. 
This takes log₂(n) steps. For example, searching 1 million items only needs 
about 20 comparisons max!

**Requirements:** Array MUST be sorted (obviously)

**When to Use:**
- Large sorted datasets
- Multiple searches on the same data
- When search speed is critical

---

### Linear Search

**What it does:**  
The simplest search possible - just check each element one by 
one until you find what you're looking for. Brute force but sometimes 
that's all you need.

**Time Complexity:**
- **Best Case: O(1)** - First element is the target
- **Average Case: O(n)** - Target somewhere in the middle
- **Worst Case: O(n)** - Target is last or doesn't exist

**Space Complexity: O(1)**

**Why This Complexity:**  
Might need to check every single element in the worst case. 
Pretty straightforward.

**When to Use:**
- Small datasets where the overhead isn't worth it
- Unsorted data (can't use binary search)
- One-time searches (not worth sorting first)
- Data structures where you can't do random access (like linked lists)

---

### Breadth-First Search (BFS)

**What it does:**  
Graph traversal that explores nodes level by level. Uses a queue to keep
track of what to visit next. Good for finding the shortest paths in 
unweighted graphs.

**Time Complexity: O(V + E)**
- V = number of vertices/nodes
- E = number of edges/connections

**Space Complexity: O(V)** - Queue might need to hold all vertices

**Why This Complexity:**  
We visit each vertex exactly once (O(V)), and we look at each edge 
exactly once (O(E)). So total is O(V + E). Pretty efficient for what it does.

**When to Use:**
- Finding the shortest path in unweighted graphs
- Level-order tree traversal
- Finding all connected components
- Checking if a graph is bipartite

**Implementation note:** I used a deque for the queue since 
it's more efficient than a regular list for this.

---

## Quick Comparison

Here's everything side-by-side for reference:

## Quick Comparison

Here's everything side-by-side for reference:

| Algorithm      | Best       | Average    | Worst      | Space      | Stable |
|----------------|------------|------------|------------|------------|--------|
| Bubble Sort    | O(n)       | O(n²)      | O(n²)      | O(1)       | Yes    |
| Merge Sort     | O(n log n) | O(n log n) | O(n log n) | O(n)       | Yes    |
| Quick Sort     | O(n log n) | O(n log n) | O(n²)      | O(log n)   | No     |
| Binary Search  | O(1)       | O(log n)   | O(log n)   | O(1)       | N/A    |
| Linear Search  | O(1)       | O(n)       | O(n)       | O(1)       | N/A    |
| BFS            | O(V+E)     | O(V+E)     | O(V+E)     | O(V)       | N/A    |

---

## Implementation Details

All the algorithms in AlgoViz Pro are implemented with some common features:

- **Generator functions** - Each algorithm yields intermediate states so the 
visualization can show step-by-step execution. This was probably the trickiest
part to get right.
- **Metrics tracking** - Count comparisons and swaps to analyze performance
- **Comprehensive docstrings** - Each function has full documentation with 
complexity analysis
- **Edge case handling** - Empty arrays, single elements, duplicate values, etc.
- **PEP 8 compliance** - Kept the code clean and readable

The generator approach was really useful for visualization but made the 
code a bit more complex than standard implementations. Worth it though!

---

## References & Learning Resources

- *Introduction to Algorithms* by Cormen, Leiserson, Rivest, and Stein (CLRS) -
The bible of algorithms
- *The Algorithm Design Manual* by Steven Skiena - More practical approach
- VisuAlgo.net - Awesome visualizations that inspired parts of this project
- Class notes from INF601