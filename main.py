"""
main.py — Integration Pipeline.

Connects all modules into a single end-to-end pipeline:
  Module A  (Bhoomika) → Sliding Window Engine      → freq_map
  Module B  (Vasudha)  → Top-K, Burst, Classify     → ranked trends
  Module C  (Parvathi) → Accessibility Scoring       → final output

Usage:
  python main.py                # synthetic demo
  python main.py --k 5          # change top-K
"""

import argparse
import os
import sys
from collections import deque
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from top_k import top_k_heap
from burst_detection import detect_bursts
from cycle_detection import classify_trend
from accessibility import rank_by_accessibility, load_accessibility_db
from config import DEFAULT_K, BURST_THRESHOLD_RATIO, DEFAULT_BURST_METHOD
from data.generate_synthetic import generate_mixed_stream


# ── Pipeline ──────────────────────────────────────────────────────────────────

def run_pipeline(
    events: List[Tuple[int, str]],
    accessibility_db: Dict,
    window_size: int = 1000,
    k: int = DEFAULT_K,
    burst_threshold: float = BURST_THRESHOLD_RATIO,
    burst_method: str = DEFAULT_BURST_METHOD,
    snapshot_interval: int = 100,
    verbose: bool = True,
) -> List[Dict]:
    """
    Process the full event stream and return a list of enriched trend records.

    Steps at each snapshot:
      1. Maintain incremental sliding window (deque + hash map).
      2. Extract current freq_map.
      3. Run Top-K heap selection.
      4. Run burst detection vs previous window.
      5. Classify each keyword (New / Cyclical / Fading).
      6. Score accessibility for each detected trend.
      7. Rank by accessibility using min-heap.
    """
    window: deque = deque()
    freq: Dict[str, int] = {}
    prev_freq: Dict[str, int] = {}
    results: List[Dict] = []

    for i, (t, kw) in enumerate(events):
        # Incremental sliding window: add event, expire old
        window.append((t, kw))
        freq[kw] = freq.get(kw, 0) + 1
        while window and window[0][0] <= t - window_size:
            _, old_kw = window.popleft()
            freq[old_kw] -= 1
            if freq[old_kw] == 0:
                del freq[old_kw]

        # Take snapshot at intervals
        if i % snapshot_interval == 0 and i > 0:
            current_freq = dict(freq)

            # Top-K by frequency
            top_k = top_k_heap(current_freq, k)

            # Burst detection
            bursts = detect_bursts(
                current_freq, prev_freq,
                threshold=burst_threshold, method=burst_method,
            )
            burst_map = {kw: score for kw, score in bursts}

            # Build trend records
            step_records: List[Dict] = []
            for keyword, count in top_k:
                b_score = burst_map.get(keyword, 0.0)
                label = classify_trend(keyword, current_freq, prev_freq, b_score)

                step_records.append({
                    "step":        t,
                    "keyword":     keyword,
                    "frequency":   count,
                    "burst_score": round(b_score, 3),
                    "label":       label,
                })

            # Rank by accessibility using min-heap
            ranked, alerts = rank_by_accessibility(
                step_records, accessibility_db, k,
            )
            results.extend(ranked)

            if verbose and len(results) % (k * 5) == 0:
                print(f"\n── Snapshot at event #{i} (timestamp={t}) ──")
                for r in ranked[:k]:
                    acc = r.get("accessibility_score", 0.0)
                    acc_lbl = r.get("accessibility_label", "N/A")
                    print(
                        f"  {r['keyword']:<22} freq={r['frequency']:>3}  "
                        f"burst={r['burst_score']:.2f}  label={r['label']:<10}  "
                        f"access={acc:.2f} ({acc_lbl})"
                    )
                if alerts:
                    print(f"  ⚠ Low/missing accessibility data: {alerts}")

            prev_freq = current_freq

    return results


# ── CLI entry point ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Real-Time Fashion Trend Detection Pipeline"
    )
    parser.add_argument("--window", type=int, default=2000, help="Sliding window size")
    parser.add_argument("--k", type=int, default=DEFAULT_K, help="Top-K trends to show")
    parser.add_argument("--burst-threshold", type=float, default=BURST_THRESHOLD_RATIO)
    parser.add_argument("--weeks", type=int, default=52, help="Number of weeks for synthetic data")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    # Load accessibility database
    db_path = os.path.join(os.path.dirname(__file__), "data", "accessibility_db.json")
    try:
        access_db = load_accessibility_db(db_path)
    except FileNotFoundError:
        print(f"[WARNING] accessibility_db.json not found. Accessibility scores will be 0.")
        access_db = {}

    # Generate synthetic events
    print("Real-Time Fashion Trend Detection System")
    print("=" * 60)
    print(f"\nGenerating synthetic event stream ({args.weeks} weeks)...")
    events = generate_mixed_stream(n_weeks=args.weeks)
    print(f"  Total events: {len(events)}")

    print(f"\nRunning pipeline (window={args.window}, k={args.k}, "
          f"burst_threshold={args.burst_threshold})...")

    results = run_pipeline(
        events, access_db,
        window_size=args.window,
        k=args.k,
        burst_threshold=args.burst_threshold,
        snapshot_interval=200,
        verbose=not args.quiet,
    )

    print(f"\n{'=' * 60}")
    print(f"Pipeline complete. {len(results)} trend records produced.")


if __name__ == "__main__":
    main()
