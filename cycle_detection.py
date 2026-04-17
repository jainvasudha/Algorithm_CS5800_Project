"""
Module B-3: Cycle Detection & Trend Classification
Owner: Vasudha Jain

Uses cosine similarity to check if a keyword's current frequency pattern
matches any historical pattern (i.e. is it cyclical / coming back?).

Then classifies each trend as New, Cyclical, or Fading based on:
  - cosine similarity to historical data
  - burst score
  - frequency trajectory (slope)

Cosine sim runs in O(n) per comparison where n = vector length.
"""

import math


def cosine_similarity(vec_a, vec_b):
    """
    Cosine similarity between two vectors.
    cos(a,b) = dot(a,b) / (|a| * |b|)

    If vectors are different lengths, truncates to the shorter one.
    Returns 0.0 if either vector is empty or all zeros.
    """
    if not vec_a or not vec_b:
        return 0.0

    n = min(len(vec_a), len(vec_b))

    dot = 0.0
    mag_a = 0.0
    mag_b = 0.0

    for i in range(n):
        dot += vec_a[i] * vec_b[i]
        mag_a += vec_a[i] ** 2
        mag_b += vec_b[i] ** 2

    if mag_a == 0 or mag_b == 0:
        return 0.0

    return dot / (math.sqrt(mag_a) * math.sqrt(mag_b))


def find_best_match(current_vector, historical_db):
    """
    Compare current_vector against every pattern in historical_db
    and return the most similar one.

    historical_db is a dict: { keyword: [freq values...] }

    Returns (best_keyword, similarity) or ("", 0.0) if db is empty.
    """
    if not historical_db or not current_vector:
        return ("", 0.0)

    best_kw = ""
    best_sim = -1.0

    for kw, hist_vec in historical_db.items():
        sim = cosine_similarity(current_vector, hist_vec)
        if sim > best_sim:
            best_sim = sim
            best_kw = kw

    return (best_kw, best_sim)


def compute_slope(values):
    """
    Simple linear regression slope for a list of values.
    Positive = trending up, negative = trending down.
    """
    n = len(values)
    if n < 2:
        return 0.0

    x_mean = (n - 1) / 2
    y_mean = sum(values) / n

    num = 0.0
    denom = 0.0
    for i in range(n):
        dx = i - x_mean
        num += dx * (values[i] - y_mean)
        denom += dx * dx

    if denom == 0:
        return 0.0
    return num / denom


def classify_trend(keyword, current_freq, prev_freq, burst_score,
                   cyclical_threshold=0.75, burst_threshold=2.0,
                   decline_threshold=-0.3):
    """
    Label a trend as "New", "Cyclical", or "Fading" using simple rules.

    Takes current and previous freq maps, builds a trajectory and
    computes cosine similarity internally.

    Decision order:
      1. slope is very negative  -> Fading
      2. high cosine similarity  -> Cyclical (it's come back before)
      3. high burst + low sim    -> New (never seen this pattern)
      4. positive slope          -> New (growing)
      5. default                 -> Fading
    """
    # build frequency trajectory from the two windows
    curr_val = current_freq.get(keyword, 0) if isinstance(current_freq, dict) else 0
    prev_val = prev_freq.get(keyword, 0) if isinstance(prev_freq, dict) else 0
    freq_trajectory = [prev_val, curr_val]

    # build vectors from both freq maps for cosine similarity
    all_keys = sorted(set(current_freq.keys()) | set(prev_freq.keys()))
    curr_vec = [current_freq.get(k, 0) for k in all_keys]
    prev_vec = [prev_freq.get(k, 0) for k in all_keys]
    cosine_sim = cosine_similarity(curr_vec, prev_vec)

    slope = compute_slope(freq_trajectory)

    # declining fast = fading, check this first
    if slope < decline_threshold:
        return "Fading"

    # strong match to a historical pattern = cyclical
    if cosine_sim >= cyclical_threshold:
        return "Cyclical"

    # bursting but doesn't match anything we've seen = new trend
    if burst_score >= burst_threshold and cosine_sim < cyclical_threshold:
        return "New"

    # still growing even if not bursting
    if slope > 0:
        return "New"

    return "Fading"


if __name__ == "__main__":
    # test cosine similarity with some sample vectors
    v1 = [10, 50, 10, 50, 10]   # cyclical pattern
    v2 = [12, 48, 11, 52, 9]    # similar cyclical
    v3 = [50, 10, 50, 10, 50]   # opposite phase

    print("Cosine similarity tests:")
    print(f"  similar cyclical:  {cosine_similarity(v1, v2):.4f}")
    print(f"  opposite phase:    {cosine_similarity(v1, v3):.4f}")
    print(f"  identical:         {cosine_similarity(v1, v1):.4f}")
    print(f"  zero vector:       {cosine_similarity([0,0,0], v1):.4f}")

    # test historical matching
    hist_db = {
        "cargo pants":    [10, 50, 10, 50, 10],
        "skinny jeans":   [90, 70, 50, 30, 10],
        "wide-leg jeans": [10, 20, 40, 60, 80],
    }
    current = [12, 48, 11, 52, 9]
    match, sim = find_best_match(current, hist_db)
    print(f"\nBest match for {current}: '{match}' (sim={sim:.4f})")

    # test classification with different scenarios
    print("\nClassifications:")

    # New - sudden burst, very different distribution
    prev1 = {"Y2K fashion": 5, "jeans": 80}
    curr1 = {"Y2K fashion": 92, "jeans": 20}
    print(f"  Y2K fashion    -> {classify_trend('Y2K fashion', curr1, prev1, 4.6)}")

    # Cyclical - same distribution both windows
    prev2 = {"cargo pants": 50, "jeans": 30}
    curr2 = {"cargo pants": 50, "jeans": 30}
    print(f"  cargo pants    -> {classify_trend('cargo pants', curr2, prev2, 1.1)}")

    # Fading - steep decline
    prev3 = {"skinny jeans": 80, "other": 20}
    curr3 = {"skinny jeans": 12, "other": 25}
    print(f"  skinny jeans   -> {classify_trend('skinny jeans', curr3, prev3, 0.15)}")

    # New - growing, different pattern
    prev4 = {"wide-leg jeans": 20, "other": 50}
    curr4 = {"wide-leg jeans": 78, "other": 10}
    print(f"  wide-leg jeans -> {classify_trend('wide-leg jeans', curr4, prev4, 2.6)}")
