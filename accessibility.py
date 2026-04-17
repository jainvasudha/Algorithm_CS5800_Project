"""
accessibility.py — Weighted accessibility scoring for fashion keywords.

Score = sum(weight_i * dimension_i) for dimensions:
    price, availability, versatility, size_inclusivity
"""

import json
import os

from config import ACCESSIBILITY_WEIGHTS, ACCESSIBILITY_LABELS

_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "accessibility_db.json")

with open(_DB_PATH, "r") as f:
    _ACCESS_DB = json.load(f)


_DEFAULT_SCORES = {"price": 0.5, "availability": 0.5, "versatility": 0.5, "size_inclusivity": 0.5}


def accessibility_score(keyword):
    entry = _ACCESS_DB.get(keyword, _DEFAULT_SCORES)
    score = sum(
        ACCESSIBILITY_WEIGHTS[dim] * entry.get(dim, 0.5)
        for dim in ACCESSIBILITY_WEIGHTS
    )
    return round(score, 4)


def accessibility_label(score):
    for (lo, hi), label in ACCESSIBILITY_LABELS.items():
        if lo <= score <= hi:
            return label
    return "Unknown"


def score_keyword(keyword):
    sc = accessibility_score(keyword)
    return sc, accessibility_label(sc)


def score_all_keywords(keywords):
    results = []
    for kw in keywords:
        sc, lbl = score_keyword(kw)
        results.append({"keyword": kw, "score": sc, "label": lbl})
    return results


if __name__ == "__main__":
    test_keywords = ["wide-leg jeans", "corset top", "hoodie", "unknown_item"]
    for kw in test_keywords:
        sc, lbl = score_keyword(kw)
        print(f"  {kw:20s} → score={sc}, label={lbl}")
