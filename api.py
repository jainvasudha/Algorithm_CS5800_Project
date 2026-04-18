"""
api.py — Flask backend connecting FashionTrend UI to your real Python algorithms.

HOW TO USE:
    1. Place this file in your repo root (same folder as main.py)
    2. pip install flask flask-cors
    3. python api.py
    4. Open index.html in your browser — it will auto-connect to this backend
"""

import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request
from flask_cors import CORS

# ── Import YOUR real modules ───────────────────────────────────────────────────
from sliding_window import add_event, get_frequencies, reset_window
from top_k import top_k_heap
from burst_detection import detect_bursts
from accessibility import score_keyword
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

app = Flask(__name__)
CORS(app)

WINDOW_EVENT_MAP = {4: 400, 8: 800, 12: 1500, 26: 3000, 52: 6000}

BASE_FREQS = {
    "wide-leg jeans": 92, "y2k fashion": 67, "cargo pants": 78,
    "baggy jeans": 58, "corset top": 51, "mom jeans": 45,
    "oversized blazer": 44, "flared pants": 38, "low-rise jeans": 35,
    "skinny jeans": 22,
}


def build_events(keywords, n_per_keyword=500):
    if HAS_SYNTHETIC:
        try:
            all_events = generate_mixed_stream(n_events_per_keyword=n_per_keyword)
            filtered = [(t, kw) for t, kw in all_events
                        if kw.lower() in [k.lower() for k in keywords]]
            if filtered:
                return filtered
        except Exception:
            pass
    events = []
    t = 0
    for kw in keywords:
        base = BASE_FREQS.get(kw.lower(), random.randint(20, 70))
        count = max(100, base * n_per_keyword // 50)
        for _ in range(count):
            t += random.randint(1, 8)
            events.append((t, kw))
    events.sort(key=lambda x: x[0])
    return events


def classify_fallback(kw, current_freq, prev_freq, burst_score):
    curr = current_freq.get(kw, 0)
    prev = prev_freq.get(kw, 0)
    if prev == 0 and curr > 0: return "New"
    if curr > prev * 1.5:      return "New"
    if curr < prev * 0.7:      return "Fading"
    if burst_score > 2.0:      return "Cyclical"
    return "Stable"


@app.route('/api/detect', methods=['GET'])
def detect():
    raw = request.args.get('keywords', '')
    keywords = [k.strip() for k in raw.split(',') if k.strip()]
    if not keywords:
        return jsonify({"error": "Please provide at least one keyword"}), 400

    window_weeks = int(request.args.get('window', DEFAULT_WINDOW_SIZE))
    k            = min(int(request.args.get('k', DEFAULT_K)), len(keywords))
    method_param = request.args.get('method', DEFAULT_BURST_METHOD)
    threshold    = float(request.args.get('threshold', BURST_THRESHOLD_RATIO))
    window_size  = WINDOW_EVENT_MAP.get(window_weeks, 1500)
    n_per_kw     = max(200, window_size // max(len(keywords), 1))
    burst_method = "difference" if method_param == "diff" else "ratio"

    events = build_events(keywords, n_per_keyword=n_per_kw)
    if not events:
        return jsonify({"error": "Could not generate events"}), 400

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

    top_k_result = top_k_heap(current_freq, k)
    bursts       = detect_bursts(current_freq, prev_freq,
                                 threshold=threshold, method=burst_method)
    burst_map    = dict(bursts)

    classifications = {}
    for kw in current_freq:
        b_score = burst_map.get(kw, 0.0)
        if HAS_CYCLE:
            try:
                classifications[kw] = classify_trend(kw, current_freq, prev_freq, b_score)
            except Exception:
                classifications[kw] = classify_fallback(kw, current_freq, prev_freq, b_score)
        else:
            classifications[kw] = classify_fallback(kw, current_freq, prev_freq, b_score)

    results = []
    for kw, freq in sorted(current_freq.items(), key=lambda x: x[1], reverse=True):
        try:
            acc_score, acc_label = score_keyword(kw)
        except Exception:
            acc_score, acc_label = 0.65, "Moderate"

        prev     = prev_freq.get(kw, 0)
        bsr      = round(freq / max(prev, 1), 3)
        bsd      = freq - prev
        is_burst = burst_map.get(kw, 0.0) >= threshold

        results.append({
            "keyword":      kw,
            "freq":         freq,
            "prev":         prev,
            "label":        classifications.get(kw, "Unknown"),
            "bs_ratio":     bsr,
            "bs_diff":      round(bsd, 3),
            "isBurst":      is_burst,
            "access":       round(float(acc_score), 3),
            "access_label": acc_label,
        })

    return jsonify({
        "keywords":     keywords,
        "window_weeks": window_weeks,
        "k":            k,
        "method":       method_param,
        "threshold":    threshold,
        "total_events": len(events),
        "results":      results,
        "top_k":  [{"keyword": kw, "freq": cnt} for kw, cnt in top_k_result],
        "bursts": [{"keyword": kw, "score": round(s, 3)} for kw, s in bursts],
    })


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "running",
        "modules": {
            "sliding_window":  True,
            "top_k":           True,
            "burst_detection": True,
            "cycle_detection": HAS_CYCLE,
            "synthetic_data":  HAS_SYNTHETIC,
        }
    })


if __name__ == '__main__':
    print("=" * 55)
    print("  FashionTrend API — real algorithms running")
    print("=" * 55)
    print(f"  cycle_detection loaded : {HAS_CYCLE}")
    print(f"  synthetic data loaded  : {HAS_SYNTHETIC}")
    print(f"  burst threshold        : {BURST_THRESHOLD_RATIO}")
    print(f"  default K              : {DEFAULT_K}")
    print()
    print("  Server → http://localhost:5000")
    print("  Open index.html in your browser")
    print("=" * 55)
    app.run(port=5000, debug=True)
