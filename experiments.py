"""
experiments.py — Benchmarking harness for all 3 money-shot experiments.
Uses time.perf_counter() for wall-clock timing and tracemalloc for memory.
"""

import time, tracemalloc, random, heapq, sys, os

sys.path.insert(0, os.path.dirname(__file__))

from config import DEFAULT_K, EXPERIMENT_STREAM_SIZES, EXPERIMENT_VOCAB_SIZES, EXPERIMENT_K_VALUES
from data.generate_synthetic import generate_scalable_stream, generate_burst_experiment_data
from burst_detection import detect_bursts, sweep_thresholds

try:
    from sliding_window import SlidingWindow
    from baseline import BaselineCounter
    HAS_WINDOW = True
except ImportError:
    HAS_WINDOW = False

try:
    from top_k import top_k_heap, top_k_sort
    HAS_TOP_K = True
except ImportError:
    HAS_TOP_K = False


class BenchmarkTimer:
    def __enter__(self):
        tracemalloc.start()
        self.start = time.perf_counter()
        return self
    def __exit__(self, *args):
        self.elapsed = time.perf_counter() - self.start
        _, self.peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()


def _time_function(func, *args, repeats=3, **kwargs):
    times = []
    for _ in range(repeats):
        with BenchmarkTimer() as bt:
            func(*args, **kwargs)
        times.append(bt.elapsed)
    times.sort()
    return times[len(times) // 2]


def _top_k_heap_standalone(freq_map, k):
    heap = []
    for kw, count in freq_map.items():
        if len(heap) < k:
            heapq.heappush(heap, (count, kw))
        elif count > heap[0][0]:
            heapq.heapreplace(heap, (count, kw))
    return sorted(heap, key=lambda x: x[0], reverse=True)


def _top_k_sort_standalone(freq_map, k):
    return sorted(freq_map.items(), key=lambda x: x[1], reverse=True)[:k]


def experiment_sliding_window(stream_sizes=None, window_size=1000, repeats=3):
    from collections import deque
    if stream_sizes is None:
        stream_sizes = EXPERIMENT_STREAM_SIZES
    results = []
    for n in stream_sizes:
        stream = generate_scalable_stream(n)
        print(f"  N={n:>7,d} ... ", end="", flush=True)
        def run_smart():
            window, freq = deque(), {}
            for t, kw in stream:
                window.append((t, kw))
                freq[kw] = freq.get(kw, 0) + 1
                while window and window[0][0] <= t - window_size:
                    _, old_kw = window.popleft()
                    freq[old_kw] -= 1
                    if freq[old_kw] == 0: del freq[old_kw]
        def run_naive():
            all_events = []
            for t, kw in stream:
                all_events.append((t, kw))
                _ = {}
                for et, ekw in all_events:
                    if et > t - window_size:
                        _[ekw] = _.get(ekw, 0) + 1
        smart_time = _time_function(run_smart, repeats=repeats)
        naive_time = _time_function(run_naive, repeats=repeats)
        results.append({"n": n, "naive_time": naive_time, "smart_time": smart_time})
        print(f"naive={naive_time:.4f}s  smart={smart_time:.4f}s")
    return results


def experiment_top_k_vary_m(k=DEFAULT_K, vocab_sizes=None, repeats=5):
    if vocab_sizes is None:
        vocab_sizes = EXPERIMENT_VOCAB_SIZES
    results = []
    for m in vocab_sizes:
        freq_map = {f"keyword_{i}": random.randint(1, 1000) for i in range(m)}
        print(f"  M={m:>5,d}, K={k} ... ", end="", flush=True)
        heap_time = _time_function(_top_k_heap_standalone, freq_map, k, repeats=repeats)
        sort_time = _time_function(_top_k_sort_standalone, freq_map, k, repeats=repeats)
        results.append({"m": m, "heap_time": heap_time, "sort_time": sort_time})
        print(f"heap={heap_time:.6f}s  sort={sort_time:.6f}s")
    return results


def experiment_top_k_vary_k(m=1000, k_values=None, repeats=5):
    if k_values is None:
        k_values = EXPERIMENT_K_VALUES
    freq_map = {f"keyword_{i}": random.randint(1, 1000) for i in range(m)}
    results = []
    for k in k_values:
        if k > m: continue
        print(f"  M={m}, K={k:>5,d} ... ", end="", flush=True)
        heap_time = _time_function(_top_k_heap_standalone, freq_map, k, repeats=repeats)
        sort_time = _time_function(_top_k_sort_standalone, freq_map, k, repeats=repeats)
        results.append({"k": k, "heap_time": heap_time, "sort_time": sort_time})
        print(f"heap={heap_time:.6f}s  sort={sort_time:.6f}s")
    return results


def experiment_burst_detection(n_keywords=50, n_true_bursts=5, repeats=3):
    prev, curr, ground_truth = generate_burst_experiment_data(
        n_keywords=n_keywords, n_true_bursts=n_true_bursts)
    ratio_thresholds = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.0, 10.0]
    diff_thresholds = [5, 10, 15, 20, 30, 50, 75, 100, 150]
    print("  Sweeping ratio thresholds...")
    ratio_results = sweep_thresholds(curr, prev, ground_truth, ratio_thresholds, method="ratio")
    print("  Sweeping difference thresholds...")
    diff_results = sweep_thresholds(curr, prev, ground_truth, diff_thresholds, method="difference")
    return {"ratio_results": ratio_results, "difference_results": diff_results, "ground_truth": ground_truth}


def experiment_pipeline_scalability(stream_sizes=None, repeats=2):
    from collections import deque
    if stream_sizes is None:
        stream_sizes = [1_000, 5_000, 10_000, 50_000]
    results = []
    for n in stream_sizes:
        stream = generate_scalable_stream(n)
        print(f"  Pipeline N={n:>7,d} ... ", end="", flush=True)
        def run_pipeline():
            window, freq, prev_freq = deque(), {}, {}
            for i, (t, kw) in enumerate(stream):
                window.append((t, kw))
                freq[kw] = freq.get(kw, 0) + 1
                while window and window[0][0] <= t - 1000:
                    _, old_kw = window.popleft()
                    freq[old_kw] -= 1
                    if freq[old_kw] == 0: del freq[old_kw]
                if i % 500 == 0 and i > 0:
                    _top_k_heap_standalone(freq, 5)
                    detect_bursts(freq, prev_freq, method="ratio", threshold=2.0)
                    prev_freq = dict(freq)
        elapsed = _time_function(run_pipeline, repeats=repeats)
        results.append({"n": n, "pipeline_time": elapsed})
        print(f"time={elapsed:.4f}s")
    return results


def run_all_experiments():
    results = {}
    print("=" * 60)
    print("EXPERIMENT 1: Sliding Window — Incremental vs Naive")
    print("=" * 60)
    results["sliding_window"] = experiment_sliding_window(
        stream_sizes=[1_000, 5_000, 10_000, 50_000, 100_000])
    print("\n" + "=" * 60)
    print("EXPERIMENT 2a: Top-K — Vary M, Fix K=5")
    print("=" * 60)
    results["top_k_vary_m"] = experiment_top_k_vary_m()
    print("\n" + "=" * 60)
    print("EXPERIMENT 2b: Top-K — Fix M=1000, Vary K")
    print("=" * 60)
    results["top_k_vary_k"] = experiment_top_k_vary_k()
    print("\n" + "=" * 60)
    print("EXPERIMENT 3: Burst Detection — Ratio vs Difference")
    print("=" * 60)
    results["burst_detection"] = experiment_burst_detection()
    print("\n" + "=" * 60)
    print("EXPERIMENT 4: Pipeline Scalability")
    print("=" * 60)
    results["pipeline"] = experiment_pipeline_scalability()
    return results


if __name__ == "__main__":
    import json as _json
    results = run_all_experiments()
    output_path = os.path.join(os.path.dirname(__file__), "experiment_results.json")
    serializable = {}
    for key, val in results.items():
        if isinstance(val, dict):
            serializable[key] = {k: (list(v) if isinstance(v, set) else v) for k, v in val.items()}
        else:
            serializable[key] = val
    with open(output_path, "w") as f:
        _json.dump(serializable, f, indent=2)
    print(f"\nResults saved to {output_path}")
