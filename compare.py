from baseline import compute_baseline
from sliding_window import add_event, freq

# sample events
events = [
    (1, "jeans"),
    (2, "tops"),
    (3, "jeans"),
    (4, "shoes"),
    (5, "tops")
]

window_size = 3

# run sliding window
for timestamp, keyword in events:
    add_event(timestamp, keyword)

sliding_result = dict(freq)

# run baseline
baseline_result = compute_baseline(events, current_time=5, window_size=window_size)

print("Sliding Window:", sliding_result)
print("Baseline:", baseline_result)
