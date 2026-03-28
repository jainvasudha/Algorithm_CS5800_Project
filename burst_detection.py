"""
Module B-2: Burst Detection
Owner: Vasudha Jain

Detects sudden spikes in keyword popularity by comparing frequencies
across two consecutive time windows.

Two scoring approaches:
  - Ratio:      current / previous  (good for relative growth)
  - Difference: current - previous  (good for absolute growth)

Time:  O(M) to score all keywords + O(M log K) for top-K extraction
Space: O(M) for the scores
"""

import heapq


def _ratio_score(current, previous):
    """Ratio-based burst score."""
    if previous > 0:
        return current / previous
    elif current > 0:
        # brand new keyword — treat raw count as the score
        return float(current)
    return 0.0


def _diff_score(current, previous):
    """Difference-based burst score."""
    return float(current - previous)


def detect_bursts(current_freq, previous_freq, k, threshold=2.0, method="ratio"):
    """
    Find the top-K keywords with the highest burst scores.

    Goes through each keyword in current_freq, computes burst score
    vs previous window, filters by threshold, then uses a min-heap
    to grab the top K.

    Returns list of (keyword, score) sorted descending by score.

    Time:  O(M) + O(B log K) where B = number that pass threshold
    Space: O(K) for the heap
    """
    if k <= 0 or not current_freq:
        return []

    if method == "ratio":
        score_fn = _ratio_score
    elif method == "difference":
        score_fn = _diff_score
    else:
        raise ValueError(f"Unknown method '{method}'. Use 'ratio' or 'difference'.")

    # score each keyword and keep top K using a min-heap
    heap = []

    for keyword, count in current_freq.items():
        prev = previous_freq.get(keyword, 0)
        score = score_fn(count, prev)

        if score < threshold:
            continue

        if len(heap) < k:
            heapq.heappush(heap, (score, keyword))
        elif (score, keyword) > heap[0]:
            heapq.heapreplace(heap, (score, keyword))

    # pop everything out and reverse for descending order
    result = []
    while heap:
        score, kw = heapq.heappop(heap)
        result.append((kw, score))
    result.reverse()

    return result


if __name__ == "__main__":
    # quick demo with made-up data
    previous = {
        "wide-leg jeans": 30, "cargo pants": 40,
        "skinny jeans": 80, "Y2K fashion": 5,
        "mom jeans": 35, "baggy jeans": 20,
    }

    current = {
        "wide-leg jeans": 78, "cargo pants": 45,
        "skinny jeans": 12, "Y2K fashion": 92,
        "mom jeans": 34, "baggy jeans": 67,
        "corset top": 55,  # new keyword
    }

    K = 5

    print("Previous:", previous)
    print("Current: ", current)

    print(f"\nRatio method (threshold=2.0, K={K}):")
    for rank, (kw, score) in enumerate(detect_bursts(current, previous, K, 2.0, "ratio"), 1):
        print(f"  #{rank}  {kw:<20} score={score:.2f}")

    print(f"\nDifference method (threshold=10, K={K}):")
    for rank, (kw, score) in enumerate(detect_bursts(current, previous, K, 10, "difference"), 1):
        print(f"  #{rank}  {kw:<20} score={score:.1f}")
