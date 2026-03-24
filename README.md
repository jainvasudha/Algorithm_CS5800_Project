# CS5800: Algorithms — Final Project Master Document

## Real-Time Fashion Cycle Detection System with Accessibility Scoring

> **Course:** CS5800 — Algorithms | Northeastern University | Spring 2026
>
> **Team:** Bhoomika Panday, Vasudha Jain, Parvathi Gottumukkala

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Gap Analysis — Loopholes Found in Current Proposals](#2-gap-analysis--loopholes-found-in-current-proposals)
3. [Unified Problem Definition](#3-unified-problem-definition)
4. [System Architecture](#4-system-architecture)
5. [Module Specifications with Pseudocode](#5-module-specifications-with-pseudocode)
6. [Complexity Analysis (Time + Space)](#6-complexity-analysis-time--space)
7. [Data Strategy](#7-data-strategy)
8. [Scalability Experiments Plan](#8-scalability-experiments-plan)
9. [Work Distribution — Parallel Development Plan](#9-work-distribution--parallel-development-plan)
10. [Interface Contracts (Enabling Parallel Work)](#10-interface-contracts-enabling-parallel-work)
11. [Week-by-Week Execution Plan](#11-week-by-week-execution-plan)
12. [Edge Cases and Correctness](#12-edge-cases-and-correctness)
13. [Testing Strategy](#13-testing-strategy)
14. [Expected Deliverables](#14-expected-deliverables)
15. [Course Topic Mapping](#15-course-topic-mapping)
16. [Risk Register](#16-risk-register)

---

## 1. Executive Summary

This project builds a **Real-Time Fashion Cycle Detection System** that processes streaming fashion trend data and:

1. **Tracks** keyword frequency over time using a sliding window with incremental updates
2. **Ranks** the Top-K most frequent/fastest-growing trends using a min-heap
3. **Detects bursts** — sudden spikes in trend popularity across consecutive windows
4. **Classifies** each trend's lifecycle stage (New, Cyclical, Seasonal, Fading) using cosine similarity against historical patterns
5. **Scores** each trend on accessibility/inclusivity using a weighted multi-criteria algorithm
6. **Benchmarks** every algorithm against a naive baseline to demonstrate algorithmic efficiency

The system uses **no machine learning** — only classical data structures and algorithms (hash maps, deques, heaps, sorting, cosine similarity, rule-based classification).

### Why This Project Works for CS5800

| Course Topic | How It Appears in the Project |
|---|---|
| Hash Tables | Frequency counting with O(1) amortized updates |
| Queues / Deques | Sliding window event management |
| Priority Queues / Heaps | Min-heap for Top-K selection |
| Sorting | Baseline comparison for Top-K; ranking output |
| Amortized Analysis | Sliding window insert/expire is amortized O(1) |
| Complexity Analysis | Theoretical + empirical for every component |
| Algorithm Design | Burst detection, cycle classification, accessibility scoring |
| Graph / Greedy (bonus) | Dependency-aware trend grouping if time permits |

---

## 2. Gap Analysis — Loopholes Found in Current Proposals

We had two proposal documents. Below is a thorough analysis of the loopholes, inconsistencies, and missing pieces found across both.

### 2.1 Inconsistencies Between the Two Documents

| Issue | Proposal 1 (Algorithm_Project_Proposal) | Proposal 2 (Fashion_Cycle_Detection) | Impact |
|---|---|---|---|
| **Scope divergence** | Generic "streaming trend detection" | Adds fashion lifecycle classification + accessibility scoring | Unclear which is the actual project |
| **Work distribution** | Bhoomika: sliding window, Vasudha: ranking + burst, Parvathi: experiments | Member 1: sliding window + peak, Member 2: cosine + classification, Member 3: accessibility + report | Completely different divisions — team doesn't have a single plan |
| **Top-K selection** | Core component (heap vs sort) | Not mentioned at all | A strong algorithmic comparison is lost |
| **Burst detection** | Core component | Not mentioned at all | Another strong algorithmic component lost |
| **Cosine similarity** | Not mentioned | Core component for cycle detection | Good addition, but absent from the "official" proposal |
| **Accessibility scoring** | Not mentioned | Core feature | Novel, but needs algorithmic depth |
| **Algorithm list** | Hash tables, deque, min-heap, sorting, amortized analysis | Sliding window, local maxima, cosine sim, hash map, rule-based, comparison sort | Partially overlapping, partially contradictory |

### 2.2 Loopholes and Gaps (Both Documents)

#### Gap 1: No Formal Mathematical Problem Statement
Both documents describe the problem in English but never formally define it. For an algorithms course, you need:
- Formal input/output specification
- Mathematical notation for the streaming model
- Clear definitions of what "trend," "burst," and "cycle" mean algorithmically

**Fix:** Section 3 of this document provides the formal definition.

#### Gap 2: Accessibility Scoring Lacks Algorithmic Depth
The current design is a simple 4-factor binary checklist (score = count of True values out of 4). This is essentially a lookup table — not an algorithm. A professor reviewing this would question what algorithmic content it demonstrates.

**Fix:** Redesign as a **weighted multi-criteria scoring algorithm** with:
- Configurable weights per factor
- Normalization across different scale types (binary, ordinal, continuous)
- Priority-queue-based ranking of trends by composite score
- This adds genuine algorithmic substance (weighted aggregation, heap-based ranking)

#### Gap 3: Burst Detection Definition is Vague
Proposal 1 says "comparing frequency distributions across consecutive time windows" but never defines:
- What metric compares two windows? (absolute difference? ratio? z-score?)
- What threshold qualifies as a "burst"?
- How to handle the cold-start problem (first window has no predecessor)

**Fix:** Section 5.3 provides a formal burst detection algorithm with configurable thresholds.

#### Gap 4: Cosine Similarity is Underspecified
Proposal 2 says "compare current vs. historical trend patterns" but doesn't explain:
- What are the vectors being compared? (frequency-over-time vectors?)
- How long is the historical window? How is it chosen?
- What similarity threshold distinguishes "cyclical" from "new"?
- How do you build the historical database from a single CSV?

**Fix:** Section 5.4 provides the full specification.

#### Gap 5: Rule-Based Classifier Has No Formal Rules
"Assign the final trend label using simple conditions" — but what conditions? The rules are never stated.

**Fix:** Section 5.5 provides a formal decision tree with explicit thresholds.

#### Gap 6: No Pseudocode
Neither document has pseudocode for any algorithm. This is essential for an algorithms course — the professor needs to see algorithm-level thinking, not just a list of data structures.

**Fix:** Section 5 provides pseudocode for every core algorithm.

#### Gap 7: No Space Complexity Analysis
Both documents discuss time complexity but completely ignore space complexity. For streaming algorithms, space is often the critical constraint.

**Fix:** Section 6 covers both time and space complexity for every component.

#### Gap 8: No Edge Cases Discussed
Neither document considers: empty windows, zero-frequency items, ties in Top-K, single data point in time series, all items having the same frequency, division by zero in burst ratio.

**Fix:** Section 12 provides a comprehensive edge-case catalog with handling strategies.

#### Gap 9: "Streaming" Simulation Not Defined
Both mention processing "streaming data" but use static CSV files. How does a CSV become a stream? Neither document explains the simulation approach.

**Fix:** Section 7 defines the exact simulation: read CSV row-by-row, emit events with timestamps, process each event through the pipeline as if arriving in real time.

#### Gap 10: No Integration/Interface Plan
Neither document explains how the three modules connect. Without defined interfaces, three team members cannot work in parallel — they'd constantly block each other.

**Fix:** Section 10 defines explicit interface contracts (function signatures, data types) so each person can develop and test independently.

#### Gap 11: Scalability Experiments Missing from Proposal 2
Proposal 1 mentions scalability experiments (varying stream size, window size, K, distinct items). Proposal 2 drops this entirely, which is a major loss — empirical evaluation is critical for an algorithms course.

**Fix:** Section 8 defines the complete experiment plan.

#### Gap 12: No Testing Strategy
Neither document explains how to verify correctness. "It runs" is not sufficient — you need unit tests with known expected outputs.

**Fix:** Section 13 provides the testing approach.

#### Gap 13: Peak Detection is Underspecified
"Local maxima scan" — compare with immediate neighbors? Use smoothing? What about plateaus (consecutive equal values)?

**Fix:** Section 5.2 formalizes peak detection with a configurable neighborhood parameter.

#### Gap 14: No Visualization Plan
The proposal mentions "minimal visualization" but doesn't specify what. For the final presentation, you need clear graphs.

**Fix:** Section 14 lists the exact plots and visualizations to produce.

#### Gap 15: Timeline Doesn't Account for Unified Scope
Proposal 1's 5-week plan was designed for a different scope. With the added cycle detection and accessibility features, the timeline needs adjustment.

**Fix:** Section 11 provides the updated week-by-week plan.

---

## 3. Unified Problem Definition

### 3.1 Formal Problem Statement

**Input:**
- A data stream `S = {(keyword_i, timestamp_i) : i = 1, 2, ..., N}` where each event represents a fashion keyword mention at a given time
- A window size `W` (time duration of each sliding window)
- A parameter `K` (number of top trends to track)
- A burst threshold `B_thresh` (minimum growth ratio to qualify as a burst)
- A similarity threshold `C_thresh` (minimum cosine similarity to classify a trend as cyclical)
- A set of historical trend vectors `H = {h_1, h_2, ..., h_p}` (from the first half of the dataset)

**Output:**
For each window position, produce:
1. `TopK_freq`: The K most frequent keywords in the current window
2. `TopK_burst`: The K keywords with the highest burst score (growth rate)
3. `Classification`: For each keyword in TopK, a label from {New, Cyclical, Seasonal, Fading}
4. `Accessibility`: For each classified trend, a weighted accessibility score and rank

### 3.2 Definitions

| Term | Formal Definition |
|---|---|
| **Sliding Window** | At time `t`, the active window contains all events with `timestamp ∈ (t - W, t]` |
| **Frequency** | `freq(k, t) = count of events with keyword = k in window at time t` |
| **Burst Score** | `burst(k, t) = freq(k, t) / freq(k, t-1)` if `freq(k, t-1) > 0`, else `freq(k, t)` if `freq(k, t) > 0`, else `0` |
| **Trend Vector** | For keyword `k`, the vector `v_k = [freq(k, t_1), freq(k, t_2), ..., freq(k, t_n)]` across `n` consecutive windows |
| **Cosine Similarity** | `cos(v_current, v_historical) = (v_current · v_historical) / (‖v_current‖ × ‖v_historical‖)` |
| **Cyclical Trend** | A keyword `k` where `max_h∈H cos(v_k, h) ≥ C_thresh` |
| **Accessibility Score** | `A(k) = Σ(w_i × f_i(k))` where `w_i` are factor weights and `f_i` are factor values |

### 3.3 What Is Explicitly Out of Scope

- Machine learning, NLP, sentiment analysis
- Live API integration or web scraping
- Distributed systems (Spark, Kafka)
- UI/UX beyond terminal output and matplotlib plots
- Statistical modeling beyond burst detection

---

## 4. System Architecture

### 4.1 Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SYSTEM PIPELINE (Left to Right)                   │
│                                                                     │
│  ┌──────────┐   ┌──────────────┐   ┌──────────────┐   ┌─────────┐ │
│  │  DATA     │──>│  SLIDING     │──>│  RANKING &   │──>│ OUTPUT  │ │
│  │  INGEST   │   │  WINDOW      │   │  ANALYSIS    │   │ & EVAL  │ │
│  │          │   │  ENGINE      │   │  ENGINE      │   │         │ │
│  │ - CSV     │   │ - Deque      │   │ - Top-K Heap │   │ - Rank  │ │
│  │ - Synth   │   │ - Hash Map   │   │ - Burst Det. │   │ - Score │ │
│  │ - Stream  │   │ - Expire     │   │ - Cosine Sim │   │ - Bench │ │
│  │   Sim     │   │ - Frequency  │   │ - Classify   │   │ - Plot  │ │
│  └──────────┘   └──────────────┘   └──────────────┘   └─────────┘ │
│                                                                     │
│  MODULE A (Bhoomika)  MODULE B (Vasudha)   MODULE C (Parvathi)     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Data Flow

```
Raw CSV / Synthetic Data
        │
        ▼
  Stream Simulator (emits events one-by-one)
        │
        ▼
  ┌─ Sliding Window Engine ─────────────────────────┐
  │  event arrives → append to deque                  │
  │  expire old events → remove from front of deque   │
  │  update hash map: freq[keyword] += 1 or -= 1      │
  │  OUTPUT: freq_map = {keyword: count}              │
  └──────────────────────────────────────────────────┘
        │
        ▼
  ┌─ Top-K Selection ───────────────────────────────┐
  │  INPUT: freq_map                                  │
  │  Build min-heap of size K                         │
  │  OUTPUT: top_k_list = [(keyword, count), ...]    │
  └──────────────────────────────────────────────────┘
        │
        ▼
  ┌─ Burst Detection ──────────────────────────────┐
  │  INPUT: freq_map(current), freq_map(previous)    │
  │  Compute burst_score for each keyword             │
  │  Select Top-K by burst_score (heap)               │
  │  OUTPUT: burst_list = [(keyword, burst_score)]   │
  └──────────────────────────────────────────────────┘
        │
        ▼
  ┌─ Cycle Classification ─────────────────────────┐
  │  INPUT: trend_vector(keyword), historical_db     │
  │  Compute cosine similarity vs historical vectors  │
  │  Apply rule-based classifier                      │
  │  OUTPUT: label ∈ {New, Cyclical, Seasonal, Fading}│
  └──────────────────────────────────────────────────┘
        │
        ▼
  ┌─ Accessibility Scoring ─────────────────────────┐
  │  INPUT: classified trends, accessibility_db       │
  │  Compute weighted multi-criteria score            │
  │  Rank by composite score (heap or sort)           │
  │  OUTPUT: ranked_trends with scores and alerts    │
  └──────────────────────────────────────────────────┘
        │
        ▼
  ┌─ Benchmarking & Output ─────────────────────────┐
  │  Compare optimized vs baseline runtimes           │
  │  Generate plots and tables                        │
  │  Format final output                              │
  └──────────────────────────────────────────────────┘
```

---

## 5. Module Specifications with Pseudocode

### 5.1 Module A: Sliding Window Frequency Engine

**Owner:** Bhoomika Panday

**Purpose:** Maintain accurate frequency counts of keywords within a time-bounded window, supporting O(1) amortized updates.

#### Data Structures

| Structure | Type | Purpose |
|---|---|---|
| `event_queue` | `collections.deque` | Ordered list of `(timestamp, keyword)` events in the window |
| `freq_map` | `dict` (hash map) | `{keyword: count}` — current frequency of each keyword |

#### Pseudocode: Incremental Sliding Window

```
ALGORITHM: IncrementalSlidingWindow

DATA STRUCTURES:
    event_queue ← empty deque
    freq_map ← empty hash map
    window_size ← W

FUNCTION process_event(timestamp, keyword):
    # Step 1: Add new event
    event_queue.append((timestamp, keyword))
    freq_map[keyword] ← freq_map.get(keyword, 0) + 1

    # Step 2: Expire old events
    WHILE event_queue is not empty
      AND event_queue.front().timestamp ≤ (timestamp - window_size):
        (old_ts, old_kw) ← event_queue.popleft()
        freq_map[old_kw] ← freq_map[old_kw] - 1
        IF freq_map[old_kw] = 0:
            DELETE freq_map[old_kw]    # remove zero-count entries

    RETURN freq_map    # current snapshot
```

#### Pseudocode: Baseline (Full Recomputation)

```
ALGORITHM: BaselineRecomputation

FUNCTION get_frequencies(all_events, current_time, window_size):
    freq_map ← empty hash map
    FOR EACH (timestamp, keyword) IN all_events:
        IF timestamp > (current_time - window_size) AND timestamp ≤ current_time:
            freq_map[keyword] ← freq_map.get(keyword, 0) + 1
    RETURN freq_map
```

#### Correctness Invariant

At any point after `process_event` returns:
- `event_queue` contains exactly those events with `timestamp ∈ (current_time - W, current_time]`
- For every keyword `k`: `freq_map[k] = |{e ∈ event_queue : e.keyword = k}|`
- No keyword in `freq_map` has count 0

#### Amortized Analysis

Each event enters the deque exactly once and leaves exactly once. The hash map update (insert, increment, decrement, delete) is O(1) average per operation.

- **Insert:** O(1) — append to deque + hash map increment
- **Expire:** O(1) amortized — each event is removed at most once
- **Total for N events:** O(N) amortized

#### Stream Simulator

```
ALGORITHM: StreamSimulator

FUNCTION simulate_stream(csv_file):
    data ← load_csv(csv_file)   # columns: date, keyword_1, keyword_2, ...
    event_stream ← empty list

    FOR EACH row IN data:
        timestamp ← parse_date(row.date)
        FOR EACH keyword_column IN keyword_columns:
            # Google Trends value (0-100) represents relative popularity
            # We convert it to event count by treating value as frequency
            count ← row[keyword_column]
            FOR i FROM 1 TO count:
                event_stream.append((timestamp, keyword_column))

    # Sort by timestamp to ensure chronological order
    SORT event_stream BY timestamp
    RETURN event_stream
```

---

### 5.2 Module B-1: Top-K Selection

**Owner:** Vasudha Jain

**Purpose:** Extract the K most frequent (or highest-burst) items from the frequency map efficiently.

#### Pseudocode: Heap-Based Top-K

```
ALGORITHM: HeapTopK

FUNCTION top_k_frequent(freq_map, K):
    min_heap ← empty min-heap (ordered by count)

    FOR EACH (keyword, count) IN freq_map:
        IF heap.size < K:
            heap.push((count, keyword))
        ELSE IF count > heap.peek().count:
            heap.pop()                    # remove smallest
            heap.push((count, keyword))   # add new larger element

    # Extract and sort results in descending order
    result ← []
    WHILE heap is not empty:
        result.append(heap.pop())
    REVERSE result
    RETURN result
```

#### Pseudocode: Baseline (Full Sort)

```
ALGORITHM: SortTopK

FUNCTION top_k_by_sorting(freq_map, K):
    items ← list of (keyword, count) from freq_map
    SORT items BY count DESCENDING        # O(M log M)
    RETURN items[0 : K]
```

#### Complexity Comparison

| Approach | Time | Space | When Better |
|---|---|---|---|
| Heap-based | O(M log K) | O(K) | When K << M (the common case) |
| Full sort | O(M log M) | O(M) | Only when K ≈ M |

Where M = number of distinct keywords in the window.

**Key insight for the report:** When K = 5 and M = 1000, heap does ~5000 comparisons vs sort doing ~10000. The advantage grows as M increases and K stays small.

---

### 5.3 Module B-2: Burst Detection

**Owner:** Vasudha Jain

**Purpose:** Identify keywords with sudden popularity spikes by comparing frequency across consecutive windows.

#### Burst Score Definition

For keyword `k` at window `t`:

```
                    ┌ freq(k, t) / freq(k, t-1)     if freq(k, t-1) > 0
burst_score(k, t) = ┤ freq(k, t)                     if freq(k, t-1) = 0 and freq(k, t) > 0
                    └ 0                               otherwise
```

A keyword is **bursting** if `burst_score(k, t) ≥ B_thresh` (default B_thresh = 2.0, meaning the frequency at least doubled).

#### Pseudocode

```
ALGORITHM: BurstDetection

FUNCTION detect_bursts(current_freq, previous_freq, K, B_thresh):
    burst_scores ← empty hash map

    # Score all keywords present in the current window
    FOR EACH (keyword, count) IN current_freq:
        prev_count ← previous_freq.get(keyword, 0)
        IF prev_count > 0:
            burst_scores[keyword] ← count / prev_count
        ELSE:
            burst_scores[keyword] ← count    # brand new = burst by definition

    # Filter by threshold
    bursting ← {k: s FOR (k, s) IN burst_scores IF s ≥ B_thresh}

    # Top-K bursting items (reuse heap-based Top-K)
    RETURN top_k_frequent(bursting, K)
```

#### Scoring Functions — Two Variants to Compare

| Function | Formula | Pros | Cons |
|---|---|---|---|
| **Ratio** (default) | `current / previous` | Captures multiplicative growth | Sensitive to small denominators |
| **Difference** | `current - previous` | Captures absolute growth | Ignores relative change |

**Enhancement:** Implement both and let experiments show which is more meaningful for different scenarios. In the report, analyze when ratio-based vs difference-based scoring is more appropriate.

---

### 5.4 Module B-3: Cycle Classification via Cosine Similarity

**Owner:** Vasudha Jain

**Purpose:** Determine whether a trend is new, returning (cyclical), seasonal, or fading by comparing its current frequency pattern against historical patterns.

#### How Historical Patterns Are Built

```
Full dataset timeline:  [────────────────────────────────────]
                         |← historical half →|← current half →|

Historical half: divided into fixed-size segments.
For each keyword, extract a vector of frequencies across segments.
Store these as the "historical database."
```

#### Cosine Similarity

For two vectors `u` and `v` of length `n`:

```
cos(u, v) = (u · v) / (‖u‖ × ‖v‖)
          = Σ(u_i × v_i) / (√Σ(u_i²) × √Σ(v_i²))
```

- Result range: [-1, 1] for general vectors; [0, 1] for non-negative frequency vectors
- 1.0 = identical pattern shape (ignoring magnitude)
- 0.0 = completely unrelated patterns

#### Pseudocode

```
ALGORITHM: CycleSimilarity

FUNCTION compute_cosine_similarity(vec_a, vec_b):
    IF length(vec_a) ≠ length(vec_b):
        # Pad the shorter vector with zeros or truncate
        min_len ← min(length(vec_a), length(vec_b))
        vec_a ← vec_a[0 : min_len]
        vec_b ← vec_b[0 : min_len]

    dot_product ← 0
    norm_a ← 0
    norm_b ← 0

    FOR i FROM 0 TO length(vec_a) - 1:
        dot_product ← dot_product + vec_a[i] × vec_b[i]
        norm_a ← norm_a + vec_a[i]²
        norm_b ← norm_b + vec_b[i]²

    IF norm_a = 0 OR norm_b = 0:
        RETURN 0.0    # zero vector — no pattern to compare

    RETURN dot_product / (√norm_a × √norm_b)


FUNCTION find_best_historical_match(current_vector, historical_db):
    best_sim ← -1
    best_match ← None

    FOR EACH (hist_keyword, hist_vector) IN historical_db:
        sim ← compute_cosine_similarity(current_vector, hist_vector)
        IF sim > best_sim:
            best_sim ← sim
            best_match ← hist_keyword

    RETURN (best_match, best_sim)
```

---

### 5.5 Module B-4: Rule-Based Trend Classifier

**Owner:** Vasudha Jain

**Purpose:** Assign each trend a lifecycle label based on burst score, cosine similarity, and frequency trajectory.

#### Classification Rules (Formal Decision Tree)

```
ALGORITHM: ClassifyTrend

FUNCTION classify(keyword, burst_score, cosine_sim, freq_trajectory):
    # freq_trajectory = list of frequencies across recent windows
    # trend_direction = slope of frequency over recent windows

    trend_direction ← compute_slope(freq_trajectory)

    # Rule 1: Is it declining?
    IF trend_direction < -DECLINE_THRESHOLD:
        RETURN "Fading"

    # Rule 2: Does it match a historical pattern?
    IF cosine_sim ≥ CYCLICAL_THRESHOLD:        # default 0.75
        # Check if the match is seasonal (periodic) or cyclical (irregular return)
        IF historical_match_is_periodic(keyword):
            RETURN "Seasonal"
        ELSE:
            RETURN "Cyclical"

    # Rule 3: Is it bursting with no historical precedent?
    IF burst_score ≥ BURST_THRESHOLD AND cosine_sim < CYCLICAL_THRESHOLD:
        RETURN "New"

    # Rule 4: Moderate growth, no strong historical match
    IF trend_direction > 0:
        RETURN "New"

    # Default: stable/flat trend
    RETURN "Fading"


FUNCTION compute_slope(freq_list):
    # Simple linear regression slope
    n ← length(freq_list)
    IF n < 2: RETURN 0
    x_mean ← (n - 1) / 2
    y_mean ← sum(freq_list) / n
    numerator ← Σ((i - x_mean) × (freq_list[i] - y_mean)) FOR i IN 0..n-1
    denominator ← Σ((i - x_mean)²) FOR i IN 0..n-1
    IF denominator = 0: RETURN 0
    RETURN numerator / denominator
```

#### Classification Thresholds (Configurable)

| Parameter | Default Value | Meaning |
|---|---|---|
| `CYCLICAL_THRESHOLD` | 0.75 | Minimum cosine similarity to consider a trend cyclical |
| `BURST_THRESHOLD` | 2.0 | Minimum burst score to consider a trend "bursting" |
| `DECLINE_THRESHOLD` | -0.3 | Slope below which a trend is considered fading |
| `SEASONAL_PERIOD_TOLERANCE` | 0.1 | Tolerance for periodic pattern matching |

---

### 5.6 Module B-5: Peak Detection

**Owner:** Vasudha Jain (integrated into burst detection)

**Purpose:** Find local maxima in a keyword's frequency time series.

#### Pseudocode

```
ALGORITHM: PeakDetection

FUNCTION find_peaks(freq_series, neighborhood=1):
    # freq_series = [f_0, f_1, ..., f_n-1]
    # A point i is a peak if it is strictly greater than all points
    # within 'neighborhood' distance on both sides

    peaks ← empty list

    FOR i FROM neighborhood TO length(freq_series) - neighborhood - 1:
        is_peak ← TRUE
        FOR j FROM (i - neighborhood) TO (i + neighborhood):
            IF j ≠ i AND freq_series[j] ≥ freq_series[i]:
                is_peak ← FALSE
                BREAK
        IF is_peak:
            peaks.append((i, freq_series[i]))    # (index, value)

    RETURN peaks
```

---

### 5.7 Module C: Accessibility Scoring

**Owner:** Parvathi Gottumukkala

**Purpose:** Score each detected trend on inclusivity/accessibility using a weighted multi-criteria algorithm, then rank trends.

#### Why This Needs Algorithmic Depth (Not Just a Checklist)

The original proposal had 4 binary factors scored as count-of-true (e.g., 3/4). This is too simple for an algorithms project. The enhanced version:

1. **Supports mixed factor types** — binary, ordinal (1-5 scale), and continuous
2. **Uses configurable weights** — different stakeholders may weight factors differently
3. **Normalizes across scales** — min-max normalization so different scale types are comparable
4. **Ranks using a heap** — integrates with the Top-K infrastructure

#### Accessibility Factors (Enhanced)

| Factor | Type | Scale | Description |
|---|---|---|---|
| `wheelchair_friendly` | Binary | {0, 1} | Easy to wear while seated? |
| `adaptive_wearability` | Ordinal | {1, 2, 3, 4, 5} | How easily modified for adaptive use? (1=hard, 5=easy) |
| `size_inclusive` | Ordinal | {1, 2, 3, 4, 5} | Range of sizes available (1=very limited, 5=fully inclusive) |
| `sensory_friendly` | Binary | {0, 1} | Non-irritating for sensory sensitivities? |
| `price_accessibility` | Ordinal | {1, 2, 3, 4, 5} | Affordability (1=luxury only, 5=widely affordable) |

**Data source:** A manually curated lookup table (JSON/CSV) mapping fashion keywords to their accessibility attributes. This is pre-built before the system runs. For demonstration purposes, the team will create a curated dataset of ~30-50 fashion items with hand-assigned scores.

#### Pseudocode: Weighted Multi-Criteria Scoring

```
ALGORITHM: AccessibilityScoring

CONSTANTS:
    # Default weights (must sum to 1.0)
    DEFAULT_WEIGHTS = {
        "wheelchair_friendly": 0.20,
        "adaptive_wearability": 0.25,
        "size_inclusive": 0.25,
        "sensory_friendly": 0.15,
        "price_accessibility": 0.15
    }

    # Min-max ranges for normalization
    FACTOR_RANGES = {
        "wheelchair_friendly": (0, 1),
        "adaptive_wearability": (1, 5),
        "size_inclusive": (1, 5),
        "sensory_friendly": (0, 1),
        "price_accessibility": (1, 5)
    }

FUNCTION normalize(value, min_val, max_val):
    IF max_val = min_val:
        RETURN 1.0
    RETURN (value - min_val) / (max_val - min_val)

FUNCTION compute_accessibility_score(keyword, accessibility_db, weights):
    IF keyword NOT IN accessibility_db:
        RETURN (0.0, "NO_DATA")    # flag for alert

    factors ← accessibility_db[keyword]
    score ← 0.0

    FOR EACH (factor_name, weight) IN weights:
        raw_value ← factors[factor_name]
        (min_val, max_val) ← FACTOR_RANGES[factor_name]
        normalized ← normalize(raw_value, min_val, max_val)
        score ← score + (weight × normalized)

    RETURN (score, classify_accessibility(score))

FUNCTION classify_accessibility(score):
    IF score ≥ 0.8: RETURN "Highly Accessible"
    IF score ≥ 0.5: RETURN "Moderately Accessible"
    IF score ≥ 0.3: RETURN "Limited Accessibility"
    RETURN "Low Accessibility"

FUNCTION rank_trends_by_accessibility(trend_list, accessibility_db, weights, K):
    # Use min-heap to get Top-K most accessible trends
    scored_trends ← []
    alerts ← []

    FOR EACH trend IN trend_list:
        (score, label) ← compute_accessibility_score(
            trend.keyword, accessibility_db, weights
        )
        scored_trends.append((trend, score, label))
        IF label = "NO_DATA" OR label = "Low Accessibility":
            alerts.append(trend.keyword)

    # Rank using heap-based Top-K (reuse from Module B)
    ranked ← top_k_by_score(scored_trends, K)

    RETURN (ranked, alerts)
```

---

## 6. Complexity Analysis (Time + Space)

### 6.1 Per-Component Complexity

| Component | Time (Optimized) | Time (Baseline) | Space | Key Variable |
|---|---|---|---|---|
| **Sliding Window Update** | O(1) amortized | O(N) per query | O(W_events) | W_events = events in window |
| **Full Recomputation** | O(N) per query | — | O(N) | N = total events |
| **Top-K (Heap)** | O(M log K) | O(M log M) sort | O(K) | M = distinct keywords |
| **Top-K (Sort)** | O(M log M) | — | O(M) | M = distinct keywords |
| **Burst Detection** | O(M) + O(M log K) | O(M log M) | O(M) | M = distinct keywords |
| **Cosine Similarity (one pair)** | O(n) | — | O(n) | n = vector length |
| **Cycle Classification (one keyword)** | O(P × n) | — | O(P × n) | P = historical patterns |
| **Peak Detection** | O(n × d) | — | O(n) | d = neighborhood size |
| **Accessibility Scoring** | O(F) per keyword | — | O(F) | F = number of factors |
| **Accessibility Ranking** | O(T log K) | O(T log T) sort | O(K) | T = number of trends |

### 6.2 End-to-End Pipeline Complexity

**Per window step (optimized):**
```
O(1)_amortized          — window update
+ O(M log K)            — Top-K by frequency
+ O(M)                  — burst score computation
+ O(M log K)            — Top-K by burst
+ O(K × P × n)          — cycle classification for K trends
+ O(K × F)              — accessibility scoring for K trends
+ O(K log K)            — final ranking

= O(M log K + K × P × n)   — dominated by classification when P is large
```

**Per window step (baseline):**
```
O(N) + O(M log M) + O(M log M) + O(K × P × n) + O(K × F)
= O(N + M log M + K × P × n)
```

### 6.3 Space Complexity Summary

| Component | Space | What It Stores |
|---|---|---|
| Event queue (deque) | O(W_events) | All events in the current window |
| Frequency map | O(M) | Distinct keyword counts |
| Previous frequency map | O(M) | Snapshot of last window's frequencies |
| Historical database | O(P × n) | P historical vectors of length n |
| Top-K heap | O(K) | Current top-K items |
| Accessibility DB | O(V × F) | V vocabulary items × F factors |
| **Total** | **O(W_events + M + P × n + V × F)** | |

---

## 7. Data Strategy

### 7.1 Primary Data: Google Trends CSV

**Source:** Google Trends (free download, no API needed)

**How to get it:**
1. Go to Google Trends
2. Search for a fashion keyword (e.g., "wide-leg jeans")
3. Set time range (e.g., 2004–present for long history)
4. Download CSV

**CSV format:**
```
Week,wide-leg jeans
2004-01-04,2
2004-01-11,3
2004-01-18,2
...
2025-03-09,78
```

- Values are 0–100 (relative search interest, 100 = peak)
- One row per week
- Can download up to 5 keywords per comparison

**Recommended keywords (fashion-relevant):**

| Keyword | Why |
|---|---|
| "wide-leg jeans" | Currently trending, potential cyclical pattern |
| "skinny jeans" | Was huge, now fading — good for "Fading" detection |
| "cargo pants" | Classic cyclical — popular in 2000s, returning now |
| "Y2K fashion" | Burst pattern — sudden revival |
| "low-rise jeans" | Controversial comeback — seasonal/cyclical |
| "mom jeans" | Rose and plateaued — tests different trajectory |
| "flared pants" | Cyclical pattern with ~20-year cycle |
| "baggy jeans" | Currently surging — burst candidate |

**Download at least 8–10 keywords** to have enough data for meaningful experiments.

### 7.2 Streaming Simulation Approach

Google Trends gives weekly aggregated data. To simulate streaming:

```
Method: Expand each weekly value into individual events

For each row (week, keyword, value):
    Generate 'value' events at random times within that week
    Each event = (timestamp, keyword)

This converts aggregated CSV data into an event stream
that can be processed event-by-event.
```

### 7.3 Synthetic Data (For Edge-Case Testing)

Generate synthetic data to test specific scenarios:

| Scenario | Pattern | Purpose |
|---|---|---|
| **Pure burst** | 0,0,0,0,100,100,0,0 | Test burst detection |
| **Gradual rise** | 1,2,4,8,16,32,64 | Exponential growth |
| **Cyclical** | 10,50,10,50,10,50 | Perfect repeating cycle |
| **Seasonal** | 0,0,80,0,0,0,80,0,0,0 | Periodic spike |
| **Fading** | 100,80,60,40,20,5,1 | Steady decline |
| **Flat** | 50,50,50,50,50 | No change — should not trigger |
| **Single spike** | 0,0,100,0,0 | One-time anomaly |
| **Tie in Top-K** | Multiple keywords at same frequency | Test tie-breaking |

### 7.4 Historical Database Construction

```
Full CSV timeline: [week_1, week_2, ..., week_N]

Split:
  Historical half: [week_1, ..., week_N/2]     → build historical pattern DB
  Current half:    [week_N/2+1, ..., week_N]   → simulate as incoming stream

For each keyword in historical half:
  Extract frequency vector → store in historical_db
  This is what cosine similarity compares against
```

### 7.5 Accessibility Lookup Table

Create a JSON file manually mapping keywords to accessibility scores:

```json
{
  "wide-leg jeans": {
    "wheelchair_friendly": 1,
    "adaptive_wearability": 4,
    "size_inclusive": 4,
    "sensory_friendly": 1,
    "price_accessibility": 3
  },
  "skinny jeans": {
    "wheelchair_friendly": 0,
    "adaptive_wearability": 2,
    "size_inclusive": 3,
    "sensory_friendly": 0,
    "price_accessibility": 4
  }
}
```

Curate this for all keywords in the dataset (~30-50 entries). This is a one-time manual effort.

---

## 8. Scalability Experiments Plan

### 8.1 Independent Variables

| Variable | Values to Test | What It Reveals |
|---|---|---|
| **Stream size (N)** | 1K, 5K, 10K, 50K, 100K, 500K events | How algorithms scale with data volume |
| **Window size (W)** | 4, 12, 26, 52 weeks | Impact of window size on memory and update cost |
| **Distinct keywords (M)** | 5, 10, 25, 50, 100 | Hash map size impact |
| **K (Top-K)** | 3, 5, 10, 25, 50 | Heap size impact on Top-K selection |
| **Burst threshold** | 1.5, 2.0, 3.0, 5.0 | Sensitivity of burst detection |

### 8.2 Dependent Variables (What to Measure)

| Metric | How to Measure |
|---|---|
| **Wall-clock runtime** | `time.perf_counter()` before/after |
| **Memory usage** | `tracemalloc` (Python's built-in memory profiler) |
| **Number of operations** | Instrument code with counters for comparisons, hash ops |
| **Accuracy** | On synthetic data with known ground truth |

### 8.3 Experiment Matrix

#### Experiment 1: Sliding Window — Incremental vs Baseline
- Fix: M=10 keywords, W=12 weeks, K=5
- Vary: N = {1K, 5K, 10K, 50K, 100K, 500K}
- Measure: Runtime of incremental vs full recomputation
- Expected: Incremental is O(1) amortized per event; baseline is O(N) per query

#### Experiment 2: Top-K — Heap vs Sort
- Fix: N=50K events, W=12 weeks
- Vary: M = {10, 25, 50, 100} and K = {3, 5, 10, 25, 50}
- Measure: Runtime of heap-based vs sort-based Top-K
- Expected: Heap wins when K << M; sort catches up when K ≈ M

#### Experiment 3: Burst Detection Sensitivity
- Fix: N=50K events, W=12 weeks, K=5
- Vary: B_thresh = {1.5, 2.0, 3.0, 5.0}
- Measure: Number of bursts detected, false positive rate (on synthetic data)
- Compare: Ratio-based vs difference-based scoring

#### Experiment 4: End-to-End Pipeline Scalability
- Vary: N = {1K, 10K, 100K, 500K}
- Measure: Total pipeline runtime (all modules)
- Compare: Optimized pipeline vs naive pipeline

### 8.4 Visualization Plan

| Plot | Type | Axes |
|---|---|---|
| Incremental vs Baseline runtime | Line chart | X: stream size, Y: time (ms) |
| Heap vs Sort for Top-K | Grouped bar chart | X: (M, K) combinations, Y: time (ms) |
| Memory usage by window size | Line chart | X: window size, Y: memory (MB) |
| Burst detection ROC-like curve | Line chart | X: threshold, Y: detection count |
| End-to-end scalability | Log-log line chart | X: N, Y: total time |

---

## 9. Work Distribution — Parallel Development Plan

### 9.1 The Core Question: Can We Work Simultaneously?

**Yes — with one condition:** the team must agree on interface contracts (Section 10) in Week 1 before splitting up. Once interfaces are defined, each module can be developed and tested independently using mock data.

### 9.2 Member Assignments

#### Bhoomika Panday — Module A: Data Ingestion & Sliding Window Engine

| Task | Deliverable |
|---|---|
| Stream simulator | `stream_simulator.py` — loads CSV/synthetic data, emits events |
| Sliding window (incremental) | `sliding_window.py` — deque + hash map implementation |
| Sliding window (baseline) | `baseline_recompute.py` — naive full-scan for comparison |
| Expiration logic | Part of `sliding_window.py` |
| Unit tests | `tests/test_sliding_window.py` |
| Amortized analysis writeup | Section in final report |

**Can work independently from Day 1** — no dependency on other modules.

#### Vasudha Jain — Module B: Ranking, Burst Detection & Classification

| Task | Deliverable |
|---|---|
| Top-K selection (heap) | `top_k.py` — min-heap Top-K |
| Top-K selection (sort baseline) | Same file, different function |
| Burst detection | `burst_detection.py` — ratio + difference scoring |
| Cosine similarity | `cycle_detection.py` — vector comparison |
| Rule-based classifier | `trend_classifier.py` — decision tree logic |
| Peak detection | `peak_detection.py` — local maxima scan |
| Unit tests | `tests/test_ranking.py`, `tests/test_burst.py`, `tests/test_classifier.py` |
| Complexity analysis writeup | Section in final report |

**Can work independently from Day 1** — use mock frequency maps (just Python dicts) to develop and test all algorithms without needing the actual sliding window.

#### Parvathi Gottumukkala — Module C: Accessibility, Experiments & Analysis

| Task | Deliverable |
|---|---|
| Accessibility scoring | `accessibility.py` — weighted multi-criteria scoring |
| Accessibility data curation | `data/accessibility_db.json` — manual dataset |
| Scalability experiments | `experiments/run_experiments.py` — benchmarking harness |
| Visualization | `experiments/plot_results.py` — matplotlib charts |
| Synthetic data generator | `data/generate_synthetic.py` — edge-case patterns |
| Integration & main pipeline | `main.py` — connects all modules |
| Final report | `report/` — LaTeX/doc compilation |

**Can work independently from Day 1** — accessibility scoring uses mock trend data; experiments use mock algorithms initially, real ones after integration.

### 9.3 Dependency Diagram

```
Week 1: All three work independently (using mocks)
         ┌──────────┐  ┌──────────┐  ┌──────────┐
         │ Bhoomika  │  │ Vasudha  │  │ Parvathi │
         │ Window    │  │ Ranking  │  │ Scoring  │
         │ Engine    │  │ + Burst  │  │ + Expts  │
         └────┬─────┘  └────┬─────┘  └────┬─────┘
              │              │              │
Week 3-4:    └──────────────┼──────────────┘
              INTEGRATION POINT
              (plug real modules into pipeline)
```

### 9.4 How Mocks Enable Parallel Work

Each person creates a simple mock of the OTHER modules' output to develop against:

**Bhoomika's mock (for Vasudha and Parvathi to use):**
```python
def mock_freq_map():
    return {"wide-leg jeans": 78, "cargo pants": 45, "skinny jeans": 12, "Y2K": 92}
```

**Vasudha's mock (for Parvathi to use):**
```python
def mock_classified_trends():
    return [
        {"keyword": "Y2K", "label": "New", "burst_score": 4.2, "frequency": 92},
        {"keyword": "cargo pants", "label": "Cyclical", "burst_score": 1.8, "frequency": 45},
    ]
```

**Parvathi's mock (for testing her own module):**
```python
def mock_accessibility_db():
    return {"wide-leg jeans": {"wheelchair_friendly": 1, "adaptive_wearability": 4, ...}}
```

---

## 10. Interface Contracts (Enabling Parallel Work)

These are the exact function signatures each module must implement. **Agree on these in Week 1 — they are the contract that allows independent development.**

### 10.1 Module A Interfaces (Bhoomika)

```python
# sliding_window.py

class SlidingWindowEngine:
    def __init__(self, window_size: int):
        """Initialize with window size (in time units)."""
        pass

    def process_event(self, timestamp: int, keyword: str) -> dict[str, int]:
        """
        Process a single event. Returns current frequency map.
        Returns: {keyword: count} for all keywords in the current window.
        """
        pass

    def get_current_frequencies(self) -> dict[str, int]:
        """Return the current frequency map without processing a new event."""
        pass

    def get_window_size(self) -> int:
        """Return the number of events currently in the window."""
        pass


# baseline_recompute.py

def recompute_frequencies(events: list[tuple], current_time: int, window_size: int) -> dict[str, int]:
    """
    Baseline: scan all events and count those within the window.
    events: list of (timestamp, keyword) tuples.
    Returns: {keyword: count}
    """
    pass


# stream_simulator.py

def load_google_trends_csv(filepath: str) -> list[tuple[int, str]]:
    """
    Load a Google Trends CSV and convert to event stream.
    Returns: sorted list of (timestamp, keyword) events.
    """
    pass

def generate_synthetic_stream(pattern: str, n_events: int) -> list[tuple[int, str]]:
    """
    Generate synthetic event stream for testing.
    pattern: one of "burst", "gradual", "cyclical", "seasonal", "fading", "flat"
    Returns: sorted list of (timestamp, keyword) events.
    """
    pass
```

### 10.2 Module B Interfaces (Vasudha)

```python
# top_k.py

def top_k_heap(freq_map: dict[str, int], k: int) -> list[tuple[str, int]]:
    """
    Return Top-K items by frequency using a min-heap.
    Returns: [(keyword, count), ...] sorted descending by count.
    """
    pass

def top_k_sort(freq_map: dict[str, int], k: int) -> list[tuple[str, int]]:
    """
    Baseline: Return Top-K items by full sorting.
    Returns: [(keyword, count), ...] sorted descending by count.
    """
    pass


# burst_detection.py

def detect_bursts(
    current_freq: dict[str, int],
    previous_freq: dict[str, int],
    k: int,
    threshold: float = 2.0,
    method: str = "ratio"     # "ratio" or "difference"
) -> list[tuple[str, float]]:
    """
    Detect Top-K bursting keywords.
    Returns: [(keyword, burst_score), ...] sorted descending.
    """
    pass


# cycle_detection.py

def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors. Returns float in [0, 1]."""
    pass

def find_best_match(
    current_vector: list[float],
    historical_db: dict[str, list[float]]
) -> tuple[str, float]:
    """
    Find the historical pattern most similar to the current vector.
    Returns: (best_matching_keyword, similarity_score)
    """
    pass


# trend_classifier.py

def classify_trend(
    keyword: str,
    burst_score: float,
    cosine_sim: float,
    freq_trajectory: list[int],
    cyclical_threshold: float = 0.75,
    burst_threshold: float = 2.0,
    decline_threshold: float = -0.3
) -> str:
    """
    Classify a trend as "New", "Cyclical", "Seasonal", or "Fading".
    Returns: classification label string.
    """
    pass


# peak_detection.py

def find_peaks(freq_series: list[int], neighborhood: int = 1) -> list[tuple[int, int]]:
    """
    Find local maxima in a frequency time series.
    Returns: [(index, value), ...] for each peak found.
    """
    pass
```

### 10.3 Module C Interfaces (Parvathi)

```python
# accessibility.py

def compute_accessibility_score(
    keyword: str,
    accessibility_db: dict,
    weights: dict[str, float] = None    # uses defaults if None
) -> tuple[float, str]:
    """
    Compute weighted accessibility score for a keyword.
    Returns: (score_0_to_1, label) where label is "Highly Accessible", etc.
    """
    pass

def rank_by_accessibility(
    trends: list[dict],
    accessibility_db: dict,
    k: int,
    weights: dict[str, float] = None
) -> tuple[list, list[str]]:
    """
    Rank trends by accessibility score. Flag low-accessibility items.
    Returns: (ranked_trends, alert_keywords)
    """
    pass


# experiments/run_experiments.py

def benchmark_sliding_window(stream_sizes: list[int], window_size: int) -> dict:
    """Run incremental vs baseline comparison across stream sizes."""
    pass

def benchmark_top_k(m_values: list[int], k_values: list[int]) -> dict:
    """Run heap vs sort comparison across M and K combinations."""
    pass

def benchmark_end_to_end(stream_sizes: list[int]) -> dict:
    """Run full pipeline benchmark."""
    pass


# main.py

def run_pipeline(
    data_source: str,          # path to CSV or "synthetic"
    window_size: int = 12,
    k: int = 5,
    burst_threshold: float = 2.0,
    cyclical_threshold: float = 0.75
) -> None:
    """Run the complete detection pipeline and print results."""
    pass
```

---

## 11. Week-by-Week Execution Plan

### Week 1 (March 18 – March 24): Setup & Parallel Start

| Person | Tasks | Deliverable |
|---|---|---|
| **ALL** | Agree on interface contracts (Section 10) | Signed-off interfaces |
| **ALL** | Set up shared repo, folder structure, virtual env | Working repo |
| **Bhoomika** | Implement stream simulator (CSV + synthetic) | `stream_simulator.py` |
| **Bhoomika** | Implement baseline full recomputation | `baseline_recompute.py` |
| **Vasudha** | Implement heap-based Top-K + sort baseline | `top_k.py` |
| **Vasudha** | Write unit tests for Top-K with mock data | `tests/test_top_k.py` |
| **Parvathi** | Download Google Trends CSVs (8-10 keywords) | `data/google_trends/` |
| **Parvathi** | Create accessibility lookup table | `data/accessibility_db.json` |
| **Parvathi** | Implement synthetic data generator | `data/generate_synthetic.py` |

### Week 2 (March 25 – March 31): Core Algorithms

| Person | Tasks | Deliverable |
|---|---|---|
| **Bhoomika** | Implement incremental sliding window | `sliding_window.py` |
| **Bhoomika** | Unit tests (correctness vs baseline) | `tests/test_sliding_window.py` |
| **Vasudha** | Implement burst detection (ratio + difference) | `burst_detection.py` |
| **Vasudha** | Implement cosine similarity + cycle matching | `cycle_detection.py` |
| **Parvathi** | Implement accessibility scoring algorithm | `accessibility.py` |
| **Parvathi** | Begin experiment harness skeleton | `experiments/run_experiments.py` |

### Week 3 (April 1 – April 7): Classification & Integration Prep

| Person | Tasks | Deliverable |
|---|---|---|
| **Bhoomika** | Polish and optimize sliding window | Updated `sliding_window.py` |
| **Bhoomika** | Write amortized analysis section | Report section |
| **Vasudha** | Implement rule-based trend classifier | `trend_classifier.py` |
| **Vasudha** | Implement peak detection | `peak_detection.py` |
| **Vasudha** | Write complexity analysis section | Report section |
| **Parvathi** | Complete accessibility scoring + ranking | Updated `accessibility.py` |
| **ALL** | **Integration point**: plug real modules together | `main.py` working end-to-end |

### Week 4 (April 8 – April 14): Experiments & Benchmarking

| Person | Tasks | Deliverable |
|---|---|---|
| **Bhoomika** | Run sliding window experiments (incremental vs baseline) | Experiment data + plots |
| **Vasudha** | Run Top-K experiments (heap vs sort) | Experiment data + plots |
| **Vasudha** | Run burst detection sensitivity experiments | Experiment data + plots |
| **Parvathi** | Run end-to-end scalability experiments | Experiment data + plots |
| **Parvathi** | Run memory profiling experiments | Experiment data + plots |
| **ALL** | Debug integration issues found during experiments | Fixes |

### Week 5 (April 15 – April 21): Report & Presentation

| Person | Tasks | Deliverable |
|---|---|---|
| **Bhoomika** | Write Module A section of report | Report sections 1-3 |
| **Vasudha** | Write Module B section of report | Report sections 4-7 |
| **Parvathi** | Write Module C + experiments section | Report sections 8-10 |
| **ALL** | Create presentation slides | Slide deck |
| **ALL** | Practice presentation, prepare demo | Demo script |
| **ALL** | Final code cleanup, comments, README | Clean repo |

---

## 12. Edge Cases and Correctness

### 12.1 Edge Case Catalog

| # | Edge Case | Affected Module | Handling Strategy |
|---|---|---|---|
| 1 | **Empty window** (no events in time range) | Sliding Window | Return empty `freq_map = {}`. Top-K returns empty list. |
| 2 | **Single event in window** | All | Works normally. Top-1 returns that single item. |
| 3 | **Tie in Top-K** (multiple items with same frequency) | Top-K | Break ties alphabetically for deterministic output. Document this choice. |
| 4 | **K > M** (asking for more Top-K than distinct items) | Top-K | Return all M items. `min(K, M)` elements in heap. |
| 5 | **K = 0** | Top-K | Return empty list immediately. |
| 6 | **Zero denominator in burst ratio** (prev_freq = 0) | Burst Detection | Use `current_freq` as the burst score (new item = burst). |
| 7 | **Division by zero in cosine sim** (zero vector) | Cycle Detection | Return 0.0 similarity. A zero vector means no data = no pattern. |
| 8 | **All items same frequency** | Top-K | All are "tied for Top-K." Return any K (with alphabetical tiebreak). |
| 9 | **Keyword not in accessibility DB** | Accessibility | Return score 0.0 and flag as "NO_DATA" in alerts. |
| 10 | **Very short time series** (< 2 points) | Classification | Cannot compute slope. Return "New" by default. |
| 11 | **Negative burst score** (frequency decreased) | Burst Detection | Score < 1.0 means decline. Only surface items with score ≥ threshold. |
| 12 | **All events have same timestamp** | Sliding Window | All in same window. Deque processes them normally. |

### 12.2 Correctness Verification Approach

For each algorithm, verify correctness by:
1. **Hand-computed examples**: Create a small input, compute expected output by hand, assert match
2. **Baseline comparison**: Incremental sliding window must produce the SAME `freq_map` as full recomputation
3. **Property testing**: Heap Top-K must return the same SET as Sort Top-K (order may differ within ties)
4. **Invariant checking**: After every `process_event`, assert the sliding window invariant holds

---

## 13. Testing Strategy

### 13.1 Unit Tests (Per Module)

#### Module A Tests
```
test_empty_stream()               → freq_map should be {}
test_single_event()               → freq_map should be {keyword: 1}
test_window_expiration()          → events outside window are removed
test_incremental_matches_baseline() → both produce identical freq_maps
test_zero_count_cleanup()         → keywords at count 0 are removed from map
```

#### Module B Tests
```
test_top_k_basic()                → known freq_map → known Top-K
test_top_k_with_ties()            → deterministic tie-breaking
test_top_k_exceeds_items()        → K > M returns all items
test_heap_matches_sort()          → both methods return same set
test_burst_new_keyword()          → new keyword gets burst score = freq
test_burst_ratio_vs_diff()        → both methods produce expected scores
test_cosine_identical_vectors()   → similarity = 1.0
test_cosine_orthogonal_vectors()  → similarity = 0.0
test_cosine_zero_vector()         → similarity = 0.0 (no crash)
test_classify_fading_trend()      → declining trajectory → "Fading"
test_classify_new_trend()         → high burst, low similarity → "New"
test_classify_cyclical_trend()    → high similarity → "Cyclical"
test_peak_detection_simple()      → [1,3,1] → peak at index 1
test_peak_detection_plateau()     → [1,3,3,1] → no peaks (equal values)
```

#### Module C Tests
```
test_accessibility_score_range()  → score is always in [0.0, 1.0]
test_accessibility_all_max()      → perfect scores → 1.0
test_accessibility_all_min()      → lowest scores → 0.0
test_missing_keyword()            → returns 0.0 + "NO_DATA" alert
test_custom_weights()             → different weights → different scores
test_ranking_order()              → highest score first
```

### 13.2 Integration Tests
```
test_full_pipeline_synthetic_burst()    → synthetic burst data → detects burst correctly
test_full_pipeline_synthetic_cyclical() → synthetic cyclical data → classifies as cyclical
test_full_pipeline_google_trends()      → real CSV data → produces valid output
```

---

## 14. Expected Deliverables

### 14.1 Code

```
Project/
├── main.py                          # Entry point — runs full pipeline
├── sliding_window.py                # Module A: incremental sliding window
├── baseline_recompute.py            # Module A: baseline for comparison
├── stream_simulator.py              # Module A: CSV loader + stream simulator
├── top_k.py                         # Module B: heap-based + sort-based Top-K
├── burst_detection.py               # Module B: burst scoring algorithms
├── cycle_detection.py               # Module B: cosine similarity + matching
├── trend_classifier.py              # Module B: rule-based classification
├── peak_detection.py                # Module B: local maxima detection
├── accessibility.py                 # Module C: weighted scoring + ranking
├── config.py                        # Shared constants and thresholds
├── data/
│   ├── google_trends/               # Downloaded Google Trends CSVs
│   │   ├── wide_leg_jeans.csv
│   │   ├── cargo_pants.csv
│   │   └── ...
│   ├── accessibility_db.json        # Hand-curated accessibility scores
│   └── generate_synthetic.py        # Synthetic data generator
├── tests/
│   ├── test_sliding_window.py
│   ├── test_top_k.py
│   ├── test_burst.py
│   ├── test_cycle.py
│   ├── test_classifier.py
│   ├── test_accessibility.py
│   └── test_integration.py
├── experiments/
│   ├── run_experiments.py           # Benchmarking harness
│   └── plot_results.py              # Visualization
├── report/                          # Final report (LaTeX/PDF)
├── slides/                          # Presentation slides
├── requirements.txt                 # Python dependencies
└── README.md                        # How to run
```

### 14.2 Report Sections

1. Introduction & Problem Statement
2. System Architecture
3. Algorithm Design & Pseudocode
4. Complexity Analysis (Theoretical)
5. Implementation Details
6. Experimental Results (with plots)
7. Edge Cases & Correctness
8. Discussion: Theoretical vs Empirical Performance
9. Accessibility Feature & Social Impact
10. Conclusion & Future Work

### 14.3 Visualizations to Produce

| # | Plot | Purpose |
|---|---|---|
| 1 | Incremental vs Baseline runtime (line chart) | Proves O(1) amortized vs O(N) |
| 2 | Heap vs Sort Top-K runtime (grouped bar) | Proves O(M log K) vs O(M log M) |
| 3 | Memory usage by window size (line chart) | Shows space-time tradeoff |
| 4 | Burst detection: threshold vs detections (line) | Sensitivity analysis |
| 5 | Trend lifecycle visualization (timeline plot) | Shows classified trends over time |
| 6 | Accessibility score distribution (bar chart) | Shows scoring output |
| 7 | End-to-end pipeline scalability (log-log) | Overall system performance |

### 14.4 Dependencies (requirements.txt)

```
matplotlib>=3.7
pytest>=7.0
```

That's it. No heavy libraries. Only Python standard library + matplotlib for plots + pytest for testing. This reinforces the "pure algorithms, no ML" claim.

---

## 15. Course Topic Mapping

This section maps every algorithm/data structure in the project to the relevant CS5800 course topic for the report.

| Course Topic | Project Component | Where It Appears | Complexity |
|---|---|---|---|
| **Hash Tables** | Frequency counting | `sliding_window.py` — `freq_map` dict | O(1) avg insert/lookup/delete |
| **Queues / Deques** | Sliding window event storage | `sliding_window.py` — `event_queue` deque | O(1) append/popleft |
| **Priority Queues / Heaps** | Top-K selection | `top_k.py` — min-heap of size K | O(M log K) for M items |
| **Sorting** | Baseline Top-K comparison | `top_k.py` — full sort approach | O(M log M) |
| **Amortized Analysis** | Sliding window updates | Each event enters/exits deque exactly once | O(1) amortized per event |
| **Divide & Conquer** (if applicable) | Merge-sort used in baseline | `top_k.py` — Python's Timsort | O(M log M) |
| **Greedy** | Top-K heap maintenance | Always keep the K largest seen so far | Greedy choice: evict minimum |
| **Algorithm Design** | Burst detection, cycle detection, trend classification | `burst_detection.py`, `cycle_detection.py`, `trend_classifier.py` | Various (see Section 6) |
| **Complexity Analysis** | Theoretical + empirical for all components | Full report + experiments | Compared across all approaches |

---

## 16. Risk Register

| # | Risk | Impact | Probability | Mitigation |
|---|---|---|---|---|
| 1 | Google Trends data is too sparse for some keywords | Some trends have mostly zeros | Medium | Supplement with synthetic data; choose popular keywords |
| 2 | Integration fails in Week 3-4 | Pipeline doesn't connect | Medium | Interface contracts defined in Week 1; integration tested with mocks early |
| 3 | Cosine similarity gives meaningless results on short vectors | All similarities ≈ 0 or ≈ 1 | Medium | Use minimum vector length of 10; pad shorter vectors; test with synthetic data first |
| 4 | Accessibility data is too subjective | Scores feel arbitrary | Low | Document scoring criteria clearly; acknowledge subjectivity in report |
| 5 | One team member falls behind | Module not ready for integration | Medium | Weekly check-ins; mocks allow others to continue; clearly scoped tasks |
| 6 | Experiments don't show expected speedup | Heap isn't faster than sort for small M | Low | Use large enough M values (100+); document and explain when they converge |
| 7 | Report/slides take longer than expected | Rushed final week | High | Start writing report sections as each module completes (Weeks 2-3) |

---

## Quick-Start Checklist

- [ ] All three members read and agree on this document
- [ ] Create shared Git repository
- [ ] Set up Python virtual environment (`python -m venv venv`)
- [ ] Install dependencies (`pip install matplotlib pytest`)
- [ ] Download Google Trends CSVs for 8-10 fashion keywords
- [ ] Create `data/accessibility_db.json` (even a partial version)
- [ ] Each person implements their mock functions first
- [ ] Each person writes unit tests alongside their code
- [ ] Schedule weekly 30-min sync meetings (e.g., every Monday)

---

*Document generated on 2026-03-18 for CS5800 — Algorithms, Northeastern University, Spring 2026*
