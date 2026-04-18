"""
generate_synthetic.py — Synthetic Fashion-Trend Stream Generator (Parvathi / Shravya).

Produces labelled event streams with known ground-truth patterns so that
every algorithm can be tested against expected output.

Patterns supported:
  burst     — low background, then sudden spike then return to low
  gradual   — exponentially increasing frequency
  cyclical  — alternating high/low in a repeating pattern
  seasonal  — spike at fixed intervals (e.g. every 26 weeks)
  fading    — steadily declining frequency
  flat      — constant frequency throughout (should NOT trigger any detector)
  spike     — exactly one isolated high window (one-time anomaly)
  tie       — multiple keywords at the same frequency (tests tie-breaking)

Each pattern returns a sorted list of (timestamp, keyword) events suitable
for direct ingestion by SlidingWindowEngine.process_event().
"""

import random
from typing import List, Tuple


# ── Internal helpers ──────────────────────────────────────────────────────────

def _expand(schedule: List[Tuple[int, str, int]], seed: int = 42) -> List[Tuple[int, str]]:
    """
    Expand a schedule [(week, keyword, count), ...] into individual events.
    Events within the same week are shuffled so the stream appears realistic.
    """
    rng = random.Random(seed)
    out: List[Tuple[int, str]] = []
    for ts, kw, cnt in schedule:
        out.extend([(ts, kw)] * cnt)
    out.sort(key=lambda e: e[0])
    return out


# ── Public generators ─────────────────────────────────────────────────────────

def generate_burst(
    keyword: str = "Y2K fashion",
    n_weeks: int = 40,
    background: int = 2,
    spike_week: int = 20,
    spike_height: int = 50,
) -> List[Tuple[int, str]]:
    """
    Background noise up to spike_week, large spike, then return to background.
    Ground truth: burst detected at spike_week.
    """
    schedule = []
    for w in range(1, n_weeks + 1):
        cnt = spike_height if w == spike_week else background
        schedule.append((w, keyword, cnt))
    return _expand(schedule)


def generate_gradual(
    keyword: str = "wide-leg jeans",
    n_weeks: int = 40,
    start: int = 1,
    multiplier: float = 1.15,
) -> List[Tuple[int, str]]:
    """
    Exponentially growing popularity. Good for 'New' classification.
    """
    schedule = []
    cnt = start
    for w in range(1, n_weeks + 1):
        schedule.append((w, keyword, max(1, int(cnt))))
        cnt *= multiplier
    return _expand(schedule)


def generate_cyclical(
    keyword: str = "cargo pants",
    n_weeks: int = 52,
    low: int = 3,
    high: int = 45,
    period: int = 13,
) -> List[Tuple[int, str]]:
    """
    Alternates between high and low every `period` weeks.
    Ground truth: cosine similarity with historical half ≈ high.
    """
    schedule = []
    for w in range(1, n_weeks + 1):
        cnt = high if (w // period) % 2 == 0 else low
        schedule.append((w, keyword, cnt))
    return _expand(schedule)


def generate_seasonal(
    keyword: str = "winter boots",
    n_weeks: int = 104,
    base: int = 2,
    spike: int = 60,
    period: int = 26,
    spike_width: int = 3,
) -> List[Tuple[int, str]]:
    """
    Spike every `period` weeks (seasonal pattern).
    """
    schedule = []
    for w in range(1, n_weeks + 1):
        is_peak = (w % period) <= spike_width
        cnt = spike if is_peak else base
        schedule.append((w, keyword, cnt))
    return _expand(schedule)


def generate_fading(
    keyword: str = "skinny jeans",
    n_weeks: int = 40,
    start: int = 80,
    decrement: int = 2,
) -> List[Tuple[int, str]]:
    """
    Steadily declining popularity. Ground truth: 'Fading' classification.
    """
    schedule = []
    for w in range(1, n_weeks + 1):
        cnt = max(0, start - (w - 1) * decrement)
        if cnt > 0:
            schedule.append((w, keyword, cnt))
    return _expand(schedule)


def generate_flat(
    keyword: str = "mom jeans",
    n_weeks: int = 40,
    count: int = 20,
) -> List[Tuple[int, str]]:
    """
    Constant frequency — should NOT trigger burst or fading detectors.
    """
    schedule = [(w, keyword, count) for w in range(1, n_weeks + 1)]
    return _expand(schedule)


def generate_spike(
    keyword: str = "corset top",
    n_weeks: int = 40,
    spike_week: int = 15,
    spike_height: int = 80,
    background: int = 1,
) -> List[Tuple[int, str]]:
    """
    Single isolated peak — one-time anomaly.
    """
    return generate_burst(keyword, n_weeks, background, spike_week, spike_height)


def generate_tie_stream(
    keywords: List[str] = None,
    n_weeks: int = 10,
    count: int = 30,
) -> List[Tuple[int, str]]:
    """
    Multiple keywords with identical frequency — tests tie-breaking in Top-K.
    """
    if keywords is None:
        keywords = ["baggy jeans", "flared pants", "low-rise jeans"]
    schedule = []
    for w in range(1, n_weeks + 1):
        for kw in keywords:
            schedule.append((w, kw, count))
    return _expand(schedule)


def generate_mixed_stream(n_weeks: int = 52) -> List[Tuple[int, str]]:
    """
    Multi-keyword stream combining several patterns for realistic end-to-end testing.
    This is the default input for main.py when no CSV is provided.
    """
    all_events: List[Tuple[int, str]] = []
    all_events += generate_burst("Y2K fashion", n_weeks)
    all_events += generate_gradual("wide-leg jeans", n_weeks)
    all_events += generate_cyclical("cargo pants", n_weeks)
    all_events += generate_fading("skinny jeans", n_weeks)
    all_events += generate_flat("mom jeans", n_weeks)
    all_events += generate_seasonal("winter boots", n_weeks)
    all_events.sort(key=lambda e: e[0])
    return all_events


# ── Scalability helpers ────────────────────────────────────────────────────────

def generate_large_stream(
    n_events: int,
    n_keywords: int = 10,
    seed: int = 0,
    n_weeks: int = 52,
) -> List[Tuple[int, str]]:
    """
    Generate a large random stream for scalability benchmarks.
    Events are spread across n_weeks weekly timestamps so the pipeline
    processes at most n_weeks steps regardless of how large n_events is.
    This mirrors real Google Trends data (many events per week).
    """
    rng = random.Random(seed)
    keywords = [f"kw_{i}" for i in range(n_keywords)]
    out = []
    for i in range(n_events):
        week = (i % n_weeks) + 1
        out.append((week, rng.choice(keywords)))
    out.sort(key=lambda e: e[0])
    return out


if __name__ == "__main__":
    # Quick sanity check
    stream = generate_mixed_stream()
    print(f"Mixed stream: {len(stream)} events across "
          f"{len(set(e[1] for e in stream))} keywords, "
          f"weeks 1–{max(e[0] for e in stream)}")
