"""
Module A-3: Baseline vs Sliding Window Comparison
Owner: Bhoomika

Compares the baseline frequency computation method with the
optimized sliding window method on the same input data.

This module is used to validate that the optimized approach
produces the same output as the baseline reference method.
"""

from baseline import compute_baseline
from sliding_window import add_event, get_frequencies, reset_window


def compare_methods(events: list[tuple[int, str]], current_time: int, window_size: int) -> tuple[dict[str, int], dict[str, int]]:
    """
    Compare baseline and sliding window frequency computation.

    Args:
        events: List of (timestamp, keyword) events
        current_time: Current timestamp at which frequencies are evaluated
        window_size: Size of the active time window

    Returns:
        A tuple:
            (sliding_window_result, baseline_result)
    """
    reset_window()

    # Run optimized sliding window method
    for timestamp, keyword in events:
        add_event(timestamp, keyword, window_size)

    sliding_result = get_frequencies()

    # Run baseline method
    baseline_result = compute_baseline(events, current_time, window_size)

    return sliding_result, baseline_result


if __name__ == "__main__":
    sample_events = [
        (1, "jeans"),
        (2, "tops"),
        (3, "jeans"),
        (4, "shoes"),
        (5, "tops"),
    ]

    current_time = 5
    window_size = 3

    sliding_result, baseline_result = compare_methods(
        sample_events,
        current_time=current_time,
        window_size=window_size
    )

    print("Sliding Window:", sliding_result)
    print("Baseline:", baseline_result)

    if sliding_result == baseline_result:
        print("Comparison successful: both methods match.")
    else:
        print("Comparison failed: outputs do not match.")
