"""
Module B-1: Top-K Selection
Owner: Vasudha Jain

Two approaches to extract the K most frequent items from a frequency map:
  1. Heap-based  — O(M log K) time, O(K) space
  2. Sort-based  — O(M log M) time, O(M) space

Where M = number of distinct keywords in the frequency map.
"""

import heapq


class _NegStr:
    """Wrapper that reverses string comparison order for heap tiebreaking."""
    __slots__ = ("val",)

    def __init__(self, val: str):
        self.val = val

    def __lt__(self, other):
        return self.val > other.val  # reversed

    def __eq__(self, other):
        return self.val == other.val


def top_k_heap(freq_map: dict[str, int], k: int) -> list[tuple[str, int]]:
    """
    Return the Top-K most frequent items using a min-heap of size K.

    Algorithm:
        - Maintain a min-heap of size K ordered by count.
        - For each item: if heap has room, push. Otherwise, if count
          beats the current minimum, replace it.
        - Ties are broken alphabetically (ascending) for deterministic output.

    Time:  O(M log K)
    Space: O(K)
    """
    if k <= 0 or not freq_map:
        return []

    # Store (count, neg_keyword) so that ties keep alphabetically-first items.
    # In a min-heap, the smallest (count, neg_keyword) is evicted first.
    # Negating keyword comparison means "alpha" > "gamma" in heap order,
    # so "alpha" survives eviction when counts are equal.
    min_heap = []  # elements: (count, NegStr(keyword))

    for keyword, count in freq_map.items():
        entry = (count, _NegStr(keyword))
        if len(min_heap) < k:
            heapq.heappush(min_heap, entry)
        elif entry > min_heap[0]:
            heapq.heapreplace(min_heap, entry)

    # Extract in descending order of count (alphabetical tiebreak)
    result = []
    while min_heap:
        count, neg_kw = heapq.heappop(min_heap)
        result.append((neg_kw.val, count))
    result.reverse()

    return result


def top_k_sort(freq_map: dict[str, int], k: int) -> list[tuple[str, int]]:
    """
    Baseline: Return the Top-K most frequent items by full sorting.

    Algorithm:
        - Convert freq_map to a list of (keyword, count).
        - Sort descending by count, then ascending by keyword for ties.
        - Return the first K items.

    Time:  O(M log M)
    Space: O(M)
    """
    if k <= 0 or not freq_map:
        return []

    items = list(freq_map.items())
    # Sort by count descending, then keyword ascending for tiebreak
    items.sort(key=lambda x: (-x[1], x[0]))

    return items[:k]


if __name__ == "__main__":
    import csv
    import os
    import time

    # Build freq_map from the latest data point in each Google Trends CSV
    data_dir = os.path.join(os.path.dirname(__file__), "data", "google_trends")
    freq_map = {}

    for filename in sorted(os.listdir(data_dir)):
        if not filename.endswith(".csv"):
            continue
        filepath = os.path.join(data_dir, filename)
        with open(filepath) as f:
            reader = csv.reader(f)
            header = next(reader)  # skip header
            keyword = header[1].strip()
            # Read all rows, keep the last one as "current" frequency
            last_val = 0
            for row in reader:
                if row[1].strip().isdigit():
                    last_val = int(row[1])
            freq_map[keyword] = last_val

    print("=" * 55)
    print("  Top-K Selection Demo — Real Google Trends Data")
    print("=" * 55)
    print(f"\nFrequency map (latest month, {len(freq_map)} keywords):")
    for kw, count in sorted(freq_map.items(), key=lambda x: -x[1]):
        print(f"  {kw:<22} → {count}")

    K = 5
    print(f"\n--- Top {K} by Heap (O(M log K)) ---")
    t0 = time.perf_counter()
    heap_result = top_k_heap(freq_map, K)
    t1 = time.perf_counter()
    for rank, (kw, count) in enumerate(heap_result, 1):
        print(f"  #{rank}  {kw:<22}  freq={count}")
    print(f"  Time: {(t1 - t0) * 1_000_000:.1f} μs")

    print(f"\n--- Top {K} by Sort (O(M log M)) ---")
    t0 = time.perf_counter()
    sort_result = top_k_sort(freq_map, K)
    t1 = time.perf_counter()
    for rank, (kw, count) in enumerate(sort_result, 1):
        print(f"  #{rank}  {kw:<22}  freq={count}")
    print(f"  Time: {(t1 - t0) * 1_000_000:.1f} μs")

    print(f"\nBoth methods agree: {set(heap_result) == set(sort_result)}")
