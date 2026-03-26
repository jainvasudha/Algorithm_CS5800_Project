def compute_baseline(events, current_time, window_size):
    freq = {}

    for timestamp, keyword in events:
        if current_time - window_size < timestamp <= current_time:
            freq[keyword] = freq.get(keyword, 0) + 1

    return freq


if __name__ == "__main__":
    events = [
        (1, "jeans"),
        (2, "tops"),
        (3, "jeans"),
        (4, "shoes"),
        (5, "tops")
    ]

    result = compute_baseline(events, current_time=5, window_size=3)
    print("Baseline frequency counts:", result)
