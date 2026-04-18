"""
experiments.py — Scalability Benchmarking Harness.

Runs four core experiments:

  Experiment 1: Sliding Window — Incremental vs Baseline
  Experiment 2: Top-K — Heap vs Sort
  Experiment 3: Burst Detection — Ratio vs Difference sensitivity
  Experiment 4: End-to-End Pipeline Scalability

Results are saved to experiment_results.json.

Measurement tools:
  time.perf_counter() — high-resolution wall-clock timer
  tracemalloc         — Python built-in memory profiler
"""

import json
import os
import random
import sys
import time
import tracemalloc
from collections import deque
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sliding_window import add_event, get_frequencies, reset_window
from baseline import compute_baseline
from top_k import top_k_heap, top_k_sort
from burst_detection import detect_bursts
from data.generate_synthetic import generate_large_stream

RESULTS_PATH = os.path.join(os.path.dirname(__file__), "experiment_results.json")


def _save_all(results: dict) -> None:
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved → {RESULTS_PATH}")


# ── Experiment 1: Sliding Window Scalability ──────────────────────────────────

def experiment1_sliding_window(
    stream_sizes: List[int] = None,
    window_size: int = 12,
) -> list:
    if stream_sizes is None:
        stream_sizes = [1_000, 5_000, 10_000, 50_000, 100_000]

    print("\n[Experiment 1] Sliding Window: Incremental vs Baseline")
    records = []

    for N in stream_sizes:
        events = generate_large_stream(N, n_keywords=10)

        # Incremental (deque + hash map)
        reset_window()
        t0 = time.perf_counter()
        for ts, kw in events:
            add_event(ts, kw, window_size)
        smart_time = time.perf_counter() - t0
        reset_window()

        # Baseline (query every 50th event to keep tractable)
        t0 = time.perf_counter()
        for i, (ts, _) in enumerate(events):
            if i % 50 == 0:
                compute_baseline(events[:i + 1], ts, window_size)
        naive_time = time.perf_counter() - t0

        records.append({"n": N, "naive_time": naive_time, "smart_time": smart_time})
        print(f"  N={N:>7,}  naive={naive_time*1000:>9.1f}ms  smart={smart_time*1000:>7.1f}ms  "
              f"speedup={naive_time/max(smart_time, 1e-9):,.0f}x")

    return records


# ── Experiment 2: Top-K Heap vs Sort ─────────────────────────────────────────

def experiment2_topk(
    m_values: List[int] = None,
    k_values: List[int] = None,
) -> tuple:
    if m_values is None:
        m_values = [50, 100, 500, 1_000, 5_000]
    if k_values is None:
        k_values = [5, 10, 50, 100, 500]

    print("\n[Experiment 2] Top-K: Heap vs Sort")

    rng = random.Random(42)
    vary_m_records = []
    vary_k_records = []

    # 2a: vary M, fix K=5
    K_FIXED = 5
    for M in m_values:
        freq_map = {f"kw_{i}": rng.randint(1, 10_000) for i in range(M)}

        t0 = time.perf_counter()
        for _ in range(200):
            top_k_heap(freq_map, K_FIXED)
        heap_time = (time.perf_counter() - t0) / 200

        t0 = time.perf_counter()
        for _ in range(200):
            top_k_sort(freq_map, K_FIXED)
        sort_time = (time.perf_counter() - t0) / 200

        vary_m_records.append({"m": M, "heap_time": heap_time, "sort_time": sort_time})
        print(f"  M={M:>5}  K={K_FIXED}  heap={heap_time*1e6:.1f}μs  sort={sort_time*1e6:.1f}μs")

    # 2b: vary K, fix M=1000
    M_FIXED = 1_000
    freq_map = {f"kw_{i}": rng.randint(1, 10_000) for i in range(M_FIXED)}
    for K in k_values:
        if K > M_FIXED:
            continue

        t0 = time.perf_counter()
        for _ in range(200):
            top_k_heap(freq_map, K)
        heap_time = (time.perf_counter() - t0) / 200

        t0 = time.perf_counter()
        for _ in range(200):
            top_k_sort(freq_map, K)
        sort_time = (time.perf_counter() - t0) / 200

        vary_k_records.append({"k": K, "heap_time": heap_time, "sort_time": sort_time})
        print(f"  M={M_FIXED}  K={K:>4}  heap={heap_time*1e6:.1f}μs  sort={sort_time*1e6:.1f}μs")

    return vary_m_records, vary_k_records


# ── Experiment 3: Burst Detection Sensitivity ─────────────────────────────────

def experiment3_burst(
    n_true_bursts: int = 5,
    background: int = 3,
    spike_height: int = 60,
) -> dict:
    ratio_thresholds = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.0, 10.0]
    diff_thresholds = [5, 10, 15, 20, 30, 50, 75, 100, 150]

    print("\n[Experiment 3] Burst Detection: Ratio vs Difference sensitivity")

    # Build freq maps with injected bursts
    n_background = 20
    prev_freq = {f"bg_{i}": background for i in range(n_background)}
    curr_freq = {f"bg_{i}": background + 1 for i in range(n_background)}

    true_keywords = set()
    for i in range(n_true_bursts):
        kw = f"burst_{i}"
        true_keywords.add(kw)
        prev_freq[kw] = background
        curr_freq[kw] = spike_height

    total_non_burst = len(prev_freq) - n_true_bursts

    ratio_results = []
    for t in ratio_thresholds:
        detected = detect_bursts(curr_freq, prev_freq, threshold=t, method="ratio")
        det_kws = {kw for kw, _ in detected}
        tp = len(det_kws & true_keywords)
        fp = len(det_kws - true_keywords)
        ratio_results.append({
            "threshold": t, "true_positives": tp, "false_positives": fp,
            "detection_rate": tp / n_true_bursts,
            "false_positive_rate": fp / max(total_non_burst, 1),
        })
        print(f"  ratio   thresh={t:5.1f}  TP={tp}  FP={fp}")

    diff_results = []
    for t in diff_thresholds:
        detected = detect_bursts(curr_freq, prev_freq, threshold=t, method="difference")
        det_kws = {kw for kw, _ in detected}
        tp = len(det_kws & true_keywords)
        fp = len(det_kws - true_keywords)
        diff_results.append({
            "threshold": t, "true_positives": tp, "false_positives": fp,
            "detection_rate": tp / n_true_bursts,
            "false_positive_rate": fp / max(total_non_burst, 1),
        })
        print(f"  diff    thresh={t:5}  TP={tp}  FP={fp}")

    return {
        "ratio_results": ratio_results,
        "difference_results": diff_results,
        "ground_truth": list(true_keywords),
    }


# ── Experiment 4: End-to-End Pipeline ─────────────────────────────────────────

def experiment4_pipeline(
    stream_sizes: List[int] = None,
    window_size: int = 1000,
    k: int = 5,
) -> list:
    if stream_sizes is None:
        stream_sizes = [1_000, 5_000, 10_000, 50_000]

    print("\n[Experiment 4] End-to-End Pipeline Scalability")
    records = []

    for N in stream_sizes:
        events = generate_large_stream(N, n_keywords=10)

        tracemalloc.start()
        t0 = time.perf_counter()

        # Run inline pipeline (window + top-k + burst)
        window = deque()
        freq = {}
        prev_freq = {}
        for i, (t, kw) in enumerate(events):
            window.append((t, kw))
            freq[kw] = freq.get(kw, 0) + 1
            while window and window[0][0] <= t - window_size:
                _, old_kw = window.popleft()
                freq[old_kw] -= 1
                if freq[old_kw] == 0:
                    del freq[old_kw]
            if i % 100 == 0 and i > 0:
                top_k_heap(dict(freq), k)
                detect_bursts(dict(freq), prev_freq, threshold=2.0, method="ratio")
                prev_freq = dict(freq)

        elapsed = time.perf_counter() - t0
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        records.append({"n": N, "pipeline_time": elapsed})
        print(f"  N={N:>7,}  time={elapsed*1000:>8.1f}ms  peak_mem={peak/1024:.1f}KB")

    return records


# ── Run all ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("CS 5800 — Scalability Experiments")
    print("=" * 60)

    r1 = experiment1_sliding_window()
    r2_m, r2_k = experiment2_topk()
    r3 = experiment3_burst()
    r4 = experiment4_pipeline()

    all_results = {
        "sliding_window": r1,
        "top_k_vary_m": r2_m,
        "top_k_vary_k": r2_k,
        "burst_detection": r3,
        "pipeline": r4,
    }
    _save_all(all_results)

    print("\nAll experiments complete.")
