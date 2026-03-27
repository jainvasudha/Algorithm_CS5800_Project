"""
plots.py — Generates matplotlib charts for all experiment results.
"""

import os, json
import matplotlib.pyplot as plt

PLOT_DIR = os.path.join(os.path.dirname(__file__), "report", "plots")
os.makedirs(PLOT_DIR, exist_ok=True)


def _save_and_show(fig, filename):
    path = os.path.join(PLOT_DIR, filename)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    print(f"  Saved: {path}")
    plt.close(fig)


def plot_sliding_window(results):
    ns = [r["n"] for r in results]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(ns, [r["naive_time"] for r in results], "o-", color="red", linewidth=2, label="Naive (full scan)")
    ax.plot(ns, [r["smart_time"] for r in results], "s-", color="green", linewidth=2, label="Incremental (deque + hash)")
    ax.set_xlabel("Stream Size (N events)", fontsize=12)
    ax.set_ylabel("Total Processing Time (seconds)", fontsize=12)
    ax.set_title("Money Shot 1: Sliding Window — Incremental vs Naive", fontsize=13)
    ax.legend(fontsize=11); ax.grid(True, alpha=0.3); ax.ticklabel_format(style="plain", axis="x")
    _save_and_show(fig, "experiment1_sliding_window.png")


def plot_top_k_vary_m(results):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot([r["m"] for r in results], [r["sort_time"] for r in results], "o-", color="red", linewidth=2, label="Sort O(M log M)")
    ax.plot([r["m"] for r in results], [r["heap_time"] for r in results], "s-", color="green", linewidth=2, label="Heap O(M log K)")
    ax.set_xlabel("Vocabulary Size (M)", fontsize=12)
    ax.set_ylabel("Time to Extract Top-K (seconds)", fontsize=12)
    ax.set_title("Money Shot 2a: Top-K Selection — Heap vs Sort (K=5)", fontsize=13)
    ax.legend(fontsize=11); ax.grid(True, alpha=0.3)
    _save_and_show(fig, "experiment2a_top_k_vary_m.png")


def plot_top_k_vary_k(results):
    ks = [r["k"] for r in results]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(ks, [r["sort_time"] for r in results], "o-", color="red", linewidth=2, label="Sort O(M log M)")
    ax.plot(ks, [r["heap_time"] for r in results], "s-", color="green", linewidth=2, label="Heap O(M log K)")
    ax.set_xlabel("K (number of top items)", fontsize=12)
    ax.set_ylabel("Time to Extract Top-K (seconds)", fontsize=12)
    ax.set_title("Money Shot 2b: Top-K — Heap vs Sort as K→M (M=1000)", fontsize=13)
    ax.legend(fontsize=11); ax.grid(True, alpha=0.3)
    _save_and_show(fig, "experiment2b_top_k_vary_k.png")


def plot_burst_detection(results):
    ratio, diff = results["ratio_results"], results["difference_results"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    ax1.plot([r["threshold"] for r in ratio], [r["detection_rate"] for r in ratio], "o-", color="blue", linewidth=2, label="Ratio")
    ax1.plot([r["threshold"] for r in diff], [r["detection_rate"] for r in diff], "s-", color="orange", linewidth=2, label="Difference")
    ax1.set_xlabel("Threshold"); ax1.set_ylabel("Detection Rate"); ax1.set_title("True Positive Rate")
    ax1.legend(); ax1.grid(True, alpha=0.3); ax1.set_ylim(-0.05, 1.1)
    ax2.plot([r["threshold"] for r in ratio], [r["false_positive_rate"] for r in ratio], "o-", color="blue", linewidth=2, label="Ratio")
    ax2.plot([r["threshold"] for r in diff], [r["false_positive_rate"] for r in diff], "s-", color="orange", linewidth=2, label="Difference")
    ax2.set_xlabel("Threshold"); ax2.set_ylabel("False Positive Rate"); ax2.set_title("False Positive Rate")
    ax2.legend(); ax2.grid(True, alpha=0.3); ax2.set_ylim(-0.05, 1.1)
    fig.suptitle("Money Shot 3: Burst Scoring — Ratio vs Difference", fontsize=14, y=1.02)
    fig.tight_layout()
    _save_and_show(fig, "experiment3_burst_detection.png")


def plot_pipeline_scalability(results):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot([r["n"] for r in results], [r["pipeline_time"] for r in results], "D-", color="purple", linewidth=2, label="Full pipeline")
    ax.set_xlabel("Stream Size (N events)"); ax.set_ylabel("Total Pipeline Time (seconds)")
    ax.set_title("End-to-End Pipeline Scalability"); ax.legend(); ax.grid(True, alpha=0.3)
    ax.ticklabel_format(style="plain", axis="x")
    _save_and_show(fig, "experiment4_pipeline_scalability.png")


def generate_all_plots(results_path=None):
    if results_path is None:
        results_path = os.path.join(os.path.dirname(__file__), "experiment_results.json")
    with open(results_path, "r") as f:
        results = json.load(f)
    print("Generating plots...")
    if "sliding_window" in results: plot_sliding_window(results["sliding_window"])
    if "top_k_vary_m" in results: plot_top_k_vary_m(results["top_k_vary_m"])
    if "top_k_vary_k" in results: plot_top_k_vary_k(results["top_k_vary_k"])
    if "burst_detection" in results: plot_burst_detection(results["burst_detection"])
    if "pipeline" in results: plot_pipeline_scalability(results["pipeline"])
    print(f"\nAll plots saved to {PLOT_DIR}/")


if __name__ == "__main__":
    import sys
    generate_all_plots(sys.argv[1] if len(sys.argv) > 1 else None)
