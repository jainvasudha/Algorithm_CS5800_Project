from baseline import compute_baseline
from sliding_window import add_event, freq, window

def reset_sliding_window():
    freq.clear()
    window.clear()

def test_window_matches_baseline():
    reset_sliding_window()

    events = [
        (1, "jeans"),
        (2, "tops"),
        (3, "jeans"),
        (4, "shoes"),
        (5, "tops")
    ]

    window_size = 3

    for timestamp, keyword in events:
        add_event(timestamp, keyword)

    sliding_result = dict(freq)
    baseline_result = compute_baseline(events, current_time=5, window_size=window_size)

    assert sliding_result == baseline_result


test_window_matches_baseline()
print("Test passed successfully")
