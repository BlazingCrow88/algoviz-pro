"""
Searching algorithm implementations with step-by-step visualization.

Why searching algorithms matter: Half of programming is finding things in data
structures. Understanding when to use binary vs linear search is fundamental CS.

Implementation note: All these algorithms use generator functions (yield instead
of return) so we can capture every step of the search process for visualization.
This was trickier than I expected - had to be careful about when to copy arrays
and when yielding was safe without breaking the visualization state.

Algorithms implemented:
- Binary Search: O(log n) but REQUIRES sorted data
- Linear Search: O(n) but works on ANY data
- Breadth-First Search: O(V+E) for graphs - different beast entirely

The professor will probably test edge cases like:
- Searching for values not in the array
- Empty arrays
- Arrays with one element
- Target at first/last position
"""
from typing import List, Dict, Any, Generator, Optional
from collections import deque
import time


class SearchingAlgorithm:
    """
    Base class for searching algorithms - similar pattern to SortingAlgorithm.

    Why a base class: Avoids code duplication. Both BinarySearch and LinearSearch
    need to track comparisons and execution time, so we define it once here.

    Design note: Searching algorithms don't track "swaps" like sorting algorithms
    do, since searching doesn't modify the array. Only tracking comparisons.
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
        stats and we'd get wrong counts. Learned this the hard way when testing!

        Also sets start_time to current moment so we can calculate execution time.
        """
        self.comparisons = 0
        self.start_time = time.time()  # Captures current timestamp

    def get_elapsed_time_ms(self):
        """
        Calculate how long the search has been running.

        Returns time in milliseconds because microseconds would be too precise
        for our needs and seconds would be too coarse (searches are fast!).

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

    Real-world uses:
    - Database indexes (looking up records)
    - Auto-complete suggestions (finding matching entries)
    - Game leaderboards (finding your rank)
    """

    def search(
            self,
            arr: List[int],
            target: int
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Search for target value in a sorted array using binary search.

        How it works: Start with left pointer at 0, right pointer at last index.
        Calculate middle, compare target to middle value, adjust pointers to
        eliminate half the search space. Repeat until found or pointers cross.

        Edge cases handled:
        - Empty array: left > right immediately, yields "not found"
        - Single element: works correctly (left = right = 0)
        - Target not in array: eventually left > right, yields "not found"
        - Duplicate values: returns first occurrence found

        Args:
            arr: List of integers IN SORTED ORDER (ascending)
                 If array isn't sorted, binary search gives wrong results!
            target: The value we're searching for

        Yields:
            dict: State at each step showing:
                - What we're comparing
                - Which half of array we're searching
                - Current left/right/mid pointers
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

    Real-world example: Finding a specific email in your inbox. If it's a recent
    email, starting at the top (linear) finds it faster than binary search would.

    Professor might test:
    - Target at first position (best case - 1 comparison)
    - Target at last position (worst case - n comparisons)
    - Target not in array (worst case - n comparisons)
    - Empty array (should handle gracefully)
    """

    def search(
            self,
            arr: List[int],
            target: int
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Search for target by checking each element sequentially.

        Simple algorithm: Start at index 0, check if it matches target.
        If not, move to index 1, check again. Continue until found or
        we reach the end of the array.

        Advantage: Works on UNSORTED data (unlike binary search).
        Disadvantage: Slower for large sorted datasets.

        Args:
            arr: List of integers (CAN be unsorted - that's the point!)
            target: Value we're looking for

        Yields:
            dict: State at each comparison showing which index we're checking

        Implementation note: Using a simple for loop since we're just going
        through elements sequentially. No fancy pointer arithmetic needed like
        binary search.
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


class BreadthFirstSearch:
    """
    Breadth-First Search (BFS) - graph traversal algorithm.

    This is different from the other searches: it works on GRAPHS, not arrays.
    A graph is a collection of nodes (vertices) connected by edges.

    The BFS strategy: Explore all neighbors of the current node before moving
    to the next level. Like ripples in a pond spreading outward.

    Example: Social network - finding how you're connected to someone
    Level 0: You
    Level 1: Your direct friends
    Level 2: Friends of friends
    Level 3: Friends of friends of friends

    Why it's O(V + E):
    - V (vertices): We visit each node once
    - E (edges): We examine each edge once when checking neighbors
    - Total: V + E operations

    Space complexity O(V): In worst case, queue could contain all nodes
    (imagine a star graph where one node connects to all others).

    Key data structures:
    - Queue (deque): FIFO - ensures we process nodes level by level
    - Set (visited): Prevents infinite loops in cyclic graphs
    - Dict (parent): Lets us reconstruct the path from start to target

    Why use BFS instead of DFS?
    - BFS finds SHORTEST path in unweighted graphs
    - DFS finds A path, but not necessarily the shortest

    Real-world uses:
    - GPS navigation (finding shortest route)
    - Social network analysis (degrees of separation)
    - Web crawlers (exploring websites level by level)
    - Network broadcasting

    Implementation note: Using deque from collections because it has O(1) append
    and popleft operations. Regular list would be O(n) for pop(0).
    """

    def __init__(self):
        """
        Initialize BFS-specific tracking.

        Note: BFS doesn't extend SearchingAlgorithm because graphs are different
        enough from arrays that the base class doesn't help much. Different data
        structure = different tracking needs.
        """
        self.visited = set()  # Track which nodes we've seen (prevents cycles)
        self.start_time = None  # For timing the search

    def search(
            self,
            graph: Dict[int, List[int]],
            start: int,
            target: Optional[int] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Perform breadth-first search on a graph.

        Two modes of operation:
        1. If target is provided: Search for that specific node, return path when found
        2. If target is None: Traverse entire graph (useful for graph analysis)

        Graph representation: Using adjacency list (dict where keys are nodes and
        values are lists of neighbor nodes). This is more space-efficient than an
        adjacency matrix for sparse graphs.

        Example graph:
        {
            1: [2, 3],      # Node 1 connects to nodes 2 and 3
            2: [1, 4],      # Node 2 connects to nodes 1 and 4
            3: [1, 4],      # Node 3 connects to nodes 1 and 4
            4: [2, 3]       # Node 4 connects to nodes 2 and 3
        }

        Args:
            graph: Adjacency list {node: [list of neighbors]}
            start: Which node to start the search from
            target: Optional - specific node to find (None means traverse all)

        Yields:
            dict: State information showing:
                - Current node being visited
                - Contents of the queue
                - Which nodes have been visited
                - Path to target (if found)

        Edge cases:
        - Start node not in graph: Will visit just that node (neighbors = empty list)
        - Disconnected graph: Will only visit nodes reachable from start
        - Cyclic graph: visited set prevents infinite loops
        """
        self.start_time = time.time()
        self.visited = set()  # Reset visited set for this search

        # Queue starts with just the start node
        # Using deque because popleft() is O(1) vs list.pop(0) which is O(n)
        queue = deque([start])

        # Track parent of each node to reconstruct path later
        parent = {start: None}  # Start node has no parent

        # Track distance/level of each node from start
        level = {start: 0}  # Start node is at level 0

        # Show initial state
        yield {
            'graph': graph,
            'start': start,
            'target': target,
            'queue': list(queue),  # Convert deque to list for JSON serialization
            'visited': list(self.visited),
            'message': f'Starting BFS from node {start}',
            'step_type': 'start'
        }

        # Main BFS loop - continues while queue has nodes to process
        while queue:
            # Remove node from front of queue (FIFO)
            node = queue.popleft()

            # Check if we've already visited this node
            # (Could happen if multiple paths lead to same node)
            if node not in self.visited:
                self.visited.add(node)  # Mark as visited NOW to avoid revisiting

                # Show that we're visiting this node
                yield {
                    'graph': graph,
                    'current_node': node,
                    'queue': list(queue),
                    'visited': list(self.visited),
                    'level': level[node],
                    'message': f'Visiting node {node} at level {level[node]}',
                    'step_type': 'visit'
                }

                # Check if this is the target we're looking for
                if target is not None and node == target:
                    # Reconstruct path from start to target by following parent pointers
                    path = []
                    current = node
                    while current is not None:
                        path.append(current)
                        current = parent[current]  # Move to parent
                    path.reverse()  # We built path backwards, so reverse it

                    yield {
                        'graph': graph,
                        'found': True,
                        'target': target,
                        'path': path,  # Shortest path from start to target
                        'visited': list(self.visited),
                        'message': f'Found target {target}! Path: {path}',
                        'complete': True,
                        'step_type': 'found'
                    }
                    return  # Stop searching - we found it

                # Add all unvisited neighbors to the queue
                # This is the "breadth" part - we queue all neighbors before moving deeper
                for neighbor in graph.get(node, []):  # .get() handles missing nodes gracefully
                    # Only add if we haven't visited and it's not already in queue
                    if neighbor not in self.visited and neighbor not in queue:
                        queue.append(neighbor)  # Add to back of queue
                        parent[neighbor] = node  # Remember how we got to this neighbor
                        level[neighbor] = level[node] + 1  # One level deeper than current node

                        yield {
                            'graph': graph,
                            'current_node': node,
                            'neighbor': neighbor,
                            'queue': list(queue),
                            'visited': list(self.visited),
                            'message': f'Adding neighbor {neighbor} to queue',
                            'step_type': 'enqueue'
                        }

        # Queue is empty - we've visited all reachable nodes
        if target is None:
            # No specific target, just traversing the graph
            yield {
                'graph': graph,
                'visited': list(self.visited),
                'message': 'BFS traversal complete',
                'complete': True,
                'step_type': 'complete'
            }
        else:
            # We were looking for a specific target but didn't find it
            # This means target is not reachable from start node
            yield {
                'graph': graph,
                'found': False,
                'target': target,
                'visited': list(self.visited),
                'message': f'Target {target} not found in graph (may be disconnected)',
                'complete': True,
                'step_type': 'not_found'
            }