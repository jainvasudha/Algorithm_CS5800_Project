def load_sample_events():
    events = [
        (1, "jeans"),
        (2, "tops"),
        (3, "jeans"),
        (4, "shoes"),
        (5, "tops")
    ]
    return events


if __name__ == "__main__":
    events = load_sample_events()
    for event in events:
        print(event)
