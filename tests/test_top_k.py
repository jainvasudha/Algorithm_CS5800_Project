"""
Tests for Top-K Selection (heap-based and sort-based).
Covers: basic usage, ties, edge cases, and heap-vs-sort equivalence.
"""

import pytest
from top_k import top_k_heap, top_k_sort


# ── Sample data ──────────────────────────────────────────────

FREQ_MAP = {
    "wide-leg jeans": 78,
    "cargo pants": 45,
    "skinny jeans": 12,
    "Y2K fashion": 92,
    "mom jeans": 34,
    "baggy jeans": 67,
    "flared pants": 23,
    "corset top": 55,
    "low-rise jeans": 41,
    "oversized blazer": 38,
}

TIED_FREQ_MAP = {
    "alpha": 50,
    "beta": 50,
    "gamma": 50,
    "delta": 30,
    "epsilon": 30,
}


# ── Basic functionality ──────────────────────────────────────

class TestTopKBasic:
    def test_heap_returns_correct_top_3(self):
        result = top_k_heap(FREQ_MAP, 3)
        keywords = [kw for kw, _ in result]
        assert keywords == ["Y2K fashion", "wide-leg jeans", "baggy jeans"]

    def test_sort_returns_correct_top_3(self):
        result = top_k_sort(FREQ_MAP, 3)
        keywords = [kw for kw, _ in result]
        assert keywords == ["Y2K fashion", "wide-leg jeans", "baggy jeans"]

    def test_heap_returns_correct_top_5(self):
        result = top_k_heap(FREQ_MAP, 5)
        keywords = [kw for kw, _ in result]
        assert keywords == ["Y2K fashion", "wide-leg jeans", "baggy jeans",
                            "corset top", "cargo pants"]

    def test_sort_returns_correct_top_5(self):
        result = top_k_sort(FREQ_MAP, 5)
        keywords = [kw for kw, _ in result]
        assert keywords == ["Y2K fashion", "wide-leg jeans", "baggy jeans",
                            "corset top", "cargo pants"]

    def test_results_sorted_descending(self):
        result = top_k_heap(FREQ_MAP, 5)
        counts = [count for _, count in result]
        assert counts == sorted(counts, reverse=True)


# ── Tie-breaking ─────────────────────────────────────────────

class TestTopKTies:
    def test_heap_breaks_ties_alphabetically(self):
        result = top_k_heap(TIED_FREQ_MAP, 3)
        keywords = [kw for kw, _ in result]
        # All three 50s: alpha, beta, gamma (alphabetical)
        assert keywords == ["alpha", "beta", "gamma"]

    def test_sort_breaks_ties_alphabetically(self):
        result = top_k_sort(TIED_FREQ_MAP, 3)
        keywords = [kw for kw, _ in result]
        assert keywords == ["alpha", "beta", "gamma"]

    def test_all_same_frequency(self):
        same = {"a": 10, "b": 10, "c": 10, "d": 10}
        result_heap = top_k_heap(same, 2)
        result_sort = top_k_sort(same, 2)
        assert result_heap == [("a", 10), ("b", 10)]
        assert result_sort == [("a", 10), ("b", 10)]


# ── Edge cases ───────────────────────────────────────────────

class TestTopKEdgeCases:
    def test_empty_freq_map(self):
        assert top_k_heap({}, 5) == []
        assert top_k_sort({}, 5) == []

    def test_k_zero(self):
        assert top_k_heap(FREQ_MAP, 0) == []
        assert top_k_sort(FREQ_MAP, 0) == []

    def test_k_negative(self):
        assert top_k_heap(FREQ_MAP, -1) == []
        assert top_k_sort(FREQ_MAP, -1) == []

    def test_k_greater_than_m(self):
        """K > number of items → return all items."""
        small = {"a": 5, "b": 3}
        result_heap = top_k_heap(small, 10)
        result_sort = top_k_sort(small, 10)
        assert result_heap == [("a", 5), ("b", 3)]
        assert result_sort == [("a", 5), ("b", 3)]

    def test_single_item(self):
        single = {"only": 42}
        assert top_k_heap(single, 1) == [("only", 42)]
        assert top_k_sort(single, 1) == [("only", 42)]

    def test_k_equals_m(self):
        """K == M → both methods return everything."""
        result_heap = top_k_heap(FREQ_MAP, len(FREQ_MAP))
        result_sort = top_k_sort(FREQ_MAP, len(FREQ_MAP))
        assert result_heap == result_sort


# ── Heap vs Sort equivalence ─────────────────────────────────

class TestHeapMatchesSort:
    def test_same_set_top_3(self):
        heap_result = top_k_heap(FREQ_MAP, 3)
        sort_result = top_k_sort(FREQ_MAP, 3)
        assert set(heap_result) == set(sort_result)

    def test_same_set_top_5(self):
        heap_result = top_k_heap(FREQ_MAP, 5)
        sort_result = top_k_sort(FREQ_MAP, 5)
        assert set(heap_result) == set(sort_result)

    def test_exact_match_with_ties(self):
        """With alphabetical tiebreak, order should match exactly."""
        heap_result = top_k_heap(TIED_FREQ_MAP, 4)
        sort_result = top_k_sort(TIED_FREQ_MAP, 4)
        assert heap_result == sort_result

    def test_exact_match_all_items(self):
        heap_result = top_k_heap(FREQ_MAP, len(FREQ_MAP))
        sort_result = top_k_sort(FREQ_MAP, len(FREQ_MAP))
        assert heap_result == sort_result
