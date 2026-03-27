"""
generate_synthetic.py — Creates synthetic event streams for testing and experiments.

Patterns: burst, cyclical, fading, flat, growing
Also generates Google-Trends-style CSVs.
"""

import csv, math, os, random
from datetime import datetime, timedelta

random.seed(42)

DEFAULT_KEYWORDS = [
    "wide-leg jeans", "skinny jeans", "cargo pants", "Y2K fashion",
    "low-rise jeans", "mom jeans", "flared pants", "baggy jeans",
    "corset top", "oversized blazer",
]


def generate_burst_stream(keyword="Y2K fashion", n_events=500,
                          burst_start=0.7, burst_multiplier=5, base_rate=2):
    events = []
    total_seconds = n_events * 10
    for i in range(n_events):
        t = int(i * (total_seconds / n_events))
        frac = i / n_events
        rate = base_rate * burst_multiplier if frac >= burst_start else base_rate
        if random.random() < (rate / (base_rate * burst_multiplier)):
            events.append((t, keyword))
    return events


def generate_cyclical_stream(keyword="cargo pants", n_events=1000,
                             period_events=200, amplitude=0.4, base=0.5):
    events = []
    total_seconds = n_events * 10
    for i in range(n_events):
        t = int(i * (total_seconds / n_events))
        prob = base + amplitude * math.sin(2 * math.pi * i / period_events)
        if random.random() < prob:
            events.append((t, keyword))
    return events


def generate_fading_stream(keyword="skinny jeans", n_events=500,
                           start_prob=0.8, end_prob=0.05):
    events = []
    total_seconds = n_events * 10
    for i in range(n_events):
        t = int(i * (total_seconds / n_events))
        prob = start_prob + (end_prob - start_prob) * (i / n_events)
        if random.random() < prob:
            events.append((t, keyword))
    return events


def generate_flat_stream(keyword="mom jeans", n_events=500, prob=0.3):
    events = []
    total_seconds = n_events * 10
    for i in range(n_events):
        t = int(i * (total_seconds / n_events))
        if random.random() < prob:
            events.append((t, keyword))
    return events


def generate_growing_stream(keyword="oversized blazer", n_events=500,
                            start_prob=0.05, end_prob=0.7):
    events = []
    total_seconds = n_events * 10
    for i in range(n_events):
        t = int(i * (total_seconds / n_events))
        prob = start_prob + (end_prob - start_prob) * (i / n_events)
        if random.random() < prob:
            events.append((t, keyword))
    return events


def generate_mixed_stream(n_events_per_keyword=500):
    generators = [
        ("Y2K fashion", generate_burst_stream), ("cargo pants", generate_cyclical_stream),
        ("skinny jeans", generate_fading_stream), ("mom jeans", generate_flat_stream),
        ("oversized blazer", generate_growing_stream), ("wide-leg jeans", generate_growing_stream),
        ("baggy jeans", generate_burst_stream), ("corset top", generate_burst_stream),
        ("flared pants", generate_cyclical_stream), ("low-rise jeans", generate_fading_stream),
    ]
    all_events = []
    for keyword, gen_func in generators:
        all_events.extend(gen_func(keyword=keyword, n_events=n_events_per_keyword))
    all_events.sort(key=lambda e: e[0])
    return all_events


def generate_scalable_stream(n_events, n_keywords=10):
    keywords = DEFAULT_KEYWORDS[:n_keywords]
    return [(i, random.choice(keywords)) for i in range(n_events)]


def generate_burst_experiment_data(n_keywords=20, n_true_bursts=5,
                                   base_range=(5, 30), burst_range=(50, 200)):
    keywords = [f"trend_{i}" for i in range(n_keywords)]
    burst_keywords = set(random.sample(keywords, n_true_bursts))
    previous_freq, current_freq = {}, {}
    for kw in keywords:
        prev_count = random.randint(*base_range)
        previous_freq[kw] = prev_count
        if kw in burst_keywords:
            current_freq[kw] = random.randint(*burst_range)
        else:
            current_freq[kw] = max(1, prev_count + random.randint(-5, 5))
    return previous_freq, current_freq, burst_keywords


def generate_google_trends_csv(keyword, pattern="burst", weeks=260, output_dir=None):
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "google_trends")
    os.makedirs(output_dir, exist_ok=True)
    start_date = datetime(2019, 1, 6)
    rows = []
    for w in range(weeks):
        date = start_date + timedelta(weeks=w)
        frac = w / weeks
        if pattern == "burst":
            val = 10 + random.randint(0, 5)
            if frac > 0.75: val = 60 + random.randint(0, 40)
        elif pattern == "cyclical":
            val = max(0, int(50 + 40 * math.sin(2 * math.pi * w / 52)) + random.randint(-5, 5))
        elif pattern == "fading":
            val = max(0, int(90 * (1 - frac) + 5) + random.randint(-3, 3))
        elif pattern == "growing":
            val = max(0, int(10 + 80 * frac) + random.randint(-3, 3))
        elif pattern == "flat":
            val = 30 + random.randint(-5, 5)
        else:
            val = random.randint(5, 95)
        rows.append((date.strftime("%Y-%m-%d"), val))
    filepath = os.path.join(output_dir, f"{keyword.replace(' ', '_')}.csv")
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Week", f"{keyword}: (Worldwide)"])
        writer.writerows(rows)
    return filepath


def generate_all_google_trends_csvs():
    keyword_patterns = [
        ("wide-leg jeans", "growing"), ("skinny jeans", "fading"),
        ("cargo pants", "cyclical"), ("Y2K fashion", "burst"),
        ("low-rise jeans", "cyclical"), ("mom jeans", "flat"),
        ("flared pants", "cyclical"), ("baggy jeans", "burst"),
        ("corset top", "burst"), ("oversized blazer", "growing"),
    ]
    for keyword, pattern in keyword_patterns:
        path = generate_google_trends_csv(keyword, pattern)
        print(f"  ✓ {path}")


if __name__ == "__main__":
    print("Generating Google Trends CSVs...")
    generate_all_google_trends_csvs()
    print("\nGenerating mixed synthetic stream...")
    stream = generate_mixed_stream()
    print(f"  ✓ {len(stream)} events")
    print("\nGenerating burst experiment data...")
    prev, curr, truth = generate_burst_experiment_data()
    print(f"  ✓ {len(prev)} keywords, {len(truth)} true bursts")
