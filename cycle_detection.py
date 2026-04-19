"""
Module B-3: Cycle Detection & Trend Classification
Owner: Vasudha Jain

Classifies each trend as New, Cyclical, or Fading based on:
  - per-keyword change ratio (curr / prev frequency)
  - slope of frequency trajectory
  - burst score from burst_detection module

Time: O(1) per keyword classification.
"""


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

    Takes current and previous freq maps. Uses per-keyword change ratio
    and slope for classification.

    Decision order:
      1. keyword is brand new (not in previous window)  -> New
      2. slope is very negative (declining fast)         -> Fading
      3. burst_score above threshold (sudden spike)      -> New
      4. significant growth (ratio > 1.3)                -> New
      5. stable frequency (ratio 0.7-1.3, both present)  -> Cyclical
      6. default                                         -> Fading
    """
    curr_val = current_freq.get(keyword, 0) if isinstance(current_freq, dict) else 0
    prev_val = prev_freq.get(keyword, 0) if isinstance(prev_freq, dict) else 0

    slope = compute_slope([prev_val, curr_val])

    if prev_val > 0:
        change_ratio = curr_val / prev_val
    elif curr_val > 0:
        change_ratio = float('inf')
    else:
        change_ratio = 1.0

    if prev_val == 0 and curr_val > 0:
        return "New"

    if slope < decline_threshold:
        return "Fading"

    if burst_score >= burst_threshold:
        return "New"

    if change_ratio > 1.3:
        return "New"

    if prev_val > 0 and curr_val > 0 and 0.7 <= change_ratio <= 1.3:
        return "Cyclical"

    return "Fading"


if __name__ == "__main__":
    print("Classifications:")

    prev1 = {"Y2K fashion": 5, "jeans": 80}
    curr1 = {"Y2K fashion": 92, "jeans": 20}
    print(f"  Y2K fashion    -> {classify_trend('Y2K fashion', curr1, prev1, 4.6)}")

    prev2 = {"cargo pants": 50, "jeans": 30}
    curr2 = {"cargo pants": 50, "jeans": 30}
    print(f"  cargo pants    -> {classify_trend('cargo pants', curr2, prev2, 1.1)}")

    prev3 = {"skinny jeans": 80, "other": 20}
    curr3 = {"skinny jeans": 12, "other": 25}
    print(f"  skinny jeans   -> {classify_trend('skinny jeans', curr3, prev3, 0.15)}")

    prev4 = {"wide-leg jeans": 20, "other": 50}
    curr4 = {"wide-leg jeans": 78, "other": 10}
    print(f"  wide-leg jeans -> {classify_trend('wide-leg jeans', curr4, prev4, 2.6)}")
