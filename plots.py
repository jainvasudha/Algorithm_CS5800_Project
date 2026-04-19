"""
plots.py — Visualisation (Parvathi).

Reads experiment_results.json and produces 5 publication-quality plots:

  Plot 1  — Incremental vs Baseline runtime     (line chart)
  Plot 2  — Heap vs Sort Top-K runtime           (line chart, K=5 fixed)
  Plot 3  — Burst detection: detection rate vs threshold (line chart, both methods)
  Plot 4  — End-to-end pipeline runtime          (line chart)
  Plot 5  — Top-K vary K convergence             (line chart, M=1000 fixed)

Output: plots/ directory (PNG, 300 dpi).

Library used: matplotlib 3.7+
  Reference: Hunter, J.D. (2007). Computing in Science & Engineering, 9(3).
"""

import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS_PATH = os.path.join(os.path.dirname(__file__), "experiment_results.json")
PLOT_DIR = os.path.join(os.path.dirname(__file__), "plots")
os.makedirs(PLOT_DIR, exist_ok=True)


def _load() -> dict:
    if not os.path.exists(RESULTS_PATH):
        print(f"Error: {RESULTS_PATH} not found. Run 'python experiments.py' first.")
        sys.exit(1)
    with open(RESULTS_PATH) as f:
        return json.load(f)


def _save_plot(name: str) -> None:
    path = os.path.join(PLOT_DIR, f"{name}.png")
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved → {path}")


# ── Plot 1: Sliding Window — Incremental vs Baseline ─────────────────────────

def plot1_sliding_window(data: dict) -> None:
    records = data["sliding_window"]
    sizes = [r["n"] for r in records]
    naive = [r["naive_time"] for r in records]
    smart = [r["smart_time"] for r in records]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(sizes, smart, marker="o", linewidth=2, color="green",
            label="Incremental — O(N) total")
    ax.plot(sizes, naive, marker="s", linewidth=2, color="red", linestyle="--",
            label="Naive — O(N²) total")
    ax.set_xlabel("Stream Size (N events)", fontsize=12)
    ax.set_ylabel("Total Runtime (seconds)", fontsize=12)
    ax.set_title("Experiment 1: Sliding Window — Incremental vs Naive", fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    _save_plot("plot1_sliding_window")


# ── Plot 2: Top-K — Heap vs Sort (vary M, K=5 fixed) ────────────────────────

def plot2_topk_vary_m(data: dict) -> None:
    records = data["top_k_vary_m"]
    M_vals = [r["m"] for r in records]
    heap = [r["heap_time"] * 1000 for r in records]   # convert to ms
    sort = [r["sort_time"] * 1000 for r in records]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(M_vals, heap, marker="o", linewidth=2, color="purple",
            label="Heap — O(M log K), K=5")
    ax.plot(M_vals, sort, marker="s", linewidth=2, color="red", linestyle="--",
            label="Sort — O(M log M)")
    ax.set_xlabel("Vocabulary Size M (distinct keywords)", fontsize=12)
    ax.set_ylabel("Runtime per call (ms)", fontsize=12)
    ax.set_title("Experiment 2a: Top-K Heap vs Sort (K=5 fixed)", fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    _save_plot("plot2_topk_vary_m")


# ── Plot 3: Burst Detection — Detection Rate vs Threshold ────────────────────

def plot3_burst(data: dict) -> None:
    burst = data["burst_detection"]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Ratio method
    ratio = burst["ratio_results"]
    ax = axes[0]
    ax.plot([r["threshold"] for r in ratio], [r["detection_rate"] for r in ratio],
            marker="o", linewidth=2, color="steelblue", label="Detection rate")
    ax.plot([r["threshold"] for r in ratio], [r["false_positive_rate"] for r in ratio],
            marker="s", linewidth=2, color="salmon", linestyle="--", label="False positive rate")
    ax.set_xlabel("Threshold", fontsize=11)
    ax.set_ylabel("Rate", fontsize=11)
    ax.set_title("Ratio Scoring", fontsize=12)
    ax.set_ylim(-0.05, 1.1)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # Difference method
    diff = burst["difference_results"]
    ax = axes[1]
    ax.plot([r["threshold"] for r in diff], [r["detection_rate"] for r in diff],
            marker="o", linewidth=2, color="steelblue", label="Detection rate")
    ax.plot([r["threshold"] for r in diff], [r["false_positive_rate"] for r in diff],
            marker="s", linewidth=2, color="salmon", linestyle="--", label="False positive rate")
    ax.set_xlabel("Threshold", fontsize=11)
    ax.set_ylabel("Rate", fontsize=11)
    ax.set_title("Difference Scoring", fontsize=12)
    ax.set_ylim(-0.05, 1.1)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    fig.suptitle("Experiment 3: Burst Detection Sensitivity", fontsize=14, y=1.01)
    fig.tight_layout()
    _save_plot("plot3_burst_sensitivity")


# ── Plot 4: End-to-End Pipeline Runtime ──────────────────────────────────────

def plot4_pipeline(data: dict) -> None:
    records = data["pipeline"]
    sizes = [r["n"] for r in records]
    times = [r["pipeline_time"] for r in records]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(sizes, times, marker="D", linewidth=2, color="darkorchid",
            label="Full pipeline runtime")
    ax.set_xlabel("Stream Size (N events)", fontsize=12)
    ax.set_ylabel("Total Runtime (seconds)", fontsize=12)
    ax.set_title("Experiment 4: End-to-End Pipeline Scalability", fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    _save_plot("plot4_pipeline")


# ── Plot 5: Top-K — Vary K convergence (M=1000 fixed) ───────────────────────

def plot5_topk_vary_k(data: dict) -> None:
    records = data["top_k_vary_k"]
    K_vals = [r["k"] for r in records]
    heap = [r["heap_time"] * 1000 for r in records]
    sort = [r["sort_time"] * 1000 for r in records]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(K_vals, heap, marker="o", linewidth=2, color="purple",
            label="Heap — O(M log K)")
    ax.plot(K_vals, sort, marker="s", linewidth=2, color="red", linestyle="--",
            label="Sort — O(M log M)")
    ax.set_xlabel("K (results requested)", fontsize=12)
    ax.set_ylabel("Runtime per call (ms)", fontsize=12)
    ax.set_title("Experiment 2b: Top-K Convergence as K → M (M=1000)", fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    _save_plot("plot5_topk_vary_k")


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating all plots...")
    data = _load()

    plot1_sliding_window(data)
    plot2_topk_vary_m(data)
    plot3_burst(data)
    plot4_pipeline(data)
    plot5_topk_vary_k(data)

    print(f"\nAll 5 plots saved to {PLOT_DIR}/")
