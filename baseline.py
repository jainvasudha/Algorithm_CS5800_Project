"""
Module A-1: Baseline Frequency Computation
Owner: Bhoomika Panday

Computes keyword frequencies by scanning all events within the
active time window for each query.

Time: O(W) per query
Space: O(M)

Where:
    W = number of events in the current window
    M = number of distinct keywords in the current window
"""

def compute_baseline(events, current_time, window_size):
    """
    Recompute frequencies from scratch for all events
    inside the active time window.

    Args:
        events: List of (timestamp, keyword) events
        current_time: Current timestamp
        window_size: Size of active time window

    Returns:
        Dictionary mapping keyword -> frequency
    """
    freq = {}

    for timestamp, keyword in events:
        if current_time - window_size < timestamp <= current_time:
            freq[keyword] = freq.get(keyword, 0) + 1

    return freq


if __name__ == "__main__":
    sample_events = [
        (1, "jeans"),
        (2, "tops"),
        (3, "jeans"),
        (4, "shoes"),
        (5, "tops")
    ]

    result = compute_baseline(sample_events, current_time=5, window_size=3)
    print("Baseline frequency counts:", result)
