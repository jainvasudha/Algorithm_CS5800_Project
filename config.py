"""
config.py — Shared constants for the Fashion Trend Detection System.
All modules import from here to stay consistent.
"""

# Sliding Window
WINDOW_SIZE_WEEKS = 12
WINDOW_SIZE_SECONDS = WINDOW_SIZE_WEEKS * 7 * 24 * 3600

# Top-K
DEFAULT_K = 5

# Burst Detection
BURST_THRESHOLD_RATIO = 2.0
BURST_THRESHOLD_DIFF = 10
DEFAULT_BURST_METHOD = "ratio"

# Cycle Detection / Cosine Similarity
SIMILARITY_THRESHOLD = 0.8

# Trend Classification labels
LABEL_NEW = "New"
LABEL_GROWING = "Growing"
LABEL_CYCLICAL = "Cyclical"
LABEL_FADING = "Fading"
LABEL_STABLE = "Stable"

# Accessibility
ACCESSIBILITY_WEIGHTS = {
    "price": 0.30,
    "availability": 0.25,
    "versatility": 0.25,
    "size_inclusivity": 0.20,
}
ACCESSIBILITY_LABELS = {
    (0.0, 0.4): "Low Accessibility",
    (0.4, 0.7): "Moderately Accessible",
    (0.7, 1.0): "Highly Accessible",
}

# Experiment parameters
EXPERIMENT_STREAM_SIZES = [1_000, 5_000, 10_000, 50_000, 100_000]
EXPERIMENT_VOCAB_SIZES = [50, 100, 500, 1_000, 5_000]
EXPERIMENT_K_VALUES = [5, 10, 50, 100, 500]

# Keywords used across the project
FASHION_KEYWORDS = [
    "wide-leg jeans", "skinny jeans", "cargo pants", "Y2K fashion",
    "low-rise jeans", "mom jeans", "flared pants", "baggy jeans",
    "corset top", "oversized blazer",
]
