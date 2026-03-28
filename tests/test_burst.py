"""
Tests for burst detection module.
"""

import pytest
from burst_detection import detect_bursts, _ratio_score, _diff_score


# sample freq maps for testing
PREV = {
    "wide-leg jeans": 30, "cargo pants": 40,
    "skinny jeans": 80, "Y2K fashion": 5,
    "mom jeans": 35, "baggy jeans": 20,
}

CURR = {
    "wide-leg jeans": 78,   # ratio 2.6
    "cargo pants": 45,      # ratio 1.125
    "skinny jeans": 12,     # ratio 0.15 (declined)
    "Y2K fashion": 92,      # ratio 18.4
    "mom jeans": 34,         # ratio ~0.97
    "baggy jeans": 67,       # ratio 3.35
    "corset top": 55,        # new keyword, ratio = 55
}


# -- scoring function tests --

class TestScoring:
    def test_ratio_normal(self):
        assert _ratio_score(60, 30) == 2.0

    def test_ratio_when_declining(self):
        assert _ratio_score(10, 80) == 0.125

    def test_ratio_brand_new(self):
        # previous was 0, so score = current count
        assert _ratio_score(55, 0) == 55.0

    def test_ratio_both_zero(self):
        assert _ratio_score(0, 0) == 0.0

    def test_diff_normal(self):
        assert _diff_score(78, 30) == 48.0

    def test_diff_negative(self):
        assert _diff_score(12, 80) == -68.0

    def test_diff_brand_new(self):
        assert _diff_score(55, 0) == 55.0


# -- ratio method --

class TestRatioMethod:
    def test_top3_bursting(self):
        results = detect_bursts(CURR, PREV, k=3, threshold=2.0, method="ratio")
        kws = [kw for kw, _ in results]
        assert "corset top" in kws
        assert "Y2K fashion" in kws
        assert "baggy jeans" in kws

    def test_results_are_sorted(self):
        results = detect_bursts(CURR, PREV, k=5, threshold=1.0, method="ratio")
        scores = [s for _, s in results]
        assert scores == sorted(scores, reverse=True)

    def test_high_threshold_filters_more(self):
        results = detect_bursts(CURR, PREV, k=5, threshold=10.0, method="ratio")
        kws = [kw for kw, _ in results]
        # only corset top (55) and Y2K (18.4) should pass
        assert len(results) == 2
        assert "corset top" in kws
        assert "Y2K fashion" in kws

    def test_nothing_passes_extreme_threshold(self):
        results = detect_bursts(CURR, PREV, k=5, threshold=100.0, method="ratio")
        assert results == []


# -- difference method --

class TestDiffMethod:
    def test_catches_large_jumps(self):
        results = detect_bursts(CURR, PREV, k=3, threshold=10, method="difference")
        kws = [kw for kw, _ in results]
        assert "Y2K fashion" in kws   # +87
        assert "corset top" in kws    # +55

    def test_results_sorted_descending(self):
        results = detect_bursts(CURR, PREV, k=5, threshold=0, method="difference")
        scores = [s for _, s in results]
        assert scores == sorted(scores, reverse=True)


# -- edge cases --

class TestEdgeCases:
    def test_empty_current(self):
        assert detect_bursts({}, PREV, k=5) == []

    def test_empty_previous(self):
        # everything is "new" so score = raw count
        results = detect_bursts({"a": 10, "b": 20}, {}, k=2, threshold=1.0)
        assert len(results) == 2

    def test_k_zero(self):
        assert detect_bursts(CURR, PREV, k=0) == []

    def test_k_negative(self):
        assert detect_bursts(CURR, PREV, k=-1) == []

    def test_same_window_no_bursts(self):
        same = {"a": 50, "b": 30}
        # ratio = 1.0, below threshold of 2.0
        assert detect_bursts(same, same, k=5, threshold=2.0) == []

    def test_bad_method_raises(self):
        with pytest.raises(ValueError):
            detect_bursts(CURR, PREV, k=3, method="invalid")

    def test_single_keyword(self):
        results = detect_bursts({"x": 100}, {"x": 10}, k=1, threshold=2.0)
        assert results == [("x", 10.0)]


# -- ratio vs difference behavior --

class TestMethodComparison:
    def test_ratio_catches_small_base_spike(self):
        """A niche keyword going 1 -> 10 has high ratio but small diff."""
        curr = {"niche": 10}
        prev = {"niche": 1}
        ratio_res = detect_bursts(curr, prev, k=1, threshold=5.0, method="ratio")
        diff_res = detect_bursts(curr, prev, k=1, threshold=5.0, method="difference")
        assert len(ratio_res) == 1   # ratio = 10, passes
        assert len(diff_res) == 1    # diff = 9, also passes 5.0

    def test_diff_catches_large_base_shift(self):
        """A popular keyword going 500 -> 600 has big diff but small ratio."""
        curr = {"popular": 600}
        prev = {"popular": 500}
        ratio_res = detect_bursts(curr, prev, k=1, threshold=2.0, method="ratio")
        diff_res = detect_bursts(curr, prev, k=1, threshold=50.0, method="difference")
        assert len(ratio_res) == 0   # ratio = 1.2, doesn't pass
        assert len(diff_res) == 1    # diff = 100, passes
