"""
test_integration.py — Tests for burst detection, accessibility, synthetic data, and pipeline.
"""

import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from burst_detection import detect_bursts, detect_bursts_ratio, detect_bursts_difference, _compute_score, sweep_thresholds
from accessibility import accessibility_score, accessibility_label, score_keyword
from data.generate_synthetic import (generate_burst_stream, generate_cyclical_stream, generate_fading_stream,
    generate_flat_stream, generate_mixed_stream, generate_scalable_stream, generate_burst_experiment_data)
from main import run_pipeline, _top_k_heap_fallback


class TestBurstDetectionRatio:
    def test_basic_burst(self):
        bursts = detect_bursts_ratio({"A": 50, "B": 22}, {"A": 10, "B": 20}, threshold=2.0)
        keywords = [kw for kw, _ in bursts]
        assert "A" in keywords and "B" not in keywords

    def test_new_keyword_burst(self):
        bursts = detect_bursts_ratio({"A": 10, "B": 30}, {"A": 10}, threshold=2.0)
        assert "B" in [kw for kw, _ in bursts]

    def test_zero_current(self):
        assert detect_bursts_ratio({"A": 0}, {"A": 50}, threshold=2.0) == []

    def test_empty_inputs(self):
        assert detect_bursts_ratio({}, {}) == []

    def test_sorted_descending(self):
        bursts = detect_bursts_ratio({"A": 10, "B": 20, "C": 5}, {"A": 1, "B": 1, "C": 1}, threshold=2.0)
        scores = [s for _, s in bursts]
        assert scores == sorted(scores, reverse=True)


class TestBurstDetectionDifference:
    def test_basic_burst(self):
        bursts = detect_bursts_difference({"A": 12, "B": 600}, {"A": 10, "B": 500}, threshold=50)
        keywords = [kw for kw, _ in bursts]
        assert "B" in keywords and "A" not in keywords

    def test_negative_change(self):
        assert detect_bursts_difference({"A": 50}, {"A": 100}, threshold=5) == []

    def test_empty_inputs(self):
        assert detect_bursts_difference({}, {}) == []


class TestBurstScoring:
    def test_ratio_score(self):
        assert _compute_score(50, 10, "ratio") == 5.0
    def test_ratio_zero_previous(self):
        assert _compute_score(30, 0, "ratio") == 30.0
    def test_difference_score(self):
        assert _compute_score(100, 40, "difference") == 60
    def test_invalid_method(self):
        with pytest.raises(ValueError): _compute_score(10, 5, "invalid")


class TestBurstTopK:
    def test_top_k_limits_results(self):
        prev = {f"k{i}": 1 for i in range(10)}
        curr = {f"k{i}": 100 for i in range(10)}
        assert len(detect_bursts(curr, prev, threshold=2.0, method="ratio", top_k=3)) == 3


class TestSweepThresholds:
    def test_basic_sweep(self):
        prev, curr, truth = generate_burst_experiment_data(n_keywords=10, n_true_bursts=3)
        results = sweep_thresholds(curr, prev, truth, thresholds=[1.0, 2.0, 5.0, 10.0], method="ratio")
        assert len(results) == 4
        assert results[0]["detection_rate"] >= results[-1]["detection_rate"]


class TestAccessibility:
    def test_known_keyword(self):
        score = accessibility_score("wide-leg jeans")
        assert score is not None and 0.0 <= score <= 1.0
    def test_unknown_keyword(self):
        score = accessibility_score("nonexistent_item_xyz")
        assert score == 0.5
    def test_label_highly_accessible(self):
        assert accessibility_label(0.85) == "Highly Accessible"
    def test_label_moderate(self):
        assert accessibility_label(0.55) == "Moderately Accessible"
    def test_label_low(self):
        assert accessibility_label(0.2) == "Low Accessibility"
    def test_label_default(self):
        score = accessibility_score("nonexistent_item_xyz")
        assert accessibility_label(score) == "Moderately Accessible"
    def test_score_keyword_returns_tuple(self):
        sc, lbl = score_keyword("mom jeans")
        assert isinstance(sc, float) and isinstance(lbl, str)
    def test_all_10_keywords_have_scores(self):
        from config import FASHION_KEYWORDS
        for kw in FASHION_KEYWORDS:
            assert accessibility_score(kw) is not None, f"Missing: {kw}"


class TestSyntheticData:
    def test_burst_stream(self):
        events = generate_burst_stream(n_events=100)
        assert len(events) > 0 and all(isinstance(e, tuple) and len(e) == 2 for e in events)
    def test_cyclical_stream(self):
        assert len(generate_cyclical_stream(n_events=200)) > 0
    def test_fading_stream(self):
        assert len(generate_fading_stream(n_events=100)) > 0
    def test_flat_stream(self):
        assert len(generate_flat_stream(n_events=100)) > 0
    def test_mixed_stream(self):
        events = generate_mixed_stream(n_events_per_keyword=50)
        assert len(events) > 0 and len(set(kw for _, kw in events)) > 1
    def test_scalable_stream_exact_count(self):
        assert len(generate_scalable_stream(1000, n_keywords=5)) == 1000
    def test_mixed_stream_sorted(self):
        events = generate_mixed_stream(n_events_per_keyword=50)
        timestamps = [t for t, _ in events]
        assert timestamps == sorted(timestamps)
    def test_burst_experiment_data(self):
        prev, curr, truth = generate_burst_experiment_data(n_keywords=20, n_true_bursts=5)
        assert len(prev) == 20 and len(truth) == 5
        for kw in truth: assert curr[kw] > prev[kw]


class TestPipeline:
    def test_pipeline_runs(self):
        events = generate_mixed_stream(n_events_per_keyword=100)
        assert len(run_pipeline(events, window_size=500, k=3, snapshot_interval=50)) > 0
    def test_pipeline_snapshot_structure(self):
        events = generate_mixed_stream(n_events_per_keyword=100)
        results = run_pipeline(events, window_size=500, k=3, snapshot_interval=50)
        required = {"timestamp", "event_index", "freq_map", "top_k", "bursts", "classifications", "scored_trends"}
        for s in results: assert required.issubset(s.keys())
    def test_pipeline_top_k_count(self):
        events = generate_mixed_stream(n_events_per_keyword=200)
        for s in run_pipeline(events, window_size=1000, k=5, snapshot_interval=100):
            assert len(s["top_k"]) <= 5
    def test_pipeline_scored_trends_have_accessibility(self):
        events = generate_mixed_stream(n_events_per_keyword=200)
        for s in run_pipeline(events, window_size=1000, k=5, snapshot_interval=100):
            for t in s["scored_trends"]:
                assert "accessibility" in t and "access_label" in t
    def test_pipeline_empty_stream(self):
        assert run_pipeline([], window_size=100, k=3) == []
    def test_pipeline_single_event(self):
        assert run_pipeline([(0, "jeans")], window_size=100, k=3, snapshot_interval=50) == []


class TestEdgeCases:
    def test_burst_single_keyword(self):
        assert len(detect_bursts_ratio({"A": 50}, {"A": 5}, threshold=2.0)) == 1
    def test_burst_all_same_score(self):
        assert len(detect_bursts_ratio({"A": 30, "B": 30, "C": 30}, {"A": 10, "B": 10, "C": 10}, threshold=2.0)) == 3
    def test_top_k_fallback_with_ties(self):
        assert len(_top_k_heap_fallback({"A": 100, "B": 100, "C": 100, "D": 50, "E": 50}, 3)) == 3
    def test_top_k_fallback_k_larger(self):
        assert len(_top_k_heap_fallback({"A": 10, "B": 20}, 10)) == 2
    def test_pipeline_large_window(self):
        assert len(run_pipeline(generate_scalable_stream(100), window_size=999999, k=3, snapshot_interval=20)) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
