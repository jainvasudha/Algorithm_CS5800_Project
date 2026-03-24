# Real-Time Fashion Cycle Detection System

**Course:** CS5800 — Algorithms | Northeastern University | Spring 2026

**Team:** Bhoomika Panday, Vasudha Jain, Parvathi Gottumukkala

---

## What This Project Does

This system processes streaming fashion trend data from Google Trends and:

1. **Tracks** keyword frequency over time using a sliding window with incremental updates
2. **Ranks** the Top-K most frequent trends using a min-heap
3. **Detects bursts** — sudden spikes in trend popularity across consecutive time windows
4. **Classifies** each trend's lifecycle stage (New, Cyclical, Seasonal, Fading) using cosine similarity
5. **Scores** trends on accessibility using weighted multi-criteria scoring

No machine learning is used — only classical data structures and algorithms.

---

## System Pipeline

```
Google Trends CSV → Stream Simulator → [Sliding Window] → freq_map
                                                              │
                                            ┌─────────────────┼──────────────────┐
                                            ▼                 ▼                  ▼
                                      [Top-K Heap]    [Burst Detection]   [Cosine Sim]
                                            │                 │                  │
                                            ▼                 ▼                  ▼
                                      top K trends      bursting items     trend labels
                                            │                 │                  │
                                            └────────┬────────┘                  │
                                                     ▼                           │
                                            Combined Results  ◄──────────────────┘
                                                     │
                                            + accessibility score
                                                     ▼
                                               Final Output
```

---

## Algorithms & Data Structures

### 1. Sliding Window (Incremental Frequency Counting)

| | Naive | Optimized |
|---|---|---|
| **Approach** | Full scan of all events in window each query | Deque + hash map, incremental insert/expire |
| **Time** | O(N) per query | O(1) amortized per event |
| **Space** | O(N) | O(W) where W = window size |
| **Course Topic** | Baseline comparison | Hash Tables, Deques, Amortized Analysis |

### 2. Top-K Selection

| | Sort-Based | Heap-Based |
|---|---|---|
| **Approach** | Sort all M items, take first K | Min-heap of size K, single pass |
| **Time** | O(M log M) | O(M log K) |
| **Space** | O(M) | O(K) |
| **Course Topic** | Sorting (Timsort baseline) | Priority Queues, Heaps, Greedy |

**Key insight:** When K = 5 and M = 1000, the heap approach does ~5,000 comparisons vs ~10,000 for sorting. The advantage grows as M increases while K stays small.

### 3. Burst Detection (Two Scoring Variants)

| | Ratio Scoring | Difference Scoring |
|---|---|---|
| **Formula** | `current_freq / prev_freq` | `current_freq - prev_freq` |
| **Catches** | Small-absolute, high-relative spikes (e.g., 2 → 10) | Large-absolute spikes (e.g., 500 → 600) |
| **Time** | O(M) | O(M) |
| **Course Topic** | Algorithm Design, Complexity Analysis |

### 4. Cycle Classification (Cosine Similarity)

Compares a trend's current frequency vector against historical vectors to classify its lifecycle stage.

```
cos(v_current, v_historical) = (v_current · v_historical) / (‖v_current‖ × ‖v_historical‖)
```

| Label | Condition |
|---|---|
| Cyclical | High cosine similarity with a past trend vector |
| New | No historical match, recent emergence |
| Seasonal | Repeating pattern at regular intervals |
| Fading | Declining frequency over recent windows |

---

## Problem Definition

**Input:**
- A data stream `S = {(keyword_i, timestamp_i)}` of fashion keyword mentions over time
- Window size `W`, Top-K parameter `K`, burst threshold `B_thresh`, similarity threshold `C_thresh`

**Output (per window):**
- Top-K most frequent keywords
- Top-K bursting keywords with growth scores
- Lifecycle classification for each trend
- Accessibility score and ranking

---

## Data

We use **real Google Trends data** (2004–2026, monthly, worldwide) for 10 fashion keywords:

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

---

## Project Structure

```
Project/
├── main.py                       # Entry point — connects all modules
├── stream_simulator.py           # CSV → streaming events
├── sliding_window.py             # Incremental frequency counting (deque + hash map)
├── baseline.py                   # Naive full-scan (for comparison)
├── top_k.py                      # Heap-based + sort-based Top-K selection
├── burst_detection.py            # Ratio + difference burst scoring
├── cycle_detection.py            # Cosine similarity + trend classifier
├── accessibility.py              # Weighted multi-criteria scoring
├── experiments.py                # Benchmarking harness (timing + memory)
├── plots.py                      # matplotlib charts for experiments
├── config.py                     # Shared constants
├── data/
│   ├── google_trends/            # 10 real Google Trends CSVs
│   ├── accessibility_db.json     # Hand-curated accessibility scores
│   └── generate_synthetic.py     # Synthetic data generator
├── tests/
│   ├── test_top_k.py             # Top-K unit tests
│   ├── test_window.py            # Sliding window tests
│   ├── test_burst.py             # Burst detection tests
│   ├── test_cycle.py             # Cycle classification tests
│   └── test_integration.py       # End-to-end pipeline tests
├── report/                       # Final report
└── requirements.txt
```

---

## Experiments

Three key comparisons form the core empirical analysis:

| # | Experiment | What We Vary | What We Measure |
|---|---|---|---|
| 1 | **Sliding Window: Incremental vs Naive** | Stream size N (1K → 100K) | Wall-clock time |
| 2 | **Top-K: Heap vs Sort** | M (distinct items: 50–5000), K (5–500) | Runtime |
| 3 | **Burst Detection: Ratio vs Difference** | Threshold (1.5–10.0) | Detection rate, false positives |

---

## Setup

```bash
pip install -r requirements.txt
```

**Dependencies:** `matplotlib`, `pytest`, `pytrends` — everything else is Python standard library (`heapq`, `collections`, `math`, `csv`, `time`, `tracemalloc`).

## Run Tests

```bash
python -m pytest tests/ -v
```

---

## Team Responsibilities

| Member | Module | Key Files |
|---|---|---|
| **Bhoomika** | Sliding Window Engine | `stream_simulator.py`, `sliding_window.py`, `baseline.py` |
| **Vasudha** | Ranking & Analysis | `top_k.py`, `burst_detection.py`, `cycle_detection.py` |
| **Parvathi** | Integration & Experiments | `main.py`, `accessibility.py`, `experiments.py`, `plots.py` |

---

## Course Topic Mapping

| Course Topic | Where It Appears |
|---|---|
| Hash Tables | Frequency counting — O(1) amortized updates |
| Queues / Deques | Sliding window event management |
| Priority Queues / Heaps | Min-heap for Top-K selection |
| Sorting | Baseline comparison for Top-K |
| Amortized Analysis | Sliding window insert/expire |
| Complexity Analysis | Theoretical + empirical for every component |
| Algorithm Design | Burst detection, cycle classification |
| Greedy | Heap maintenance — always keep K largest seen so far |
