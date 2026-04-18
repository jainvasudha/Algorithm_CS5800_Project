"""
api.py — Flask backend connecting FashionTrend UI to your real Python algorithms.

Data source priority:
  1. Real Google Trends CSV  (data/google_trends/<keyword>.csv) — if available
  2. Synthetic data fallback (data/generate_synthetic.py)        — for unknown keywords

HOW TO USE:
    1. Place this file in your repo root (same folder as main.py)
    2. pip3 install flask flask-cors
    3. python3 api.py
    4. Open index.html in your browser
"""

import sys, os, csv, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request
from flask_cors import CORS

# ── Import YOUR real modules ───────────────────────────────────────────────────
from sliding_window import add_event, get_frequencies, reset_window
from top_k import top_k_heap
from burst_detection import detect_bursts
from accessibility import compute_accessibility_score, load_accessibility_db
from config import (
    DEFAULT_K,
    BURST_THRESHOLD_RATIO,
    DEFAULT_BURST_METHOD,
    DEFAULT_WINDOW_SIZE,
)

try:
    from cycle_detection import classify_trend
    HAS_CYCLE = True
except Exception:
    HAS_CYCLE = False

try:
    from data.generate_synthetic import generate_mixed_stream
    HAS_SYNTHETIC = True
except Exception:
    HAS_SYNTHETIC = False

# ── Load accessibility database once at startup ───────────────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "data", "accessibility_db.json")
try:
    ACCESSIBILITY_DB = load_accessibility_db(DB_PATH)
    print(f"  Accessibility DB loaded: {len(ACCESSIBILITY_DB)} keywords")
except Exception as e:
    ACCESSIBILITY_DB = {}
    print(f"  WARNING: Could not load accessibility DB: {e}")

# ── CSV folder path ────────────────────────────────────────────────────────────
CSV_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "data", "google_trends")

# ── Flask app ──────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

WINDOW_EVENT_MAP = {4: 400, 8: 800, 12: 1500, 26: 3000, 52: 6000}


# ── CSV loader ─────────────────────────────────────────────────────────────────
def keyword_to_csv_filename(keyword):
    """Convert keyword to CSV filename. e.g. 'wide-leg jeans' -> 'wide_leg_jeans.csv'"""
    return keyword.lower().replace(' ', '_').replace('-', '_') + '.csv'


def load_csv_events(keyword):
    """
    Load real Google Trends CSV data for a keyword and convert to
    (timestamp, keyword) events that sliding_window.py can process.

    CSV format:
        date,       keyword
        2004-01-01, 3
        2004-02-01, 3

    Each row's value = how many times to emit that keyword event
    for that month (scaled down to keep manageable numbers).

    Returns list of (timestamp, keyword) or empty list if CSV not found.
    """
    filename = keyword_to_csv_filename(keyword)
    filepath = os.path.join(CSV_DIR, filename)

    if not os.path.exists(filepath):
        return []

    events = []
    t = 0  # timestamp counter

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)  # skip header row

            for row in reader:
                if len(row) < 2:
                    continue
                try:
                    value = int(row[1])
                except (ValueError, IndexError):
                    continue

                t += 1
                # Emit 'value' events for this time period
                # This converts monthly interest score into event count
                for _ in range(max(1, value)):
                    events.append((t, keyword))
                    t += 1

    except Exception as e:
        print(f"  Warning: Could not read {filename}: {e}")
        return []

    return events


def build_events_synthetic(keywords, n_per_keyword=500):
    """Synthetic fallback for keywords without CSV files."""
    if HAS_SYNTHETIC:
        try:
            all_events = generate_mixed_stream(n_events_per_keyword=n_per_keyword)
            filtered = [(t, kw) for t, kw in all_events
                        if kw.lower() in [k.lower() for k in keywords]]
            if filtered:
                return filtered
        except Exception:
            pass

    # Manual fallback
    BASE_FREQS = {
        "wide-leg jeans": 92, "y2k fashion": 67, "cargo pants": 78,
        "baggy jeans": 58,    "corset top": 51,  "mom jeans": 45,
        "oversized blazer": 44, "flared pants": 38,
        "low-rise jeans": 35,  "skinny jeans": 22,
    }
    events = []
    t = 0
    for kw in keywords:
        base = BASE_FREQS.get(kw.lower(), random.randint(20, 70))
        for _ in range(max(100, base * 5)):
            t += random.randint(1, 8)
            events.append((t, kw))
    events.sort(key=lambda x: x[0])
    return events


def build_events(keywords, n_per_keyword=500):
    """
    Build event stream using real CSV data where available,
    synthetic data as fallback for unknown keywords.
    """
    all_events = []
    csv_used = []
    synthetic_used = []

    for kw in keywords:
        csv_events = load_csv_events(kw)
        if csv_events:
            all_events.extend(csv_events)
            csv_used.append(kw)
            print(f"  ✅ Real CSV data: '{kw}' ({len(csv_events)} events)")
        else:
            synthetic_used.append(kw)
            print(f"  🔄 Synthetic data: '{kw}' (no CSV found)")

    # Get synthetic events for keywords without CSV
    if synthetic_used:
        syn_events = build_events_synthetic(synthetic_used, n_per_keyword)
        all_events.extend(syn_events)

    # Sort all events by timestamp
    all_events.sort(key=lambda x: x[0])
    return all_events, csv_used, synthetic_used


def classify_fallback(kw, current_freq, prev_freq, burst_score):
    """Fallback classifier matching your real cycle_detection.py logic."""
    curr = current_freq.get(kw, 0)
    prev = prev_freq.get(kw, 0)
    if prev == 0 and curr > 0:   return "New"
    if curr > prev * 1.5:        return "New"
    if curr < prev * 0.7:        return "Fading"
    if burst_score >= 2.0:       return "New"
    if prev > 0 and 0.7 <= (curr / max(prev, 1)) <= 1.3:
        return "Cyclical"
    return "Fading"


# ── Main API endpoint ──────────────────────────────────────────────────────────
@app.route('/api/detect', methods=['GET'])
def detect():
    raw      = request.args.get('keywords', '')
    keywords = [k.strip() for k in raw.split(',') if k.strip()]
    if not keywords:
        return jsonify({"error": "Please provide at least one keyword"}), 400

    window_weeks = int(request.args.get('window', DEFAULT_WINDOW_SIZE))
    k            = min(int(request.args.get('k', DEFAULT_K)), len(keywords))
    method_param = request.args.get('method', DEFAULT_BURST_METHOD)
    threshold    = float(request.args.get('threshold', BURST_THRESHOLD_RATIO))
    window_size  = WINDOW_EVENT_MAP.get(window_weeks, 1500)
    burst_method = "difference" if method_param == "diff" else "ratio"

    # Step 1: Build events — real CSV where available, synthetic fallback
    events, csv_used, synthetic_used = build_events(keywords)
    if not events:
        return jsonify({"error": "Could not generate events"}), 400

    # Step 2: Sliding window — Bhoomika's sliding_window.py
    mid = len(events) // 2
    reset_window()
    for t, kw in events[:mid]:
        add_event(t, kw, window_size)
    prev_freq = get_frequencies()

    reset_window()
    for t, kw in events[mid:]:
        add_event(t, kw, window_size)
    current_freq = get_frequencies()

    if not current_freq:
        return jsonify({"error": "No frequency data"}), 400

    # Step 3: Top-K heap — Vasudha's top_k.py
    top_k_result = top_k_heap(current_freq, k)

    # Step 4: Burst detection — Vasudha's burst_detection.py
    bursts    = detect_bursts(current_freq, prev_freq,
                              threshold=threshold, method=burst_method)
    burst_map = dict(bursts)

    # Step 5: Classification — Vasudha's cycle_detection.py
    classifications = {}
    for kw in current_freq:
        b_score = burst_map.get(kw, 0.0)
        if HAS_CYCLE:
            try:
                classifications[kw] = classify_trend(
                    kw, current_freq, prev_freq, b_score)
            except Exception:
                classifications[kw] = classify_fallback(
                    kw, current_freq, prev_freq, b_score)
        else:
            classifications[kw] = classify_fallback(
                kw, current_freq, prev_freq, b_score)

    # Step 6: Accessibility — Parvathi's accessibility.py
    results = []
    for kw, freq in sorted(current_freq.items(),
                            key=lambda x: x[1], reverse=True):
        if ACCESSIBILITY_DB:
            acc_score, acc_label = compute_accessibility_score(
                kw, ACCESSIBILITY_DB)
            if acc_score == 0.0 and acc_label == "NO_DATA":
                acc_score, acc_label = 0.65, "Moderately Accessible"
        else:
            acc_score, acc_label = 0.65, "Moderately Accessible"

        prev     = prev_freq.get(kw, 0)
        bsr      = round(freq / max(prev, 1), 3)
        bsd      = freq - prev
        is_burst = burst_map.get(kw, 0.0) >= threshold
        # Flag whether this keyword used real or synthetic data
        data_source = "Real CSV" if kw in csv_used else "Synthetic"

        results.append({
            "keyword":      kw,
            "freq":         freq,
            "prev":         prev,
            "label":        classifications.get(kw, "Fading"),
            "bs_ratio":     bsr,
            "bs_diff":      round(bsd, 3),
            "isBurst":      is_burst,
            "access":       round(float(acc_score), 3),
            "access_label": acc_label,
            "data_source":  data_source,
        })

    return jsonify({
        "keywords":       keywords,
        "window_weeks":   window_weeks,
        "k":              k,
        "method":         method_param,
        "threshold":      threshold,
        "total_events":   len(events),
        "csv_keywords":   csv_used,
        "synthetic_keywords": synthetic_used,
        "results":        results,
        "top_k":  [{"keyword": kw, "freq": cnt} for kw, cnt in top_k_result],
        "bursts": [{"keyword": kw, "score": round(s, 3)} for kw, s in bursts],
    })


@app.route('/api/health', methods=['GET'])
def health():
    # Check which CSV files are available
    csv_available = []
    if os.path.exists(CSV_DIR):
        csv_available = [f.replace('.csv', '').replace('_', ' ')
                        for f in os.listdir(CSV_DIR) if f.endswith('.csv')]

    return jsonify({
        "status": "running",
        "modules": {
            "sliding_window":   True,
            "top_k":            True,
            "burst_detection":  True,
            "cycle_detection":  HAS_CYCLE,
            "synthetic_data":   HAS_SYNTHETIC,
            "accessibility_db": len(ACCESSIBILITY_DB) > 0,
        },
        "csv_keywords_available": csv_available,
    })


if __name__ == '__main__':
    # Check available CSV files
    csv_count = 0
    if os.path.exists(CSV_DIR):
        csv_count = len([f for f in os.listdir(CSV_DIR) if f.endswith('.csv')])

    print("=" * 55)
    print("  FashionTrend API — real algorithms running")
    print("=" * 55)
    print(f"  cycle_detection loaded  : {HAS_CYCLE}")
    print(f"  synthetic data loaded   : {HAS_SYNTHETIC}")
    print(f"  accessibility DB loaded : {len(ACCESSIBILITY_DB) > 0}")
    print(f"  Google Trends CSVs      : {csv_count} files")
    print(f"  burst threshold         : {BURST_THRESHOLD_RATIO}")
    print(f"  default K               : {DEFAULT_K}")
    print()
    print("  Data priority:")
    print("  1. Real Google Trends CSV (10 known keywords)")
    print("  2. Synthetic fallback (any other keyword)")
    print()
    print("  Server → http://localhost:5000")
    print("  Open index.html in your browser")
    print("=" * 55)
    app.run(port=5000, debug=True)
