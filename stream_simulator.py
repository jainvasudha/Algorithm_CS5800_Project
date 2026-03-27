"""
Module A-0: Stream Simulator
Owner: Bhoomika Panday

Converts static input data into a sequence of timestamped events
to simulate a streaming data environment.

This module is used to generate event streams in the form:
    (timestamp, keyword)

These events can later be processed by the baseline and
sliding window modules.

Time:  O(N)
Space: O(N)

Where:
    N = number of input events
"""


def load_sample_events() -> list[tuple[int, str]]:
    """
    Return a small sample event stream for testing.

    Each event is represented as:
        (timestamp, keyword)

    Returns:
        List of timestamped keyword events
    """
    events = [
        (1, "jeans"),
        (2, "tops"),
        (3, "jeans"),
        (4, "shoes"),
        (5, "tops"),
    ]
    return events


def stream_events(events: list[tuple[int, str]]):
    """
    Yield events one at a time to simulate streaming input.

    Args:
        events: List of (timestamp, keyword) events

    Yields:
        One event at a time
    """
    for event in events:
        yield event


if __name__ == "__main__":
    sample_events = load_sample_events()

    print("Sample event stream:")
    for timestamp, keyword in stream_events(sample_events):
        print((timestamp, keyword))
