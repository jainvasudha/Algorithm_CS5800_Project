"""
accessibility.py — Weighted Multi-Criteria Accessibility Scoring (Parvathi / Shravya).

Algorithm design:
  1. Each fashion keyword has 5 accessibility factors (binary or ordinal).
  2. Every factor is min-max normalised to [0, 1] so different scales are comparable.
  3. A weighted sum produces a composite score in [0, 1].
  4. A min-heap of size K is used to rank the Top-K most accessible trends —
     reusing the same heap pattern from Module B (Top-K selection).

Time complexity : O(T · F + T · log K)
                  T = number of trends, F = number of factors (constant = 5),
                  simplifies to O(T log K).
Space complexity: O(K) for the heap  +  O(V · F) for the accessibility database.
"""

import heapq
import json
import os
from typing import Dict, List, Optional, Tuple

from config import ACCESSIBILITY_WEIGHTS, ACCESSIBILITY_RANGES


# ── Normalisation helper ───────────────────────────────────────────────────────

def _normalise(value: float, lo: float, hi: float) -> float:
    """Min-max normalise `value` from [lo, hi] to [0, 1].
    Returns 1.0 if lo == hi (degenerate range).
    """
    if hi == lo:
        return 1.0
    return (value - lo) / (hi - lo)


# ── Single-item scoring ────────────────────────────────────────────────────────

def compute_accessibility_score(
    keyword: str,
    accessibility_db: Dict,
    weights: Optional[Dict[str, float]] = None,
) -> Tuple[float, str]:
    """
    Compute the weighted accessibility score for one keyword.

    Parameters
    ----------
    keyword          : fashion keyword to look up.
    accessibility_db : dict mapping keyword → {factor: raw_value, ...}
    weights          : optional override; uses config defaults if None.

    Returns
    -------
    (score_0_to_1, label)   where label ∈ {Highly Accessible, Moderately Accessible,
                                            Limited Accessibility, Low Accessibility,
                                            NO_DATA}
    """
    if weights is None:
        weights = ACCESSIBILITY_WEIGHTS

    if keyword not in accessibility_db:
        return (0.0, "NO_DATA")

    factors = accessibility_db[keyword]
    score = 0.0

    for factor, w in weights.items():
        raw = factors.get(factor, 0)
        lo, hi = ACCESSIBILITY_RANGES[factor]
        normalised = _normalise(raw, lo, hi)
        score += w * normalised

    label = _classify_score(score)
    return (round(score, 4), label)


def _classify_score(score: float) -> str:
    if score >= 0.80:
        return "Highly Accessible"
    if score >= 0.55:
        return "Moderately Accessible"
    if score >= 0.30:
        return "Limited Accessibility"
    return "Low Accessibility"


# ── Batch ranking using a min-heap ─────────────────────────────────────────────

def rank_by_accessibility(
    trends: List[Dict],
    accessibility_db: Dict,
    k: int,
    weights: Optional[Dict[str, float]] = None,
) -> Tuple[List[Dict], List[str]]:
    """
    Rank a list of detected trends by accessibility score and return the Top-K.

    Uses a min-heap of size K so we never store more than K items at once:
      - For each of T trends, one heap.push/pop operation → O(log K).
      - Total: O(T log K).
    Compare against the naive approach of sorting all T items → O(T log T).

    Parameters
    ----------
    trends           : list of dicts with at least a "keyword" key.
    accessibility_db : accessibility lookup table.
    k                : number of top accessible trends to return.
    weights          : optional weight override.

    Returns
    -------
    (top_k_trends_sorted_desc, alert_keywords)
    alert_keywords = items with label NO_DATA or Low Accessibility.
    """
    if k <= 0:
        return ([], [])

    min_heap: List[Tuple[float, int, Dict]] = []   # (score, idx, trend_dict)
    alerts: List[str] = []

    for idx, trend in enumerate(trends):
        kw = trend.get("keyword", "")
        score, label = compute_accessibility_score(kw, accessibility_db, weights)

        # Attach score info to a copy of the trend dict
        enriched = dict(trend)
        enriched["accessibility_score"] = score
        enriched["accessibility_label"] = label

        if label in ("NO_DATA", "Low Accessibility"):
            alerts.append(kw)

        # Maintain min-heap of size k
        if len(min_heap) < k:
            heapq.heappush(min_heap, (score, idx, enriched))
        elif score > min_heap[0][0]:
            heapq.heapreplace(min_heap, (score, idx, enriched))

    # Extract heap contents and sort descending
    top_k = sorted(min_heap, key=lambda x: x[0], reverse=True)
    return ([item[2] for item in top_k], alerts)


# ── Database loader ────────────────────────────────────────────────────────────

def load_accessibility_db(path: str) -> Dict:
    """Load the JSON accessibility database from disk."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Accessibility DB not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
