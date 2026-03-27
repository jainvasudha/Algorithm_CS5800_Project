"""
Module A-1: Baseline Frequency Computation
Owner: Bhoomika Panday

Computes keyword frequencies by scanning all events within the
active time window for each query.

This serves as the reference implementation for validating the
optimized sliding window approach.

Time:  O(N) per query
Space: O(M)

Where:
    N = total number of input events
    M = number of distinct keywords in the active window
"""


def compute_baseline(events: list[tuple[int, str]], current_time: int, window_size: int) -> dict[str, int]:
    """
    Recompute frequencies from scratch for all events
    inside the active time window.

    The active window includes events satisfying:
        current_time - window_size < timestamp <= current_time

    Args:
        events: List of (timestamp, keyword) events
        current_time: Current timestamp
        window_size: Size of active time window

    Returns:
        Dictionary mapping keyword -> frequency
    """
    if window_size <= 0 or not events:
        return {}

    freq_map = {}

    for timestamp, keyword in events:
        if current_time - window_size < timestamp <= current_time:
            freq_map[keyword] = freq_map.get(keyword, 0) + 1

    return freq_map


if __name__ == "__main__":
    sample_events = [
        (1, "jeans"),
        (2, "tops"),
        (3, "jeans"),
        (4, "shoes"),
        (5, "tops"),
    ]

    result = compute_baseline(sample_events, current_time=5, window_size=3)
    print("Baseline frequency counts:", result)
