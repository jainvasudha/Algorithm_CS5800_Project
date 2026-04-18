"""
config.py — Shared configuration constants.

All tunable parameters are centralised here so experiments can vary them
without modifying algorithm files.
"""

# ── Sliding Window ─────────────────────────────────────────────────────
DEFAULT_WINDOW_SIZE = 12        # 12 time-steps (weeks) per window

# ── Top-K ──────────────────────────────────────────────────────────────
DEFAULT_K = 5                   # how many top trends to surface

# ── Burst Detection ────────────────────────────────────────────────────
BURST_THRESHOLD       = 2.0     # ratio >= 2.0  →  frequency at least doubled
BURST_METHOD          = "ratio" # "ratio" | "difference"
# Aliases used by Vasudha's burst_detection.py
BURST_THRESHOLD_RATIO = 2.0
BURST_THRESHOLD_DIFF  = 10
DEFAULT_BURST_METHOD  = "ratio"

# ── Cycle Classification ───────────────────────────────────────────────
CYCLICAL_SIMILARITY_THRESHOLD = 0.75
DECLINE_SLOPE_THRESHOLD       = -0.3

# ── Accessibility Scoring ──────────────────────────────────────────────
# Weights must sum to 1.0
ACCESSIBILITY_WEIGHTS = {
    "wheelchair_friendly":   0.20,
    "adaptive_wearability":  0.25,
    "size_inclusive":        0.25,
    "sensory_friendly":      0.15,
    "price_accessibility":   0.15,
}

# (min, max) for normalising each factor to [0, 1]
ACCESSIBILITY_RANGES = {
    "wheelchair_friendly":   (0, 1),
    "adaptive_wearability":  (1, 5),
    "size_inclusive":        (1, 5),
    "sensory_friendly":      (0, 1),
    "price_accessibility":   (1, 5),
}
