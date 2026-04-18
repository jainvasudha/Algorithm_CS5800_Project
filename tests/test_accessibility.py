"""
test_accessibility.py — Unit tests for accessibility.py (Parvathi / Shravya).

Run with:  pytest tests/test_accessibility.py -v
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from accessibility import (
    compute_accessibility_score,
    rank_by_accessibility,
    _normalise,
    _classify_score,
)


# ── Sample database fixture ───────────────────────────────────────────────────

SAMPLE_DB = {
    "hoodie": {
        "wheelchair_friendly":  1,
        "adaptive_wearability": 5,
        "size_inclusive":       5,
        "sensory_friendly":     1,
        "price_accessibility":  5,
    },
    "skinny jeans": {
        "wheelchair_friendly":  0,
        "adaptive_wearability": 2,
        "size_inclusive":       3,
        "sensory_friendly":     0,
        "price_accessibility":  4,
    },
    "high heels": {
        "wheelchair_friendly":  0,
        "adaptive_wearability": 1,
        "size_inclusive":       2,
        "sensory_friendly":     0,
        "price_accessibility":  3,
    },
}


# ── _normalise ────────────────────────────────────────────────────────────────

def test_normalise_midpoint():
    assert _normalise(3, 1, 5) == pytest.approx(0.5)

def test_normalise_min():
    assert _normalise(1, 1, 5) == pytest.approx(0.0)

def test_normalise_max():
    assert _normalise(5, 1, 5) == pytest.approx(1.0)

def test_normalise_degenerate_range():
    assert _normalise(3, 3, 3) == 1.0

def test_normalise_binary_one():
    assert _normalise(1, 0, 1) == pytest.approx(1.0)

def test_normalise_binary_zero():
    assert _normalise(0, 0, 1) == pytest.approx(0.0)


# ── _classify_score ───────────────────────────────────────────────────────────

def test_classify_highly_accessible():
    assert _classify_score(0.90) == "Highly Accessible"

def test_classify_moderately_accessible():
    assert _classify_score(0.60) == "Moderately Accessible"

def test_classify_limited():
    assert _classify_score(0.40) == "Limited Accessibility"

def test_classify_low():
    assert _classify_score(0.10) == "Low Accessibility"

def test_classify_boundary_at_080():
    assert _classify_score(0.80) == "Highly Accessible"

def test_classify_boundary_just_below_080():
    assert _classify_score(0.799) == "Moderately Accessible"


# ── compute_accessibility_score ───────────────────────────────────────────────

def test_score_missing_keyword():
    score, label = compute_accessibility_score("unknown item", SAMPLE_DB)
    assert score == 0.0
    assert label == "NO_DATA"

def test_score_range_is_0_to_1():
    for kw in SAMPLE_DB:
        score, _ = compute_accessibility_score(kw, SAMPLE_DB)
        assert 0.0 <= score <= 1.0, f"Score out of range for {kw}: {score}"

def test_score_hoodie_is_high():
    """Hoodie has max scores on all factors → should be Highly Accessible."""
    score, label = compute_accessibility_score("hoodie", SAMPLE_DB)
    assert score == pytest.approx(1.0)
    assert label == "Highly Accessible"

def test_score_high_heels_is_low():
    """High heels have low scores → should not be Highly Accessible."""
    score, label = compute_accessibility_score("high heels", SAMPLE_DB)
    assert label in ("Low Accessibility", "Limited Accessibility")

def test_score_ranking_order():
    """hoodie should score higher than skinny jeans which scores higher than high heels."""
    s_hoodie, _ = compute_accessibility_score("hoodie", SAMPLE_DB)
    s_skinny, _ = compute_accessibility_score("skinny jeans", SAMPLE_DB)
    s_heels,  _ = compute_accessibility_score("high heels", SAMPLE_DB)
    assert s_hoodie > s_skinny > s_heels

def test_custom_weights_sum_to_one():
    """Custom weights that change importance of price."""
    custom = {
        "wheelchair_friendly":  0.10,
        "adaptive_wearability": 0.10,
        "size_inclusive":       0.10,
        "sensory_friendly":     0.10,
        "price_accessibility":  0.60,  # price dominates
    }
    score, _ = compute_accessibility_score("skinny jeans", SAMPLE_DB, custom)
    assert 0.0 <= score <= 1.0


# ── rank_by_accessibility ─────────────────────────────────────────────────────

def test_rank_empty_trends():
    ranked, alerts = rank_by_accessibility([], SAMPLE_DB, k=5)
    assert ranked == []
    assert alerts == []

def test_rank_k_zero():
    trends = [{"keyword": "hoodie"}]
    ranked, alerts = rank_by_accessibility(trends, SAMPLE_DB, k=0)
    assert ranked == []

def test_rank_returns_at_most_k():
    trends = [{"keyword": kw} for kw in SAMPLE_DB]
    ranked, _ = rank_by_accessibility(trends, SAMPLE_DB, k=2)
    assert len(ranked) <= 2

def test_rank_sorted_descending():
    """Returned list must be in descending order of accessibility_score."""
    trends = [{"keyword": kw} for kw in SAMPLE_DB]
    ranked, _ = rank_by_accessibility(trends, SAMPLE_DB, k=3)
    scores = [r["accessibility_score"] for r in ranked]
    assert scores == sorted(scores, reverse=True)

def test_rank_hoodie_first():
    """Hoodie has the highest score and should appear first."""
    trends = [{"keyword": kw} for kw in SAMPLE_DB]
    ranked, _ = rank_by_accessibility(trends, SAMPLE_DB, k=3)
    assert ranked[0]["keyword"] == "hoodie"

def test_rank_alerts_contain_missing():
    trends = [{"keyword": "hoodie"}, {"keyword": "unknown item"}]
    _, alerts = rank_by_accessibility(trends, SAMPLE_DB, k=5)
    assert "unknown item" in alerts

def test_rank_enriches_dicts():
    """Each returned record should have accessibility_score and accessibility_label keys."""
    trends = [{"keyword": "hoodie", "frequency": 42}]
    ranked, _ = rank_by_accessibility(trends, SAMPLE_DB, k=1)
    assert "accessibility_score" in ranked[0]
    assert "accessibility_label" in ranked[0]
    assert ranked[0]["frequency"] == 42   # original data preserved
