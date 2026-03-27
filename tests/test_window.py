"""
Tests for Sliding Window Frequency Maintenance.
Covers: basic usage, expiration behavior, edge cases,
and equivalence with the baseline method.
"""

from baseline import compute_baseline
from sliding_window import add_event, get_frequencies, reset_window


# ── Sample data ──

SAMPLE_EVENTS = [
    (1, "jeans"),
    (2, "tops"),
    (3, "jeans"),
    (4, "shoes"),
    (5, "tops"),
]

REPEATED_EVENTS = [
    (1, "jeans"),
    (2, "jeans"),
    (3, "jeans"),
    (4, "jeans"),
]

MIXED_EVENTS = [
    (1, "hat"),
    (2, "bag"),
    (3, "hat"),
    (4, "shoes"),
    (5, "bag"),
    (6, "hat"),
]


# ── Basic functionality ───

class TestSlidingWindowBasic:
    def test_single_event(self):
        reset_window()
        add_event(1, "jeans", 3)
        assert get_frequencies() == {"jeans": 1}

    def test_multiple_events_before_expiration(self):
        reset_window()
        add_event(1, "jeans", 5)
        add_event(2, "tops", 5)
        add_event(3, "jeans", 5)
        assert get_frequencies() == {"jeans": 2, "tops": 1}

    def test_repeated_keyword_counts_correctly(self):
        reset_window()
        for timestamp, keyword in REPEATED_EVENTS:
            add_event(timestamp, keyword, 10)
        assert get_frequencies() == {"jeans": 4}


# ── Expiration behavior ───

class TestSlidingWindowExpiration:
    def test_expired_events_removed_correctly(self):
        reset_window()
        window_size = 3

        for timestamp, keyword in SAMPLE_EVENTS:
            add_event(timestamp, keyword, window_size)

        # Valid window at time 5 with size 3:
        # 2 < timestamp <= 5  → events at 3, 4, 5
        assert get_frequencies() == {"jeans": 1, "shoes": 1, "tops": 1}

    def test_all_old_events_expire(self):
        reset_window()
        add_event(1, "jeans", 2)
        add_event(2, "tops", 2)
        add_event(5, "shoes", 2)

        # At time 5, old timestamps 1 and 2 should expire
        assert get_frequencies() == {"shoes": 1}

    def test_no_expiration_with_large_window(self):
        reset_window()
        for timestamp, keyword in SAMPLE_EVENTS:
            add_event(timestamp, keyword, 10)

        assert get_frequencies() == {"jeans": 2, "tops": 2, "shoes": 1}


# ── Edge cases ───

class TestSlidingWindowEdgeCases:
    def test_empty_sequence(self):
        reset_window()
        assert get_frequencies() == {}

    def test_window_size_zero(self):
        reset_window()
        add_event(1, "jeans", 0)
        assert get_frequencies() == {}

    def test_window_size_negative(self):
        reset_window()
        add_event(1, "jeans", -1)
        assert get_frequencies() == {}

    def test_single_item_expires(self):
        reset_window()
        add_event(1, "jeans", 2)
        add_event(4, "tops", 2)
        assert get_frequencies() == {"tops": 1}


# ── Sliding window vs baseline equivalence ───

class TestSlidingMatchesBaseline:
    def test_sample_events_match_baseline(self):
        reset_window()
        window_size = 3

        for timestamp, keyword in SAMPLE_EVENTS:
            add_event(timestamp, keyword, window_size)

        sliding_result = get_frequencies()
        baseline_result = compute_baseline(SAMPLE_EVENTS, current_time=5, window_size=window_size)

        assert sliding_result == baseline_result

    def test_repeated_events_match_baseline(self):
        reset_window()
        window_size = 2

        for timestamp, keyword in REPEATED_EVENTS:
            add_event(timestamp, keyword, window_size)

        sliding_result = get_frequencies()
        baseline_result = compute_baseline(REPEATED_EVENTS, current_time=4, window_size=window_size)

        assert sliding_result == baseline_result

    def test_mixed_events_match_baseline(self):
        reset_window()
        window_size = 3

        for timestamp, keyword in MIXED_EVENTS:
            add_event(timestamp, keyword, window_size)

        sliding_result = get_frequencies()
        baseline_result = compute_baseline(MIXED_EVENTS, current_time=6, window_size=window_size)

        assert sliding_result == baseline_result
