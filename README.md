# Real-Time Fashion Trend Detection System

**Course:** CS 5800 — Algorithms | Northeastern University | Spring 2026

**Team:** Bhoomika Panday, Vasudha Jain, Parvathi Gottumukkala

**Report:** `ReportGottumukkalaJainPanday.pdf`

**Live Demo:** [delicate-dango-9dd344.netlify.app](https://delicate-dango-9dd344.netlify.app/)

---

## What This Project Does

This system processes streaming fashion trend data from Google Trends and:

1. **Tracks** keyword frequency over time using a sliding window with incremental updates
2. **Ranks** the Top-K most frequent trends using a min-heap
3. **Detects bursts** — sudden spikes in trend popularity across consecutive time windows
4. **Classifies** each trend's lifecycle stage (New, Cyclical, Fading) using per-keyword change analysis
5. **Scores** trends on accessibility using weighted multi-criteria scoring with min-heap ranking

No machine learning is used — only classical data structures and algorithms from CS 5800.

---

## How to Run

### Prerequisites

- Python 3.8 or higher
- pip

### Step 1 — Clone and install

```bash
git clone https://github.com/jainvasudha/Algorithm_CS5800_Project.git
cd Algorithm_CS5800_Project
pip install -r requirements.txt
```

**Dependencies:** `matplotlib`, `pytest`, `pytrends` — all algorithm implementations use only Python's standard library (`heapq`, `collections`, `math`, `csv`, `time`, `tracemalloc`).

### Step 2 — Run the main pipeline

```bash
python main.py
```

This runs the full system on synthetic streaming data and prints:
- Top-K trending keywords for each window
- Bursting keywords with growth scores
- Lifecycle classification (New / Cyclical / Fading)
- Accessibility scores

### Step 3 — Run experiments and generate plots

```bash
python experiments.py
python plots.py
```

This produces 3 performance comparison charts:
- Plot 1: Sliding window — incremental vs naive runtime (N = 1K to 100K)
- Plot 2: Top-K — heap vs sort runtime (M = 50 to 5,000)
- Plot 3: Burst detection — ratio vs difference detection rate across thresholds

### Step 4 — Run the web demo (optional)

```bash
pip install flask flask-cors
python api.py
```

Then open the website at [delicate-dango-9dd344.netlify.app](https://delicate-dango-9dd344.netlify.app/) or serve `index.html` locally.

### Step 5 — Run all tests

```bash
python -m pytest tests/ -v
```

---

## Algorithms and CS 5800 Topics

| # | Algorithm | Approach | Time | CS 5800 Topic |
|---|-----------|----------|------|---------------|
| 1 | Sliding Window | Deque + hash map, incremental insert/expire | O(1) amortized per event | Hash Tables, Deques, Amortized Analysis |
| 2 | Top-K Selection | Min-heap of size K, single pass | O(M log K) | Priority Queues, Heaps, Greedy |
| 3 | Burst Detection | Ratio and difference scoring between windows | O(M) | Algorithm Design, Complexity Analysis |
| 4 | Cycle Classification | Per-keyword change ratio + slope | O(1) per keyword | Algorithm Design |
| 5 | Accessibility Scoring | Weighted sum + min-heap ranking | O(T log K) | Weighted Scoring, Priority Queues |

---

## Data

10 real Google Trends CSVs (2004–2026, monthly, worldwide):

| Keyword | Expected Pattern |
|---|---|
| wide-leg jeans | Currently rising |
| skinny jeans | Was huge, now fading |
| cargo pants | Cyclical (2000s → now) |
| Y2K fashion | Sudden burst (2021+) |
| low-rise jeans | Controversial comeback |
| mom jeans | Rose and plateaued |
| flared pants | Long cycle (~20 years) |
| baggy jeans | Currently surging |
| corset top | Fashion micro-trend |
| oversized blazer | Steady rise |

Synthetic data with known ground-truth patterns is also generated via `data/generate_synthetic.py` for controlled experiment accuracy measurement.

---

## Project Structure

```
Project/
├── main.py                       # Entry point — connects all modules
├── api.py                        # Flask backend for the web demo
├── stream_simulator.py           # CSV → streaming events
├── sliding_window.py             # Incremental frequency counting (deque + hash map)
├── baseline.py                   # Naive full-scan (for comparison)
├── compare.py                    # Validates optimized output matches baseline
├── top_k.py                      # Heap-based + sort-based Top-K selection
├── burst_detection.py            # Ratio + difference burst scoring
├── cycle_detection.py            # Cosine similarity + trend classifier
├── accessibility.py              # Weighted multi-criteria scoring + heap ranking
├── experiments.py                # Benchmarking harness (timing + memory)
├── plots.py                      # matplotlib charts for experiments
├── config.py                     # Shared constants
├── data/
│   ├── google_trends/            # 10 real Google Trends CSVs
│   ├── accessibility_db.json     # Hand-curated accessibility scores (30 keywords)
│   └── generate_synthetic.py     # Synthetic data generator
├── tests/
│   ├── test_window.py            # Sliding window tests
│   ├── test_top_k.py             # Top-K unit tests
│   ├── test_cycle.py             # Cycle classification tests
│   ├── test_accessibility.py     # Accessibility scoring tests
│   └── test_integration.py       # End-to-end pipeline tests
├── report/                       # Progress reports
└── requirements.txt
```

---

## Team Responsibilities

| Member | Role | Key Files |
|---|---|---|
| **Bhoomika Panday** | Sliding Window Engine | `stream_simulator.py`, `sliding_window.py`, `baseline.py`, `compare.py` |
| **Vasudha Jain** | Ranking & Classification | `top_k.py`, `burst_detection.py`, `cycle_detection.py` |
| **Parvathi Gottumukkala** | Integration & Experiments | `main.py`, `accessibility.py`, `experiments.py`, `plots.py`, `api.py` |

---

## References

1. Cormen, T. H., Leiserson, C. E., Rivest, R. L., & Stein, C. (2022). *Introduction to Algorithms* (4th ed.). MIT Press.
2. Hunter, J. D. (2007). Matplotlib: A 2D graphics environment. *Computing in Science & Engineering*, 9(3), 90–95.
3. Google LLC. (2024). Google Trends. https://trends.google.com
