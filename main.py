"""
main.py — Integration Pipeline (Parvathi / Shravya).

Connects all three modules into a single end-to-end pipeline:
  Module A  (Bhoomika) → Sliding Window Engine      → freq_map
  Module B  (Vasudha)  → Top-K, Burst, Classify     → ranked trends
  Module C  (Parvathi) → Accessibility Scoring       → final output

Usage:
  python -m src.main                        # synthetic demo
  python -m src.main --csv data/google_trends/fashion.csv

The pipeline tries to import the real implementations first; if they are not
present yet it falls back to the stubs in src/stubs.py so the integration
can be demonstrated immediately.
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Optional, Tuple

# ── Import real modules if available, otherwise fall back to stubs ─────────────
try:
    from src.sliding_window import SlidingWindowEngine
    from src.baseline import recompute_frequencies
    from src.stream_simulator import load_google_trends_csv
    _REAL_A = True
except ImportError:
    from src.stubs import SlidingWindowEngine, recompute_frequencies  # type: ignore
    _REAL_A = False

try:
    from src.top_k import top_k_heap, top_k_sort
    from src.burst_detection import detect_bursts
    from src.cycle_detection import cosine_similarity
    from src.trend_classifier import classify_trend
    _REAL_B = True
except ImportError:
    from src.stubs import (  # type: ignore
        top_k_heap, top_k_sort, detect_bursts, cosine_similarity, classify_trend,
    )
    _REAL_B = False

from src.accessibility import compute_accessibility_score, rank_by_accessibility, load_accessibility_db
from src.config import DEFAULT_WINDOW_SIZE, DEFAULT_K, BURST_THRESHOLD, BURST_METHOD

# Synthetic data lives in data/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.generate_synthetic import generate_mixed_stream


# ── Pipeline ──────────────────────────────────────────────────────────────────

def run_pipeline(
    events: List[Tuple[int, str]],
    accessibility_db: Dict,
    window_size: int = DEFAULT_WINDOW_SIZE,
    k: int = DEFAULT_K,
    burst_threshold: float = BURST_THRESHOLD,
    burst_method: str = BURST_METHOD,
    verbose: bool = True,
) -> List[Dict]:
    """
    Process the full event stream and return a list of enriched trend records.

    Steps per window boundary:
      1. Feed events into the incremental sliding window.
      2. At each window step: extract current freq_map.
      3. Run Top-K heap selection.
      4. Run burst detection vs previous window.
      5. Build frequency trajectory for cycle classification.
      6. Score accessibility for each detected trend.
      7. Merge into final output record.
    """
    engine = SlidingWindowEngine(window_size)
    prev_freq: Dict[str, int] = {}
    trajectory: Dict[str, List[int]] = {}   # keyword → list of per-window counts
    results: List[Dict] = []

    # Group events by their timestamp so we can process window-by-window
    from collections import defaultdict
    by_step: Dict[int, List[str]] = defaultdict(list)
    for ts, kw in events:
        by_step[ts].append(kw)

    all_steps = sorted(by_step.keys())

    for step in all_steps:
        # Process all events at this time step
        for kw in by_step[step]:
            engine.process_event(step, kw)

        freq_map = engine.get_current_frequencies()

        # Update trajectories
        for kw in freq_map:
            trajectory.setdefault(kw, []).append(freq_map[kw])

        # Top-K by frequency
        top_freq = top_k_heap(freq_map, k)

        # Burst detection
        bursting = detect_bursts(freq_map, prev_freq, k, burst_threshold, burst_method)
        burst_dict = {kw: score for kw, score in bursting}

        # Build trend records for this step
        step_records: List[Dict] = []
        seen = set()
        for kw, cnt in top_freq:
            if kw in seen:
                continue
            seen.add(kw)
            b_score = burst_dict.get(kw, 1.0)
            traj = trajectory.get(kw, [cnt])
            # Simplified historical comparison: compare first half vs second half
            half = len(traj) // 2 or 1
            hist_vec = traj[:half]
            curr_vec = traj[half:]
            if not curr_vec:
                curr_vec = traj
            cos_sim = cosine_similarity(hist_vec, curr_vec) if len(hist_vec) > 0 else 0.0
            label = classify_trend(kw, b_score, cos_sim, traj)

            step_records.append({
                "step":      step,
                "keyword":   kw,
                "frequency": cnt,
                "burst_score": round(b_score, 3),
                "cosine_sim":  round(cos_sim, 3),
                "label":     label,
            })

        # Rank by accessibility
        ranked, alerts = rank_by_accessibility(step_records, accessibility_db, k)
        results.extend(ranked)

        if verbose and step % (window_size * 2) == 0:
            print(f"\n── Step {step} ──────────────────────────────")
            for r in ranked[:3]:
                print(f"  {r['keyword']:<25} freq={r['frequency']:>3}  "
                      f"burst={r['burst_score']:.2f}  label={r['label']:<10}  "
                      f"access={r['accessibility_score']:.2f} ({r['accessibility_label']})")
            if alerts:
                print(f"  ⚠ Low/missing accessibility data: {alerts}")

        prev_freq = dict(freq_map)

    return results


# ── CLI entry point ────────────────────────────────────────────────────────────

def _load_csv_events(path: str) -> List[Tuple[int, str]]:
    """Try to load real CSV; fall back to synthetic if not found."""
    if not os.path.exists(path):
        print(f"[WARNING] CSV not found at {path}. Using synthetic data.")
        return generate_mixed_stream()
    # Real loader from Bhoomika's module (or stub equivalent)
    try:
        from src.stream_simulator import load_google_trends_csv
        return load_google_trends_csv(path)
    except ImportError:
        print("[WARNING] stream_simulator.py not available; using synthetic data.")
        return generate_mixed_stream()


def main():
    parser = argparse.ArgumentParser(description="Real-Time Fashion Trend Detection Pipeline")
    parser.add_argument("--csv",    type=str, default=None, help="Path to Google Trends CSV")
    parser.add_argument("--window", type=int, default=DEFAULT_WINDOW_SIZE)
    parser.add_argument("--k",      type=int, default=DEFAULT_K)
    parser.add_argument("--burst-threshold", type=float, default=BURST_THRESHOLD)
    parser.add_argument("--quiet",  action="store_true")
    args = parser.parse_args()

    # Load accessibility database
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "accessibility_db.json")
    try:
        access_db = load_accessibility_db(db_path)
    except FileNotFoundError:
        print(f"[WARNING] accessibility_db.json not found at {db_path}. Scores will be 0.")
        access_db = {}

    # Load events
    if args.csv:
        events = _load_csv_events(args.csv)
    else:
        print("[INFO] No CSV provided. Running on synthetic mixed-pattern stream.")
        events = generate_mixed_stream()

    print(f"[INFO] Stream: {len(events)} events  |  "
          f"window={args.window}  k={args.k}  "
          f"using_real_A={_REAL_A}  using_real_B={_REAL_B}")

    results = run_pipeline(
        events, access_db,
        window_size=args.window,
        k=args.k,
        burst_threshold=args.burst_threshold,
        verbose=not args.quiet,
    )

    print(f"\n[INFO] Pipeline complete. {len(results)} trend records produced.")


if __name__ == "__main__":
    main()
