"""
Module A-2: Sliding Window Frequency Maintenance
Owner: Bhoomika Panday

Maintains keyword frequencies incrementally over an active time window.

Instead of recomputing frequencies from scratch for every query,
this module updates counts by:
    1. Adding new incoming events
    2. Removing expired old events

This serves as the optimized alternative to the baseline method.

Time:  O(1) amortized per event update
Space: O(W + M)

Where:
    W = number of events currently stored in the active window
    M = number of distinct keywords in the active window
"""

from collections import deque

# Active events currently inside the time window
window = deque()

# Current frequency map for keywords in the active window
freq = {}


def add_event(timestamp: int, keyword: str, window_size: int) -> None:
    """
    Add a new event to the active window and update frequencies.

    Args:
        timestamp: Timestamp of the incoming event
        keyword: Keyword associated with the event
        window_size: Size of the active time window
    """
    if window_size <= 0:
        return

    window.append((timestamp, keyword))
    freq[keyword] = freq.get(keyword, 0) + 1

    # Remove events that are no longer in the active window
    remove_expired(timestamp, window_size)


def remove_expired(current_time: int, window_size: int) -> None:
    """
    Remove expired events from the front of the window.

    An event is expired if:
        timestamp <= current_time - window_size

    Args:
        current_time: Current timestamp
        window_size: Size of the active time window
    """
    while window and window[0][0] <= current_time - window_size:
        old_timestamp, old_keyword = window.popleft()
        freq[old_keyword] -= 1

        if freq[old_keyword] == 0:
            del freq[old_keyword]


def get_frequencies() -> dict[str, int]:
    """
    Return a copy of the current frequency map.

    Returns:
        Dictionary mapping keyword -> frequency
    """
    return dict(freq)


def reset_window() -> None:
    """
    Clear all stored events and frequencies.

    Useful for testing and repeated runs.
    """
    window.clear()
    freq.clear()


if __name__ == "__main__":
    sample_events = [
        (1, "jeans"),
        (2, "tops"),
        (3, "jeans"),
        (4, "shoes"),
        (5, "tops"),
    ]

    window_size = 3
    reset_window()

    print("Sliding window frequency updates:")
    for timestamp, keyword in sample_events:
        add_event(timestamp, keyword, window_size)
        print(f"After adding ({timestamp}, {keyword}): {get_frequencies()}")
