"""
run_experiments.py — Scalability Benchmarking Harness (Parvathi / Shravya).

Runs the four core experiments described in the project proposal:

  Experiment 1: Sliding Window — Incremental vs Baseline
    Vary stream size N, compare O(1)-amortised vs O(N)-per-query runtime.

  Experiment 2: Top-K — Heap vs Sort
    Vary M (distinct keywords) and K, compare O(M log K) vs O(M log M).

  Experiment 3: Burst Detection — Ratio vs Difference
    Inject known bursts, vary threshold, measure true-positive and false-positive rate.

  Experiment 4: End-to-End Pipeline Scalability
    Vary N, measure total wall-clock time for the full pipeline.

Results are saved to results/ as JSON files that plot_results.py reads.

Measurement tools used:
  time.perf_counter() — high-resolution wall-clock timer
  tracemalloc         — Python built-in memory profiler
"""

import json
import os
import sys
import time
import tracemalloc
from typing import Dict, List, Tuple

# Make project root importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.stubs import (
    SlidingWindowEngine,
    recompute_frequencies,
    top_k_heap,
    top_k_sort,
    detect_bursts,
)
from data.generate_synthetic import generate_large_stream, generate_burst

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _save(name: str, data: dict) -> None:
    path = os.path.join(RESULTS_DIR, f"{name}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  Saved → {path}")


# ── Experiment 1: Sliding Window Scalability ──────────────────────────────────

def experiment1_sliding_window(
    stream_sizes: List[int] = None,
    window_size: int = 12,
    n_keywords: int = 10,
) -> Dict:
    """
    For each stream size N:
      - INCREMENTAL: feed events one-by-one through SlidingWindowEngine.
      - BASELINE: after every event call recompute_frequencies() over ALL past events.

    Expected result: incremental runtime ≈ flat (O(N) total / O(1) amortised per event);
    baseline runtime ≈ quadratic (O(N^2) total / O(N) per query).
    """
    if stream_sizes is None:
        stream_sizes = [1_000, 5_000, 10_000, 50_000, 100_000]

    print("\n[Experiment 1] Sliding Window: Incremental vs Baseline")

    inc_times, base_times = [], []

    for N in stream_sizes:
        events = generate_large_stream(N, n_keywords)

        # ── Incremental ──────────────────────────────────────
        engine = SlidingWindowEngine(window_size)
        t0 = time.perf_counter()
        for ts, kw in events:
            engine.process_event(ts, kw)
        inc_times.append(time.perf_counter() - t0)

        # ── Baseline (sample every 50th query to keep runtime tractable) ──
        t0 = time.perf_counter()
        for i, (ts, _kw) in enumerate(events):
            if i % 50 == 0:
                recompute_frequencies(events[:i+1], ts, window_size)
        base_times.append(time.perf_counter() - t0)

        print(f"  N={N:>7}  incremental={inc_times[-1]*1000:7.1f}ms  "
              f"baseline={base_times[-1]*1000:7.1f}ms")

    result = {
        "stream_sizes": stream_sizes,
        "incremental_ms": [t * 1000 for t in inc_times],
        "baseline_ms":    [t * 1000 for t in base_times],
        "window_size": window_size,
    }
    _save("exp1_sliding_window", result)
    return result


# ── Experiment 2: Top-K Heap vs Sort ─────────────────────────────────────────

def experiment2_topk(
    m_values: List[int] = None,
    k_values: List[int] = None,
) -> Dict:
    """
    For each (M, K) combination:
      Build a synthetic freq_map with M distinct keywords.
      Time top_k_heap() vs top_k_sort().

    Expected result: heap wins when K << M; they converge as K → M.
    """
    if m_values is None:
        m_values = [50, 100, 500, 1_000, 5_000]
    if k_values is None:
        k_values = [5, 10, 50, 100, 500]

    print("\n[Experiment 2] Top-K: Heap vs Sort")

    records = []
    import random
    rng = random.Random(99)

    for M in m_values:
        freq_map = {f"kw_{i}": rng.randint(1, 1000) for i in range(M)}
        for K in k_values:
            if K > M:
                continue

            # Heap
            t0 = time.perf_counter()
            for _ in range(200):      # repeat 200× for timing precision
                top_k_heap(freq_map, K)
            heap_ms = (time.perf_counter() - t0) / 200 * 1000

            # Sort
            t0 = time.perf_counter()
            for _ in range(200):
                top_k_sort(freq_map, K)
            sort_ms = (time.perf_counter() - t0) / 200 * 1000

            records.append({"M": M, "K": K, "heap_ms": round(heap_ms, 4),
                             "sort_ms": round(sort_ms, 4)})
            print(f"  M={M:>5}  K={K:>4}  heap={heap_ms:.4f}ms  sort={sort_ms:.4f}ms")

    result = {"records": records, "m_values": m_values, "k_values": k_values}
    _save("exp2_topk", result)
    return result


# ── Experiment 3: Burst Detection Sensitivity ─────────────────────────────────

def experiment3_burst_sensitivity(
    thresholds: List[float] = None,
    n_true_bursts: int = 5,
    background: int = 3,
    spike_height: int = 60,
) -> Dict:
    """
    Inject `n_true_bursts` known burst keywords into a stream of non-bursting keywords.
    For each threshold and each scoring method (ratio / difference):
      - Count true positives detected.
      - Count false positives from the non-bursting keywords.

    Expected result: ratio method catches proportional spikes better at low thresholds;
    difference method scales with absolute magnitude.
    """
    if thresholds is None:
        thresholds = [1.5, 2.0, 3.0, 5.0, 8.0, 10.0]

    print("\n[Experiment 3] Burst Detection: Ratio vs Difference sensitivity")

    # Build current and previous freq_map with injected bursts
    n_background = 20
    prev_freq = {f"bg_{i}": background for i in range(n_background)}
    curr_freq = {f"bg_{i}": background + 1 for i in range(n_background)}   # tiny change

    true_keywords = [f"burst_{i}" for i in range(n_true_bursts)]
    for kw in true_keywords:
        prev_freq[kw] = background
        curr_freq[kw] = spike_height

    records = []
    for method in ("ratio", "difference"):
        for thresh in thresholds:
            detected = detect_bursts(curr_freq, prev_freq, k=len(curr_freq),
                                     threshold=thresh, method=method)
            det_kws = {kw for kw, _ in detected}
            tp = sum(1 for kw in true_keywords if kw in det_kws)
            fp = sum(1 for kw in det_kws if kw not in true_keywords)
            records.append({
                "method": method, "threshold": thresh,
                "true_positives": tp, "false_positives": fp,
                "total_detected": len(det_kws),
            })
            print(f"  method={method:<12}  thresh={thresh:5.1f}  "
                  f"TP={tp}  FP={fp}")

    result = {
        "records": records,
        "thresholds": thresholds,
        "n_true_bursts": n_true_bursts,
    }
    _save("exp3_burst", result)
    return result


# ── Experiment 4: End-to-End Pipeline Memory + Runtime ───────────────────────

def experiment4_end_to_end(
    stream_sizes: List[int] = None,
    window_size: int = 12,
    k: int = 5,
) -> Dict:
    """
    For each stream size N, run the full pipeline and measure:
      - Wall-clock total runtime.
      - Peak memory usage (tracemalloc).
    """
    if stream_sizes is None:
        stream_sizes = [1_000, 5_000, 10_000, 50_000]

    print("\n[Experiment 4] End-to-End Pipeline Scalability")

    # Import run_pipeline — we only import once here to avoid circular issues
    from src.main import run_pipeline

    runtimes, memories = [], []

    for N in stream_sizes:
        events = generate_large_stream(N, n_keywords=10)

        tracemalloc.start()
        t0 = time.perf_counter()
        run_pipeline(events, accessibility_db={}, window_size=window_size, k=k, verbose=False)
        elapsed = time.perf_counter() - t0
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        runtimes.append(elapsed * 1000)
        memories.append(peak / 1024)   # KB
        print(f"  N={N:>7}  time={elapsed*1000:8.1f}ms  peak_mem={peak/1024:.1f}KB")

    result = {
        "stream_sizes": stream_sizes,
        "runtime_ms": runtimes,
        "memory_kb": memories,
    }
    _save("exp4_e2e", result)
    return result


# ── Run all ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("CS5800 — Scalability Experiments (Parvathi / Shravya)")
    print("=" * 60)

    r1 = experiment1_sliding_window()
    r2 = experiment2_topk()
    r3 = experiment3_burst_sensitivity()
    r4 = experiment4_end_to_end()

    print("\n✓ All experiments complete. Results saved to results/")
    print("  Run:  python experiments/plot_results.py")
