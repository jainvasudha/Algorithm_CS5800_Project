"""
main.py — Entry point for the Real-Time Fashion Trend Detection System.
Connects all modules into one pipeline.
"""

import sys, os, heapq
from collections import deque

sys.path.insert(0, os.path.dirname(__file__))

from config import DEFAULT_K, BURST_THRESHOLD_RATIO, DEFAULT_BURST_METHOD
from burst_detection import detect_bursts
from accessibility import score_keyword

try:
    from top_k import top_k_heap
    HAS_TOP_K = True
except ImportError:
    HAS_TOP_K = False

try:
    from cycle_detection import classify_trend
    HAS_CYCLE = True
except ImportError:
    HAS_CYCLE = False


def _top_k_heap_fallback(freq_map, k):
    heap = []
    for kw, count in freq_map.items():
        if len(heap) < k:
            heapq.heappush(heap, (count, kw))
        elif count > heap[0][0]:
            heapq.heapreplace(heap, (count, kw))
    return [(kw, count) for count, kw in sorted(heap, reverse=True)]


def _classify_trend_fallback(keyword, current_freq, previous_freq, burst_score):
    curr = current_freq.get(keyword, 0)
    prev = previous_freq.get(keyword, 0)
    if prev == 0 and curr > 0: return "New"
    elif burst_score > 2.0: return "Growing"
    elif curr < prev * 0.5: return "Fading"
    else: return "Stable"


def run_pipeline(events, window_size=1000, k=DEFAULT_K,
                 burst_threshold=BURST_THRESHOLD_RATIO,
                 burst_method=DEFAULT_BURST_METHOD, snapshot_interval=100):
    window, freq, prev_freq, results = deque(), {}, {}, []

    for i, (t, kw) in enumerate(events):
        window.append((t, kw))
        freq[kw] = freq.get(kw, 0) + 1
        while window and window[0][0] <= t - window_size:
            _, old_kw = window.popleft()
            freq[old_kw] -= 1
            if freq[old_kw] == 0: del freq[old_kw]

        if i % snapshot_interval == 0 and i > 0:
            current_freq = dict(freq)
            top_k = top_k_heap(current_freq, k) if HAS_TOP_K else _top_k_heap_fallback(current_freq, k)
            bursts = detect_bursts(current_freq, prev_freq, threshold=burst_threshold, method=burst_method)
            burst_map = dict(bursts)

            classifications = {}
            for keyword in current_freq:
                b_score = burst_map.get(keyword, 0.0)
                if HAS_CYCLE:
                    classifications[keyword] = classify_trend(keyword, current_freq, prev_freq, b_score)
                else:
                    classifications[keyword] = _classify_trend_fallback(keyword, current_freq, prev_freq, b_score)

            scored_trends = []
            for keyword, count in top_k:
                acc_score, acc_label = score_keyword(keyword)
                scored_trends.append({
                    "keyword": keyword, "freq": count,
                    "label": classifications.get(keyword, "Unknown"),
                    "burst": burst_map.get(keyword, 0.0),
                    "accessibility": acc_score, "access_label": acc_label,
                })
            results.append({
                "timestamp": t, "event_index": i, "freq_map": current_freq,
                "top_k": top_k, "bursts": bursts, "classifications": classifications,
                "scored_trends": scored_trends,
            })
            prev_freq = current_freq
    return results


def print_results(results, last_n=3):
    for snapshot in results[-last_n:]:
        print(f"\n{'='*60}")
        print(f"Snapshot at event #{snapshot['event_index']} (timestamp={snapshot['timestamp']})")
        print(f"{'='*60}")
        print(f"\n  Top-{len(snapshot['top_k'])} Trends:")
        for kw, count in snapshot["top_k"]:
            print(f"    {kw:20s}  freq={count}")
        if snapshot["bursts"]:
            print(f"\n  Bursting Keywords:")
            for kw, score in snapshot["bursts"][:5]:
                print(f"    {kw:20s}  burst_score={score:.2f}")
        print(f"\n  Scored Trends (with accessibility):")
        for trend in snapshot["scored_trends"]:
            acc = trend["accessibility"]
            acc_str = f"{acc:.2f}" if acc is not None else "N/A"
            print(f"    {trend['keyword']:20s}  freq={trend['freq']:>3d}  "
                  f"label={trend['label']:10s}  burst={trend['burst']:.2f}  "
                  f"access={acc_str} ({trend['access_label']})")


def main():
    from data.generate_synthetic import generate_mixed_stream
    print("Real-Time Fashion Trend Detection System")
    print("=" * 60)
    print("\nGenerating synthetic event stream...")
    events = generate_mixed_stream(n_events_per_keyword=500)
    print(f"  Total events: {len(events)}")
    print("\nRunning pipeline...")
    results = run_pipeline(events, window_size=2000, k=5, burst_threshold=1.5,
                           burst_method="ratio", snapshot_interval=200)
    print(f"  Snapshots collected: {len(results)}")
    print_results(results, last_n=3)
    print(f"\n{'='*60}\nPipeline complete.")
    return results


if __name__ == "__main__":
    main()
