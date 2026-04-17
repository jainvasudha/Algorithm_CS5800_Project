# Execution Plan — 4 Weeks, 3 People, Zero Fluff

## CS5800: Real-Time Fashion Trend Detection System

> **Team:** Bhoomika, Vasudha, Parvathi
> **Deadline:** ~April 18, 2026 (4 weeks from March 18)
> **Philosophy:** Depth over breadth. 3 algorithms done properly beats 7 done halfway.

---

## What Actually Impresses a CS5800 Professor

**These things score marks:**
1. Formal problem definition with mathematical notation
2. Pseudocode for each algorithm (not just Python code)
3. Complexity analysis — theoretical (Big-O proof) AND empirical (plots)
4. Baseline vs Optimized comparison with clear experiment results
5. Correctness argument (invariants, hand-traced examples)
6. Clean plots showing theory matches practice

**These things do NOT score marks (and waste your time):**
- Feature bloat (adding more algorithms you can't explain deeply)
- Fancy UI or excessive visualization beyond what's needed
- "Social impact" features that have zero algorithmic content
- Over-engineering code with abstractions you don't need

---

## Architecture — Trimmed and Focused

### What We Keep (High Algorithmic Value)

| # | Component | Why It's Gold | Course Topic It Hits |
|---|---|---|---|
| 1 | **Sliding Window** (incremental vs naive recomputation) | Amortized O(1) vs O(N) — the most dramatic speedup in the project | Hash Tables, Deques, Amortized Analysis |
| 2 | **Top-K Selection** (min-heap vs full sort) | O(M log K) vs O(M log M) — classic heap application | Priority Queues, Heaps, Sorting |
| 3 | **Burst Detection** (two scoring variants) | Algorithm design — ratio vs difference, threshold tuning | Algorithm Design, Complexity Analysis |
| 4 | **Cycle Classification** (cosine similarity) | Applied algorithm — dot product, vector comparison | Algorithm Design |

### What We Simplify

| Component | Old Plan | New Plan | Why |
|---|---|---|---|
| **Accessibility Scoring** | Full module with weighted multi-criteria, normalization, heap ranking | Simple lookup table + weighted sum. 30 lines of code, not a module. | It's a weighted average — there's no real algorithm here. Keep it as a feature, not a selling point. |
| **Peak Detection** | Separate algorithm with neighborhood parameter | Fold into burst detection — peaks are just windows where burst score is high | Redundant. Burst detection already finds spikes. |
| **Trend Classifier** | Complex rule-based system with 4 thresholds | Simple 4-rule if/else based on cosine similarity + burst score | Don't overthink it — the classification rules are the OUTPUT, not the interesting algorithm. The interesting part is cosine similarity. |

### Simplified Pipeline

```
CSV Data → Stream Simulator → [Sliding Window] → freq_map
                                                      │
                                    ┌─────────────────┼─────────────────┐
                                    ▼                 ▼                 ▼
                              [Top-K Heap]    [Burst Detection]  [Cosine Sim]
                                    │                 │                 │
                                    ▼                 ▼                 ▼
                              top K trends      bursting items    trend labels
                                    │                 │                 │
                                    └────────┬────────┘                 │
                                             ▼                         │
                                    Combined Results ◄─────────────────┘
                                             │
                                    + accessibility score (simple lookup)
                                             │
                                             ▼
                                       Final Output
```

**Total files needed: 8 Python files + 1 data file + tests. That's it.**

---

## The 3 "Money Shot" Comparisons

These are the 3 experiments that will be the centerpiece of your report and presentation. Each one follows the same pattern:

### Money Shot 1: Sliding Window — Incremental vs Naive

```
WHAT:    Process N events, query frequency after each one
NAIVE:   Scan ALL events within window every time → O(N) per query
SMART:   Maintain deque + hash map, update incrementally → O(1) amortized

EXPERIMENT:
  - Fix: 10 keywords, window = 12 weeks
  - Vary: N = 1,000 → 5,000 → 10,000 → 50,000 → 100,000
  - Measure: Wall-clock time for processing all N events
  - Plot: X = stream size, Y = total time (seconds)

EXPECTED RESULT:
  - Naive: line goes up steeply (linear or worse)
  - Smart: line stays nearly flat (constant per event)
  - THIS IS YOUR BEST PLOT. It will be dramatic.
```

### Money Shot 2: Top-K — Heap vs Sort

```
WHAT:    Given a freq_map of M items, find the K largest
NAIVE:   Sort all M items, take first K → O(M log M)
SMART:   Min-heap of size K, scan once → O(M log K)

EXPERIMENT:
  - Fix: K = 5
  - Vary: M = 50, 100, 500, 1000, 5000
  - Measure: Time to extract Top-K
  - Also: Fix M = 1000, vary K = 5, 10, 50, 100, 500 (shows convergence)
  - Plot: Line chart with two lines (heap vs sort)

EXPECTED RESULT:
  - Sort: grows with M regardless of K
  - Heap: grows slower, advantage bigger when K << M
  - When K approaches M: they converge (document this — shows understanding)
```

### Money Shot 3: Burst Detection — Ratio vs Difference

```
WHAT:    Compare two scoring methods for detecting sudden spikes
RATIO:   burst = current_freq / prev_freq (captures multiplicative growth)
DIFF:    burst = current_freq - prev_freq (captures absolute growth)

EXPERIMENT:
  - Use SYNTHETIC data with known ground-truth bursts
  - Inject: 5 true bursts of varying magnitudes
  - Vary: threshold from 1.5 to 10.0
  - Measure: For each threshold — how many true bursts detected, how many false positives
  - Plot: Threshold vs Detection Rate for both methods

EXPECTED RESULT:
  - Ratio: better at catching small-absolute but high-relative spikes (e.g., 2→10)
  - Difference: better at catching large-absolute spikes (e.g., 500→600)
  - DISCUSS which is more appropriate for fashion trends (and why)
```

---

## Work Distribution — Who Does What

### Can You Work Simultaneously? YES.

Here's why: **each module takes a Python dict as input and returns a Python dict/list as output.** You don't need the other person's code to develop — you just need a sample dict.

```python
# This is ALL Vasudha needs from Bhoomika to start working:
sample_freq_map = {"wide-leg jeans": 78, "cargo pants": 45, "skinny jeans": 12}

# This is ALL Parvathi needs from Vasudha to start experiments:
sample_classified = [("Y2K", 92, "New", 4.2), ("cargo pants", 45, "Cyclical", 1.1)]
```

Agree on these dict shapes on Day 1. Then go work independently.

### Bhoomika — The Engine Builder

**Owns:** Everything that touches raw data and the sliding window.

| File | What It Does |
|---|---|
| `stream_simulator.py` | Loads Google Trends CSV → emits `(timestamp, keyword)` events |
| `sliding_window.py` | Incremental: deque + hash map. Returns `freq_map: dict[str, int]` |
| `baseline.py` | Naive: full scan each time. Same output format. For comparison. |
| `tests/test_window.py` | Unit tests: empty stream, expiration, correctness vs baseline |

**Report sections:** Problem statement, sliding window pseudocode + amortized analysis, Experiment 1 writeup + plot.

**This is the most critical module.** If the sliding window works and the experiment plot is clean, the project already passes. Bhoomika should be done with core code by end of Week 2.

### Vasudha — The Algorithm Designer

**Owns:** Everything that analyzes the frequency map.

| File | What It Does |
|---|---|
| `top_k.py` | `top_k_heap(freq_map, k)` and `top_k_sort(freq_map, k)` |
| `burst_detection.py` | `detect_bursts(current, previous, k, threshold, method)` |
| `cycle_detection.py` | Cosine similarity + `classify_trend()` (simple 4-rule classifier) |
| `tests/test_ranking.py` | Tests for Top-K, burst detection, cosine similarity, classifier |

**Report sections:** Top-K pseudocode + complexity proof, burst detection design + scoring comparison, cycle classification, Experiments 2 & 3 writeup + plots.

**This is the most algorithm-heavy module.** Vasudha should focus on getting the pseudocode and complexity proofs right — these are what the professor reads.

### Parvathi — The Integrator & Experimenter

**Owns:** Gluing everything together, running experiments, making plots, writing the report.

| File | What It Does |
|---|---|
| `main.py` | Connects all modules into one pipeline. The entry point. |
| `accessibility.py` | Simple weighted lookup. ~40 lines. |
| `data/accessibility_db.json` | Hand-curated scores for ~30 fashion keywords |
| `data/generate_synthetic.py` | Creates synthetic streams (burst, cyclical, fading, etc.) |
| `experiments.py` | Benchmarking: `time.perf_counter()` + `tracemalloc` |
| `plots.py` | matplotlib charts for all 3 money-shot experiments |
| `tests/test_integration.py` | End-to-end tests with synthetic + real data |

**Report sections:** Experimental setup, all plots with analysis, integration, accessibility feature, conclusion.

**This role is underrated.** Clean plots with clear labels and insightful analysis (e.g., "the heap advantage diminishes as K approaches M, which matches theory") are what elevate a B+ project to an A.

---

## 4-Week Calendar

### Week 1 (Mar 18–24): Foundation — Everyone Works in Parallel

**Monday (Day 1) — 1-hour team meeting (mandatory):**
- [ ] Agree on this plan
- [ ] Set up shared Git repo (one person creates, others clone)
- [ ] Agree on interface: `freq_map` is always `dict[str, int]`
- [ ] Agree on data: download 8 Google Trends CSVs together
- [ ] Each person creates their files (empty functions with docstrings)

**Bhoomika (rest of Week 1):**
- [ ] `stream_simulator.py` — load CSV, emit events (this is straightforward)
- [ ] `baseline.py` — naive full-scan frequency counter
- [ ] Start `sliding_window.py` — get deque + hash map working
- [ ] Test: `sliding_window` output matches `baseline` output for same input

**Vasudha (rest of Week 1):**
- [ ] `top_k.py` — both heap and sort versions
- [ ] `tests/test_ranking.py` — verify heap and sort return same set
- [ ] Start `burst_detection.py` — ratio scoring first

**Parvathi (rest of Week 1):**
- [ ] Download 8-10 Google Trends CSVs → `data/google_trends/`
- [ ] Create `data/accessibility_db.json` (manually score ~30 keywords)
- [ ] `data/generate_synthetic.py` — patterns: burst, cyclical, fading, flat
- [ ] `experiments.py` skeleton — timing and memory measurement functions

**Week 1 Checkpoint (Sunday):** Everyone pushes code. Bhoomika's window works. Vasudha's Top-K works. Parvathi has data ready.

---

### Week 2 (Mar 25–31): Core Algorithms Complete

**Bhoomika:**
- [ ] Finish and polish `sliding_window.py`
- [ ] Write comprehensive `tests/test_window.py`
- [ ] Verify: incremental output == baseline output on ALL test cases
- [ ] Start writing: pseudocode + amortized analysis for the report

**Vasudha:**
- [ ] Finish `burst_detection.py` — both ratio and difference methods
- [ ] `cycle_detection.py` — cosine similarity + classify_trend()
- [ ] Write `tests/test_burst.py` and `tests/test_cycle.py`
- [ ] Start writing: pseudocode + complexity proofs for the report

**Parvathi:**
- [ ] `accessibility.py` — weighted scoring (simple, ~40 lines)
- [ ] Start `main.py` — wire up Module A and Module B using mock data first
- [ ] Run first timing experiment with Bhoomika's sliding window code
- [ ] Start `plots.py` — get the matplotlib boilerplate ready

**Week 2 Checkpoint (Sunday):** All core algorithms implemented and tested individually. Report pseudocode sections drafted.

---

### Week 3 (Apr 1–7): Integration + Experiments

**ALL — Monday meeting:**
- [ ] Merge all code into `main.py`
- [ ] Run end-to-end with real Google Trends data
- [ ] Debug integration issues (expect 1-2 days of fixing)

**Bhoomika:**
- [ ] Run Experiment 1: Sliding window scalability (N = 1K to 100K)
- [ ] Generate Plot 1: incremental vs naive runtime
- [ ] Finalize amortized analysis writeup

**Vasudha:**
- [ ] Run Experiment 2: Top-K heap vs sort (vary M and K)
- [ ] Run Experiment 3: Burst detection ratio vs difference
- [ ] Generate Plots 2 and 3
- [ ] Finalize complexity analysis writeup

**Parvathi:**
- [ ] Run end-to-end benchmark (full pipeline at different scales)
- [ ] Generate remaining plots (memory usage, end-to-end scalability)
- [ ] Begin assembling full report (outline + completed sections)
- [ ] Test pipeline with synthetic edge cases

**Week 3 Checkpoint (Sunday):** Pipeline runs end-to-end. All 3 money-shot experiments complete with plots.

---

### Week 4 (Apr 8–14): Report + Presentation + Polish

**ALL — Monday meeting:**
- [ ] Review all experiment plots together
- [ ] Discuss: does theory match practice? Where doesn't it? Why?
- [ ] Divide report sections (see below)

**Report Writing Distribution:**

| Section | Owner | Content |
|---|---|---|
| 1. Introduction & Problem Statement | Bhoomika | Formal definition, motivation, scope |
| 2. System Architecture | Parvathi | Pipeline diagram, data flow |
| 3. Sliding Window Algorithm | Bhoomika | Pseudocode, amortized analysis, correctness invariant |
| 4. Top-K Selection Algorithm | Vasudha | Pseudocode, complexity proof (heap vs sort) |
| 5. Burst Detection Algorithm | Vasudha | Pseudocode, ratio vs difference analysis |
| 6. Cycle Classification | Vasudha | Cosine similarity, classifier rules |
| 7. Experimental Results | Parvathi | All plots, analysis, theory-vs-practice discussion |
| 8. Edge Cases & Correctness | Bhoomika | Edge case table, invariant proofs |
| 9. Accessibility Feature | Parvathi | Brief description, social impact angle |
| 10. Conclusion | ALL | What worked, what didn't, future work |

**Presentation (Thursday–Sunday):**
- [ ] Create slides (max 15 slides)
- [ ] Each person presents their section
- [ ] Prepare live demo (run `main.py` on real data, show output)
- [ ] Practice run-through at least once

**Week 4 Checkpoint (Friday):** Report done. Slides done. Demo works.

---

## Folder Structure (Final)

```
Project/
├── main.py                       # Entry point
├── stream_simulator.py           # Bhoomika — CSV + synthetic stream
├── sliding_window.py             # Bhoomika — incremental (deque + hash map)
├── baseline.py                   # Bhoomika — naive full-scan
├── top_k.py                      # Vasudha — heap + sort
├── burst_detection.py            # Vasudha — ratio + difference scoring
├── cycle_detection.py            # Vasudha — cosine sim + classifier
├── accessibility.py              # Parvathi — weighted lookup
├── experiments.py                # Parvathi — benchmarking harness
├── plots.py                      # Parvathi — matplotlib charts
├── config.py                     # Shared constants (window size, K, thresholds)
├── data/
│   ├── google_trends/            # Downloaded CSVs
│   ├── accessibility_db.json     # Hand-curated scores
│   └── generate_synthetic.py     # Synthetic data generator
├── tests/
│   ├── test_window.py
│   ├── test_ranking.py
│   ├── test_burst.py
│   ├── test_cycle.py
│   └── test_integration.py
├── report/                       # Final report (PDF)
├── slides/                       # Presentation
└── requirements.txt              # matplotlib, pytest — that's it
```

---

## Interface Contracts (Agree on Day 1)

These are the data shapes that flow between modules. Once agreed, each person codes independently.

```python
# ── MODULE A OUTPUT (Bhoomika → everyone) ──
freq_map = {"wide-leg jeans": 78, "cargo pants": 45, "skinny jeans": 12}
# Type: dict[str, int]  — keyword → count in current window

# ── MODULE B OUTPUTS (Vasudha → Parvathi) ──
top_k_result = [("wide-leg jeans", 78), ("cargo pants", 45), ("Y2K", 42)]
# Type: list[tuple[str, int]]  — sorted descending by count

burst_result = [("Y2K", 4.6), ("cargo pants", 2.1)]
# Type: list[tuple[str, float]]  — sorted descending by burst score

classification = {"Y2K": "New", "cargo pants": "Cyclical", "skinny jeans": "Fading"}
# Type: dict[str, str]  — keyword → label

# ── MODULE C OUTPUT (Parvathi → final output) ──
scored_trend = {"keyword": "wide-leg jeans", "freq": 78, "label": "Cyclical",
                "burst": 1.2, "accessibility": 0.82, "access_label": "Highly Accessible"}
# Type: dict  — all info combined per trend
```

**Rule: If you change a data shape, you tell the team IMMEDIATELY.** This is the one thing that can break parallel work.

---

## What Your Report Must Have (Checklist)

Every section should follow this pattern for EACH algorithm:

- [ ] **Problem statement** — what does this algorithm solve?
- [ ] **Pseudocode** — language-agnostic, with clear variable names
- [ ] **Time complexity** — Big-O with derivation (not just "it's O(n log k)")
- [ ] **Space complexity** — what's stored, how much memory
- [ ] **Correctness argument** — invariant or hand-traced example
- [ ] **Baseline comparison** — what's the naive alternative?
- [ ] **Experiment** — vary the right parameter, measure runtime
- [ ] **Plot** — clear axes labels, legend, title
- [ ] **Discussion** — does the plot match the theoretical prediction? Why or why not?

If you hit all 9 points for 3 algorithms, you're getting an A.

---

## Common Mistakes to Avoid

| Mistake | Why It Hurts | What To Do Instead |
|---|---|---|
| "We used a heap because it's efficient" | Professor wants to see WHY it's efficient — prove it | Show O(M log K) derivation step by step |
| Showing only the optimized version | No contrast = no story = boring | Always show naive baseline side-by-side |
| Tiny experiment inputs (N=100) | Can't see the asymptotic behavior | Go up to N=100K minimum. The curves need to separate. |
| Spaghetti code with everything in one file | Hard to grade, looks amateur | One algorithm per file. Clear function names. |
| Starting the report in Week 4 | Rushed, shallow, typos everywhere | Start pseudocode sections in Week 2. Plots in Week 3. Text in Week 4. |
| Skipping tests | "It works on my data" → breaks on edge cases during demo | Test with empty inputs, single items, ties, large inputs |
| Over-explaining accessibility | It's not the algorithmic core — don't pretend it is | 1 paragraph in report. Mention it shows social awareness. Move on. |

---

## Quick Reference: Google Trends Keywords to Download

Download these 8-10 as separate CSVs. Use "Worldwide" and "2004–present" for maximum history.

| Keyword | Expected Pattern | Tests |
|---|---|---|
| wide-leg jeans | Currently rising | Top-K frequency |
| skinny jeans | Was huge, now fading | "Fading" classification |
| cargo pants | Cyclical (2000s → now) | Cosine similarity detection |
| Y2K fashion | Sudden burst (2021+) | Burst detection |
| low-rise jeans | Controversial comeback | Seasonal/cyclical |
| mom jeans | Rose and plateaued | Stable trend |
| flared pants | Long cycle (~20 years) | Historical pattern matching |
| baggy jeans | Currently surging | Burst candidate |
| corset top | Fashion micro-trend | Short burst |
| oversized blazer | Steady rise | Gradual growth detection |

---

## Dependencies

```
# requirements.txt
matplotlib>=3.7
pytest>=7.0
```

Two packages. That's it. Everything else is Python standard library (`collections`, `heapq`, `math`, `time`, `tracemalloc`, `json`, `csv`).

---

## One Last Thing

The master document (`PROJECT_MASTER_DOCUMENT.md`) has all the detailed pseudocode, edge cases, and formal definitions. **Use it as a reference** while coding. This execution plan tells you **what to do and when**. The master document tells you **how each algorithm works**.

Don't try to memorize both. Bookmark them and refer as needed.

Now go set up the repo.
