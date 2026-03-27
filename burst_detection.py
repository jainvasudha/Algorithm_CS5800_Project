"""
burst_detection.py — Detects keywords with sudden popularity spikes.

Two scoring methods:
  - Ratio:      burst_score = current / max(previous, 1)
  - Difference: burst_score = current - previous

Complexity:
  Time:  O(M) for scoring, O(M log M) if sorted
  Space: O(M)
"""

from config import BURST_THRESHOLD_RATIO, BURST_THRESHOLD_DIFF, DEFAULT_BURST_METHOD


def detect_bursts(current_freq, previous_freq, threshold=None,
                  method=DEFAULT_BURST_METHOD, top_k=None):
    """
    Compare two frequency maps and return keywords whose burst score
    exceeds the threshold.

    Args:
        current_freq:  dict[str, int]
        previous_freq: dict[str, int]
        threshold:     float
        method:        "ratio" or "difference"
        top_k:         int or None

    Returns:
        list[tuple[str, float]] sorted descending by score
    """
    if threshold is None:
        threshold = (BURST_THRESHOLD_RATIO if method == "ratio"
                     else BURST_THRESHOLD_DIFF)

    all_keywords = set(current_freq) | set(previous_freq)
    bursts = []

    for keyword in all_keywords:
        current = current_freq.get(keyword, 0)
        previous = previous_freq.get(keyword, 0)
        score = _compute_score(current, previous, method)
        if score > threshold:
            bursts.append((keyword, score))

    bursts.sort(key=lambda x: x[1], reverse=True)

    if top_k is not None:
        bursts = bursts[:top_k]

    return bursts


def detect_bursts_ratio(current_freq, previous_freq, threshold=None, top_k=None):
    if threshold is None:
        threshold = BURST_THRESHOLD_RATIO
    return detect_bursts(current_freq, previous_freq, threshold, "ratio", top_k)


def detect_bursts_difference(current_freq, previous_freq, threshold=None, top_k=None):
    if threshold is None:
        threshold = BURST_THRESHOLD_DIFF
    return detect_bursts(current_freq, previous_freq, threshold, "difference", top_k)


def _compute_score(current, previous, method):
    if method == "ratio":
        return current / max(previous, 1)
    elif method == "difference":
        return current - previous
    else:
        raise ValueError(f"Unknown method: {method!r}. Use 'ratio' or 'difference'.")


def sweep_thresholds(current_freq, previous_freq, ground_truth,
                     thresholds, method="ratio"):
    """Sweep thresholds and compute detection/false-positive rates."""
    total_true = len(ground_truth)
    total_non_burst = len(set(current_freq) | set(previous_freq)) - total_true

    results = []
    for t in thresholds:
        detected = detect_bursts(current_freq, previous_freq, threshold=t, method=method)
        detected_keywords = {kw for kw, _ in detected}
        tp = len(detected_keywords & ground_truth)
        fp = len(detected_keywords - ground_truth)
        results.append({
            "threshold": t,
            "true_positives": tp,
            "false_positives": fp,
            "detection_rate": tp / total_true if total_true > 0 else 0.0,
            "false_positive_rate": fp / total_non_burst if total_non_burst > 0 else 0.0,
        })
    return results


if __name__ == "__main__":
    prev = {"jeans": 10, "cargo": 20, "Y2K": 2, "mom": 50}
    curr = {"jeans": 12, "cargo": 22, "Y2K": 40, "mom": 48, "corset": 30}

    print("Ratio scoring:")
    for kw, score in detect_bursts_ratio(curr, prev, threshold=1.5):
        print(f"  {kw}: {score:.2f}")

    print("\nDifference scoring:")
    for kw, score in detect_bursts_difference(curr, prev, threshold=5):
        print(f"  {kw}: {score:.2f}")
