"""Tests for cycle_detection.py — slope computation and trend classification."""

import pytest
from cycle_detection import compute_slope, classify_trend


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
        assert compute_slope([0, 5, 10, 15, 20]) == pytest.approx(5.0)


class TestClassify:
    def test_fading(self):
        prev = {"skinny jeans": 80}
        curr = {"skinny jeans": 12}
        assert classify_trend("skinny jeans", curr, prev, 0.15) == "Fading"

    def test_cyclical(self):
        prev = {"cargo pants": 50, "jeans": 30}
        curr = {"cargo pants": 50, "jeans": 30}
        assert classify_trend("cargo pants", curr, prev, 1.1) == "Cyclical"

    def test_new_burst(self):
        prev = {"Y2K fashion": 5, "other": 100}
        curr = {"Y2K fashion": 92, "other": 10}
        assert classify_trend("Y2K fashion", curr, prev, 4.6) == "New"

    def test_new_growing(self):
        prev = {"wide-leg jeans": 20, "other": 50}
        curr = {"wide-leg jeans": 78, "other": 10}
        assert classify_trend("wide-leg jeans", curr, prev, 1.5) == "New"

    def test_decline(self):
        prev = {"retro": 100, "a": 30}
        curr = {"retro": 5, "a": 28}
        assert classify_trend("retro", curr, prev, 0.5) == "Fading"

    def test_flat_is_cyclical(self):
        prev = {"neutral": 30, "x": 100}
        curr = {"neutral": 30, "x": 0}
        assert classify_trend("neutral", curr, prev, 0.8) == "Cyclical"

    def test_brand_new_keyword(self):
        prev = {"other": 50}
        curr = {"corset top": 30, "other": 50}
        assert classify_trend("corset top", curr, prev, 30.0) == "New"

    def test_custom_thresholds(self):
        prev = {"test": 30, "x": 100}
        curr = {"test": 30, "x": 5}
        label = classify_trend("test", curr, prev, 1.5, burst_threshold=1.0)
        assert label == "New"
