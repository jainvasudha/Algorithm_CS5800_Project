"""
Tests for cycle detection and trend classification.
"""

import pytest
from cycle_detection import cosine_similarity, find_best_match, compute_slope, classify_trend


# -- cosine similarity --

class TestCosine:
    def test_identical(self):
        v = [10, 20, 30, 40, 50]
        assert cosine_similarity(v, v) == pytest.approx(1.0)

    def test_scaled_vector(self):
        # [1,2,3] and [2,4,6] point same direction, should be 1.0
        assert cosine_similarity([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)

    def test_orthogonal(self):
        assert cosine_similarity([1, 0, 0], [0, 1, 0]) == pytest.approx(0.0)

    def test_zero_vector(self):
        assert cosine_similarity([0, 0, 0], [1, 2, 3]) == 0.0

    def test_both_zero(self):
        assert cosine_similarity([0, 0], [0, 0]) == 0.0

    def test_empty(self):
        assert cosine_similarity([], [1, 2]) == 0.0
        assert cosine_similarity([], []) == 0.0

    def test_different_lengths(self):
        # should truncate to shorter and still work
        assert cosine_similarity([1, 2, 3, 4, 5], [1, 2, 3]) == pytest.approx(1.0)

    def test_cyclical_patterns(self):
        a = [10, 50, 10, 50, 10]
        b = [12, 48, 11, 52, 9]
        assert cosine_similarity(a, b) > 0.99

    def test_rising_vs_falling(self):
        # both positive so not orthogonal, but should be < 1
        assert cosine_similarity([10, 20, 30, 40, 50], [50, 40, 30, 20, 10]) < 0.9

    def test_range_check(self):
        sim = cosine_similarity([3, 7, 1, 9], [5, 2, 8, 4])
        assert 0.0 <= sim <= 1.0


# -- best match --

class TestBestMatch:
    def test_matches_cyclical(self):
        hist = {
            "cyclical": [10, 50, 10, 50, 10],
            "rising":   [10, 20, 30, 40, 50],
            "fading":   [50, 40, 30, 20, 10],
        }
        match, sim = find_best_match([12, 48, 11, 52, 9], hist)
        assert match == "cyclical"
        assert sim > 0.99

    def test_empty_db(self):
        assert find_best_match([1, 2, 3], {}) == ("", 0.0)

    def test_empty_vector(self):
        assert find_best_match([], {"a": [1, 2]}) == ("", 0.0)

    def test_single_entry(self):
        match, sim = find_best_match([2, 4, 6], {"only": [1, 2, 3]})
        assert match == "only"
        assert sim == pytest.approx(1.0)


# -- slope --

class TestSlope:
    def test_upward(self):
        assert compute_slope([10, 20, 30, 40, 50]) > 0

    def test_downward(self):
        assert compute_slope([50, 40, 30, 20, 10]) < 0

    def test_flat(self):
        assert compute_slope([30, 30, 30, 30]) == pytest.approx(0.0)

    def test_single_value(self):
        assert compute_slope([42]) == 0.0

    def test_empty(self):
        assert compute_slope([]) == 0.0

    def test_two_points(self):
        assert compute_slope([10, 20]) == pytest.approx(10.0)

    def test_linear(self):
        # y = 5 + 3x -> slope should be 3
        assert compute_slope([5, 8, 11, 14, 17]) == pytest.approx(3.0)


# -- classification --

class TestClassify:
    def test_fading(self):
        # steep decline in keyword freq -> Fading
        prev = {"skinny jeans": 80}
        curr = {"skinny jeans": 12}
        assert classify_trend("skinny jeans", curr, prev, 0.15) == "Fading"

    def test_cyclical(self):
        # same distribution both windows -> high cosine sim -> Cyclical
        prev = {"cargo pants": 50, "jeans": 30}
        curr = {"cargo pants": 50, "jeans": 30}
        assert classify_trend("cargo pants", curr, prev, 1.1) == "Cyclical"

    def test_new_burst(self):
        # big burst + very different distribution -> New
        prev = {"Y2K fashion": 5, "other": 100}
        curr = {"Y2K fashion": 92, "other": 10}
        assert classify_trend("Y2K fashion", curr, prev, 4.6) == "New"

    def test_new_growing(self):
        # growing keyword, low burst, different pattern -> New (via slope > 0)
        prev = {"wide-leg jeans": 20, "other": 50}
        curr = {"wide-leg jeans": 78, "other": 10}
        assert classify_trend("wide-leg jeans", curr, prev, 1.5) == "New"

    def test_decline_beats_high_similarity(self):
        # steep decline should be Fading even if overall distribution is similar
        prev = {"retro": 100, "a": 30}
        curr = {"retro": 5, "a": 28}
        assert classify_trend("retro", curr, prev, 0.5) == "Fading"

    def test_flat_defaults_to_fading(self):
        # flat keyword + very different overall pattern -> Fading
        prev = {"neutral": 30, "x": 100}
        curr = {"neutral": 30, "x": 0}
        assert classify_trend("neutral", curr, prev, 0.8) == "Fading"

    def test_custom_thresholds(self):
        # lowering cyclical_threshold should flip this to Cyclical
        prev = {"test": 30, "x": 100}
        curr = {"test": 30, "x": 5}
        label = classify_trend("test", curr, prev, 1.0,
                               cyclical_threshold=0.4)
        assert label == "Cyclical"
