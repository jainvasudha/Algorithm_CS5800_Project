"""
plot_results.py — Visualisation (Parvathi / Shravya).

Reads JSON result files from results/ and produces 5 publication-quality plots:

  Plot 1  (exp1)  — Incremental vs Baseline runtime   (line chart)
  Plot 2  (exp2)  — Heap vs Sort Top-K runtime        (line chart, K=5 slice)
  Plot 3  (exp3)  — Burst detection: TP and FP vs threshold (line chart, both methods)
  Plot 4  (exp4)  — End-to-end pipeline runtime       (log-log line chart)
  Plot 5  (exp4)  — Peak memory usage vs stream size  (line chart)

Output: results/plots/ directory (PNG, 300 dpi).

Library used: matplotlib 3.7+
  matplotlib.pyplot — standard 2-D plotting API
  Reference: https://matplotlib.org/stable/api/pyplot_api.html
"""

import json
import os
import sys

import matplotlib
matplotlib.use("Agg")           # non-interactive backend (safe on any machine)
import matplotlib.pyplot as plt

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE = os.path.join(os.path.dirname(__file__), "..", "results")
PLOT_DIR = os.path.join(BASE, "plots")
os.makedirs(PLOT_DIR, exist_ok=True)


def _load(name: str) -> dict:
    path = os.path.join(BASE, f"{name}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Result file not found: {path}\n"
            f"Run:  python experiments/run_experiments.py  first."
        )
    with open(path) as f:
        return json.load(f)


def _save_plot(name: str) -> None:
    path = os.path.join(PLOT_DIR, f"{name}.png")
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved → {path}")


# ── Plot 1: Sliding Window — Incremental vs Baseline ─────────────────────────

def plot1_sliding_window() -> None:
    data = _load("exp1_sliding_window")
    sizes = data["stream_sizes"]
    inc   = data["incremental_ms"]
    base  = data["baseline_ms"]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(sizes, inc,  marker="o", linewidth=2, label="Incremental (O(N) total)")
    ax.plot(sizes, base, marker="s", linewidth=2, linestyle="--",
            label="Baseline recomputation (O(N²) total)")
    ax.set_xlabel("Stream Size (N)", fontsize=12)
    ax.set_ylabel("Total Runtime (ms)", fontsize=12)
    ax.set_title("Experiment 1: Sliding Window — Incremental vs Baseline", fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    _save_plot("plot1_sliding_window")


# ── Plot 2: Top-K — Heap vs Sort (K=5 slice) ─────────────────────────────────

def plot2_topk() -> None:
    data = _load("exp2_topk")
    records = data["records"]

    # Slice where K=5
    k_fixed = 5
    rows = [r for r in records if r["K"] == k_fixed]
    if not rows:
        # Fall back to smallest K available
        k_fixed = min(r["K"] for r in records)
        rows = [r for r in records if r["K"] == k_fixed]

    M_vals  = [r["M"] for r in rows]
    heap_ms = [r["heap_ms"] for r in rows]
    sort_ms = [r["sort_ms"] for r in rows]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(M_vals, heap_ms, marker="o", linewidth=2, label=f"Heap Top-K  (K={k_fixed})")
    ax.plot(M_vals, sort_ms, marker="s", linewidth=2, linestyle="--",
            label=f"Full Sort   (K={k_fixed})")
    ax.set_xlabel("Number of Distinct Keywords (M)", fontsize=12)
    ax.set_ylabel("Runtime per call (ms)", fontsize=12)
    ax.set_title(f"Experiment 2: Top-K Heap vs Sort (K={k_fixed})", fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    _save_plot("plot2_topk")


# ── Plot 3: Burst Detection — TP and FP vs Threshold ─────────────────────────

def plot3_burst() -> None:
    data = _load("exp3_burst")
    records   = data["records"]
    thresholds = data["thresholds"]
    n_true    = data["n_true_bursts"]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=False)

    for method, ax in zip(("ratio", "difference"), axes):
        rows = [r for r in records if r["method"] == method]
        tp_vals = [r["true_positives"]  for r in rows]
        fp_vals = [r["false_positives"] for r in rows]
        t_vals  = [r["threshold"]       for r in rows]

        ax.plot(t_vals, tp_vals, marker="o", linewidth=2, color="steelblue",
                label="True Positives (max={})".format(n_true))
        ax.plot(t_vals, fp_vals, marker="s", linewidth=2, color="salmon",
                linestyle="--", label="False Positives")
        ax.axhline(y=n_true, color="gray", linestyle=":", linewidth=1, label="Ground-truth count")
        ax.set_xlabel("Burst Threshold", fontsize=11)
        ax.set_ylabel("Count", fontsize=11)
        ax.set_title(f"Burst Detection — {method.capitalize()} Scoring", fontsize=12)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    fig.suptitle("Experiment 3: Burst Detection Sensitivity", fontsize=14, y=1.01)
    fig.tight_layout()
    _save_plot("plot3_burst")


# ── Plot 4: End-to-End Runtime (log-log) ─────────────────────────────────────

def plot4_e2e_runtime() -> None:
    data    = _load("exp4_e2e")
    sizes   = data["stream_sizes"]
    runtime = data["runtime_ms"]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.loglog(sizes, runtime, marker="D", linewidth=2, color="darkorchid",
              label="Full pipeline runtime")
    ax.set_xlabel("Stream Size (N)", fontsize=12)
    ax.set_ylabel("Total Runtime (ms)  [log scale]", fontsize=12)
    ax.set_title("Experiment 4: End-to-End Pipeline Scalability (log-log)", fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    _save_plot("plot4_e2e_runtime")


# ── Plot 5: Peak Memory Usage ─────────────────────────────────────────────────

def plot5_memory() -> None:
    data   = _load("exp4_e2e")
    sizes  = data["stream_sizes"]
    memory = data["memory_kb"]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(sizes, memory, marker="^", linewidth=2, color="seagreen",
            label="Peak memory (KB)")
    ax.set_xlabel("Stream Size (N)", fontsize=12)
    ax.set_ylabel("Peak Memory (KB)", fontsize=12)
    ax.set_title("Experiment 4b: Peak Memory vs Stream Size", fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    _save_plot("plot5_memory")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating all plots …")
    failed = []
    for fn in (plot1_sliding_window, plot2_topk, plot3_burst,
               plot4_e2e_runtime, plot5_memory):
        try:
            fn()
        except FileNotFoundError as e:
            print(f"  [SKIP] {e}")
            failed.append(fn.__name__)

    if failed:
        print(f"\n  Skipped {len(failed)} plot(s) — run run_experiments.py first.")
    else:
        print(f"\n✓ All 5 plots saved to results/plots/")
