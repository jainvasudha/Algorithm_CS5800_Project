"""
app.py — Streamlit UI for the Real-Time Fashion Trend Detection System.
Run with:  streamlit run app.py
"""

import csv
import json
import math
import os
import random
import sys
import time
from collections import deque

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from baseline import compute_baseline
from burst_detection import detect_bursts
from config import (
    BURST_THRESHOLD_DIFF,
    BURST_THRESHOLD_RATIO,
    DEFAULT_K,
    FASHION_KEYWORDS,
)
from cycle_detection import classify_trend, cosine_similarity
from data.generate_synthetic import (
    generate_burst_experiment_data,
    generate_mixed_stream,
    generate_scalable_stream,
)
from top_k import top_k_heap, top_k_sort
from accessibility import score_keyword

try:
    from pytrends.request import TrendReq
    HAS_PYTRENDS = True
except ImportError:
    HAS_PYTRENDS = False

# ───────────────────────── Config ─────────────────────────

st.set_page_config(
    page_title="Fashion Trend Detector",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "google_trends")
RESULTS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "experiment_results.json")

CLASSIFICATION_COLORS = {
    "New": "🟢", "Cyclical": "🔵", "Fading": "🔴", "Growing": "🟡", "Stable": "⚪",
}

# ───────────────────────── Cached loaders ─────────────────────────

@st.cache_data(ttl=300, show_spinner="Fetching from Google Trends...")
def fetch_google_trends(keyword, timeframe="today 5-y"):
    pytrends = TrendReq(hl="en-US", tz=360)
    pytrends.build_payload([keyword], timeframe=timeframe)
    df = pytrends.interest_over_time()
    if df.empty or keyword not in df.columns:
        return None
    values = df[keyword].tolist()
    dates = [d.strftime("%Y-%m-%d") for d in df.index]
    return list(zip(dates, values))


@st.cache_data(show_spinner=False)
def load_google_trends_freq_map():
    freq_map = {}
    if not os.path.isdir(DATA_DIR):
        return freq_map
    for filename in sorted(os.listdir(DATA_DIR)):
        if not filename.endswith(".csv"):
            continue
        with open(os.path.join(DATA_DIR, filename)) as f:
            reader = csv.reader(f)
            header = next(reader)
            keyword = header[1].split(":")[0].strip()
            last_val = 0
            for row in reader:
                if len(row) >= 2 and row[1].strip().isdigit():
                    last_val = int(row[1])
            freq_map[keyword] = last_val
    return freq_map


@st.cache_data(show_spinner=False)
def load_google_trends_timeseries():
    series = {}
    if not os.path.isdir(DATA_DIR):
        return series
    for filename in sorted(os.listdir(DATA_DIR)):
        if not filename.endswith(".csv"):
            continue
        with open(os.path.join(DATA_DIR, filename)) as f:
            reader = csv.reader(f)
            header = next(reader)
            keyword = header[1].split(":")[0].strip()
            rows = []
            for row in reader:
                if len(row) >= 2 and row[1].strip().isdigit():
                    rows.append((row[0], int(row[1])))
            series[keyword] = rows
    return series


def save_trend_to_dataset(keyword, timeseries):
    filename = keyword.lower().replace(" ", "_").replace("-", "_") + ".csv"
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", keyword])
        for date, val in timeseries:
            writer.writerow([date, val])
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "accessibility_db.json")
    with open(db_path) as f:
        db = json.load(f)
    if keyword not in db:
        db[keyword] = {"price": 0.5, "availability": 0.5, "versatility": 0.5, "size_inclusivity": 0.5}
        with open(db_path, "w") as f:
            json.dump(db, f, indent=4)
    load_google_trends_freq_map.clear()
    load_google_trends_timeseries.clear()


def build_prev_current_from_timeseries(series, split_frac=0.5):
    prev_freq, curr_freq = {}, {}
    for kw, rows in series.items():
        if not rows:
            continue
        mid = int(len(rows) * split_frac)
        prev_freq[kw] = sum(v for _, v in rows[:mid])
        curr_freq[kw] = sum(v for _, v in rows[mid:])
    return prev_freq, curr_freq


# ───────────────────────── Helper: insight text ─────────────────────────

def trend_direction_text(prev_val, curr_val):
    if prev_val == 0 and curr_val > 0:
        return "🆕 Brand new — wasn't seen before"
    if curr_val == 0 and prev_val > 0:
        return "💀 Disappeared completely"
    if prev_val == 0 and curr_val == 0:
        return "—  No activity"
    pct = ((curr_val - prev_val) / prev_val) * 100
    if pct > 50:
        return f"🚀 Surging — up {pct:+.0f}%"
    if pct > 10:
        return f"📈 Growing — up {pct:+.0f}%"
    if pct > -10:
        return f"➡️  Stable — {pct:+.0f}%"
    if pct > -50:
        return f"📉 Declining — {pct:+.0f}%"
    return f"⬇️  Dropping fast — {pct:+.0f}%"


def classification_badge(label):
    icon = CLASSIFICATION_COLORS.get(label, "⚪")
    return f"{icon} {label}"


def burst_insight(ratio, diff, method, threshold):
    if method == "ratio":
        if ratio > threshold:
            return f"⚡ **Bursting** — popularity multiplied by {ratio:.1f}x (above {threshold} threshold)"
        return f"Steady — ratio of {ratio:.2f}x is below the {threshold} threshold"
    else:
        if diff > threshold:
            return f"⚡ **Bursting** — jumped by {diff:+,} points (above {threshold} threshold)"
        return f"Steady — change of {diff:+,} is below the {threshold} threshold"


def accessibility_insight(score, label):
    if score >= 0.7:
        return f"✅ {score:.2f} — **{label}**: affordable, widely available, size-inclusive"
    if score >= 0.4:
        return f"🟡 {score:.2f} — **{label}**: moderate price/availability"
    return f"🔴 {score:.2f} — **{label}**: expensive, limited sizes, or hard to find"


# ───────────────────────── Page header ─────────────────────────

st.markdown(
    """
    <div style="text-align:center; padding: 0.5rem 0 1rem 0;">
        <h1 style="margin-bottom:0.2rem;">👗 Fashion Trend Detector</h1>
        <p style="color:gray; font-size:1.05rem; margin-top:0;">
            Detect what's trending, what's fading, and what's coming back — powered by algorithms.
        </p>
        <p style="color:gray; font-size:0.85rem;">
            CS 5800 · Bhoomika Panday · Vasudha Jain · Shravya (Parvathi)
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_dashboard, tab_search, tab_window, tab_topk, tab_burst, tab_bench = st.tabs([
    "📊 Trend Dashboard",
    "🔍 Search a Trend",
    "⚡ Speed Test: Sliding Window",
    "🏆 Ranking: Heap vs Sort",
    "💥 Spike Detection",
    "📈 Performance Benchmarks",
])


# ╔══════════════════════════════════════════════════════════════╗
# ║  TAB 1 — TREND DASHBOARD                                    ║
# ╚══════════════════════════════════════════════════════════════╝

with tab_dashboard:

    st.markdown(
        "See which fashion keywords are trending right now based on Google Trends data. "
        "Each keyword is ranked by popularity, checked for sudden spikes, classified into "
        "a trend type, and scored for accessibility."
    )

    # Controls in a clean row
    st.markdown("##### Settings")
    col1, col2, col3 = st.columns(3)
    with col1:
        k = st.slider(
            "How many top trends to show",
            1, 10, DEFAULT_K, key="pipe_k",
            help="Show the K most popular fashion keywords from the current period.",
        )
    with col2:
        burst_method = st.selectbox(
            "Spike detection method",
            ["ratio", "difference"],
            key="pipe_method",
            help="**Ratio**: flags keywords that *multiplied* in popularity (good for small trends going viral). "
                 "**Difference**: flags keywords with the biggest *absolute* jump (good for already-popular trends).",
        )
    with col3:
        default_thr = BURST_THRESHOLD_RATIO if burst_method == "ratio" else BURST_THRESHOLD_DIFF
        threshold = st.number_input(
            "Spike sensitivity (threshold)",
            0.0, 10000.0, float(default_thr), key="pipe_thr",
            help="Lower = more sensitive (catches smaller spikes but may give false alarms). "
                 "Higher = stricter (only flags dramatic spikes).",
        )

    st.divider()

    series = load_google_trends_timeseries()
    if not series:
        st.warning("No data files found. Add Google Trends CSVs to data/google_trends/.")
    else:
        prev_freq, curr_freq = build_prev_current_from_timeseries(series)

        top_k = top_k_heap(curr_freq, k)
        bursts = detect_bursts(curr_freq, prev_freq, threshold=threshold, method=burst_method)
        burst_map = dict(bursts)

        # ── KPI row ──
        total_kw = len(curr_freq)
        bursting_count = len(bursts)
        top_kw, top_freq = top_k[0] if top_k else ("—", 0)
        avg_freq = sum(curr_freq.values()) / max(len(curr_freq), 1)

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Keywords tracked", total_kw, help="Total unique fashion keywords in the dataset.")
        k2.metric(
            "Currently spiking",
            bursting_count,
            help=f"Keywords whose {burst_method} score exceeds {threshold}.",
        )
        k3.metric(
            "#1 trending keyword",
            top_kw,
            help="Most popular keyword by total search interest in the current period.",
        )
        k4.metric(
            "Avg. interest score",
            f"{avg_freq:,.0f}",
            help="Average total search interest across all keywords. A baseline to compare individual keywords against.",
        )

        st.divider()

        # ── Main results table ──
        st.markdown("##### Top trending keywords")
        st.caption(
            "Each keyword is scored across 4 dimensions: popularity (frequency), "
            "spike activity (burst score), trend type (classification), and how accessible "
            "it is for the average consumer."
        )

        rows = []
        for rank_i, (kw, count) in enumerate(top_k, 1):
            b_score = burst_map.get(kw, 0.0)
            label = classify_trend(kw, curr_freq, prev_freq, b_score)
            acc_score, acc_label = score_keyword(kw)
            prev_val = prev_freq.get(kw, 0)
            pct_change = ((count - prev_val) / prev_val * 100) if prev_val > 0 else 0

            rows.append({
                "Rank": f"#{rank_i}",
                "Keyword": kw,
                "Popularity": f"{count:,}",
                "Change": f"{pct_change:+.0f}%" if prev_val > 0 else "🆕 New",
                "Spike score": f"{b_score:.1f}" if b_score > 0 else "—",
                "Trend type": classification_badge(label),
                "Accessibility": f"{acc_score:.2f}" if acc_score else "—",
            })

        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # ── Legend for first-time users ──
        with st.expander("What do the trend types mean?"):
            st.markdown(
                """
| Type | Meaning | Example |
|------|---------|---------|
| 🟢 **New** | Recently appeared or surging for the first time | Y2K fashion in 2021 |
| 🔵 **Cyclical** | Has been popular before and is coming back | Cargo pants (2000s → now) |
| 🔴 **Fading** | Was popular but declining | Skinny jeans |
| 🟡 **Growing** | Steadily increasing over time | Oversized blazer |
| ⚪ **Stable** | Consistent, no major change | Mom jeans |
"""
            )

        # ── Side-by-side: Spikes + Time series ──
        left, right = st.columns([1, 2])
        with left:
            st.markdown("##### Spiking right now")
            if bursts:
                st.caption(
                    f"These keywords exceeded the {burst_method} threshold of {threshold} — "
                    "their popularity changed dramatically between periods."
                )
                for kw, score in bursts[:8]:
                    st.markdown(f"- **{kw}** — spike score: `{score:.1f}`")
            else:
                st.info(
                    "No spikes detected at this sensitivity. Try lowering the threshold to catch subtler changes."
                )

        with right:
            st.markdown("##### Search interest over time")
            st.caption("Google Trends data for all tracked keywords. Higher = more search interest in that period.")
            df = pd.DataFrame({kw: [v for _, v in rows_] for kw, rows_ in series.items()})
            st.line_chart(df, height=320)


# ╔══════════════════════════════════════════════════════════════╗
# ║  TAB 2 — SEARCH A TREND                                     ║
# ╚══════════════════════════════════════════════════════════════╝

with tab_search:
    st.markdown(
        "Look up any fashion keyword to see how it's performing. "
        "If it's already in our dataset we'll show it instantly — "
        "if not, we'll fetch live data from Google Trends."
    )

    series = load_google_trends_timeseries()
    if series:
        prev_freq, curr_freq = build_prev_current_from_timeseries(series)
    else:
        prev_freq, curr_freq = {}, {}

    col_search, col_settings = st.columns([3, 1])
    with col_search:
        lookup_kw = st.text_input(
            "Search for a fashion keyword",
            value="",
            placeholder="Try: cargo pants, bell bottoms, crochet top, platform shoes...",
            key="search_kw",
            label_visibility="collapsed",
        )
    with col_settings:
        search_method = st.selectbox(
            "Spike method",
            ["ratio", "difference"],
            key="search_method",
            label_visibility="collapsed",
        )

    if lookup_kw.strip():
        lookup_kw = lookup_kw.strip()
        in_dataset = lookup_kw in curr_freq

        look_prev, look_curr = 0, 0
        lookup_prev_freq, lookup_curr_freq = prev_freq, curr_freq
        live_ts = None
        fetch_failed = False

        if in_dataset:
            look_curr = curr_freq[lookup_kw]
            look_prev = prev_freq.get(lookup_kw, 0)
            lookup_curr_freq = curr_freq
            lookup_prev_freq = prev_freq
            st.caption(f"✅ Found **{lookup_kw}** in local dataset")
        else:
            if not HAS_PYTRENDS:
                st.warning(
                    f"**{lookup_kw}** isn't in the local dataset, and live fetching isn't available "
                    "(pytrends not installed). Try one of the existing keywords."
                )
                fetch_failed = True
            else:
                live_ts = fetch_google_trends(lookup_kw)
                if live_ts:
                    st.caption(f"🌐 **{lookup_kw}** fetched live from Google Trends ({len(live_ts)} data points)")
                    mid = len(live_ts) // 2
                    look_prev = sum(v for _, v in live_ts[:mid])
                    look_curr = sum(v for _, v in live_ts[mid:])
                    lookup_prev_freq = dict(prev_freq, **{lookup_kw: look_prev})
                    lookup_curr_freq = dict(curr_freq, **{lookup_kw: look_curr})
                else:
                    st.error(
                        f"Couldn't find **{lookup_kw}** on Google Trends. "
                        "Check the spelling or try a more common fashion term."
                    )
                    fetch_failed = True

        if not fetch_failed and (look_prev or look_curr):
            st.divider()

            ratio_score = look_curr / max(look_prev, 1)
            diff_score = look_curr - look_prev
            label = classify_trend(lookup_kw, lookup_curr_freq, lookup_prev_freq, ratio_score)
            acc_score, acc_label = score_keyword(lookup_kw)

            ranking = top_k_heap(lookup_curr_freq, len(lookup_curr_freq))
            rank = next((i + 1 for i, (kw, _) in enumerate(ranking) if kw == lookup_kw), None)

            # ── Result cards ──
            st.markdown(f"### {classification_badge(label)}  **{lookup_kw}**")

            c1, c2, c3 = st.columns(3)

            with c1:
                st.markdown("**📊 Popularity**")
                delta = look_curr - look_prev
                st.metric(
                    "Search interest",
                    f"{look_curr:,}",
                    delta=f"{delta:+,} vs previous period",
                    delta_color="normal",
                )
                st.caption(trend_direction_text(look_prev, look_curr))

            with c2:
                st.markdown("**💥 Spike analysis**")
                st.metric("Ratio score", f"{ratio_score:.2f}x", help="Current / Previous. Above 2.0 = doubled.")
                st.metric("Absolute change", f"{diff_score:+,}", help="Raw point difference between periods.")
                thr_val = BURST_THRESHOLD_RATIO if search_method == "ratio" else BURST_THRESHOLD_DIFF
                st.caption(burst_insight(ratio_score, diff_score, search_method, thr_val))

            with c3:
                st.markdown("**♿ Accessibility**")
                st.caption(accessibility_insight(acc_score, acc_label))
                if rank:
                    rank_pct = (rank / len(lookup_curr_freq)) * 100
                    st.markdown(f"**Rank: #{rank}** out of {len(lookup_curr_freq)} keywords")
                    if rank_pct <= 20:
                        st.caption("🏆 Top 20% — one of the most popular right now")
                    elif rank_pct <= 50:
                        st.caption("Performing above average")
                    else:
                        st.caption("Below the midpoint — not a top trend currently")

            # ── Chart (live-fetched) ──
            if live_ts:
                st.divider()
                st.markdown(f"##### Search interest over time — *{lookup_kw}*")
                ts_df = pd.DataFrame(live_ts, columns=["Date", "Interest"])
                ts_df["Year"] = ts_df["Date"].str[:4]
                yearly = ts_df.groupby("Year")["Interest"].mean().round(1)
                st.bar_chart(yearly, height=250)
                st.caption("Average yearly search interest from Google Trends. Higher = more people searched for this term.")

                csv_exists = os.path.exists(
                    os.path.join(DATA_DIR, lookup_kw.lower().replace(" ", "_").replace("-", "_") + ".csv")
                )
                if not csv_exists:
                    st.divider()
                    st.markdown(
                        f"💾 Want to add **{lookup_kw}** to the local dataset? "
                        "This saves it so it appears on the dashboard and in future analyses."
                    )
                    if st.button("Save to dataset", key="search_save", type="primary"):
                        save_trend_to_dataset(lookup_kw, live_ts)
                        st.success(f"Saved! **{lookup_kw}** will now appear in the Trend Dashboard.")
                        st.rerun()

    elif series:
        st.divider()
        st.markdown("##### Keywords in the dataset")
        st.caption("Type any of these for instant results, or try something new to fetch from Google Trends.")
        kw_cols = st.columns(5)
        for i, kw in enumerate(sorted(curr_freq.keys())):
            kw_cols[i % 5].markdown(f"` {kw} `")


# ╔══════════════════════════════════════════════════════════════╗
# ║  TAB 3 — SLIDING WINDOW SPEED TEST                          ║
# ╚══════════════════════════════════════════════════════════════╝

with tab_window:
    st.markdown(
        "### How fast can we count trending keywords?"
    )
    st.markdown(
        "When thousands of fashion events stream in every second, we need to keep a running "
        "count of keyword frequencies within a time window. There are two ways to do this:"
    )

    col_naive, col_smart = st.columns(2)
    with col_naive:
        st.error("**Naive method (Baseline)**", icon="🐢")
        st.markdown(
            "Re-scans *every* event in the window from scratch each time a new event arrives. "
            "Gets slower and slower as more data comes in."
        )
        st.code("Time: O(N) per update", language=None)

    with col_smart:
        st.success("**Smart method (Sliding Window)**", icon="🚀")
        st.markdown(
            "Keeps a running count — adds new events and removes expired ones instantly. "
            "Speed stays constant regardless of data size."
        )
        st.code("Time: O(1) amortized per update", language=None)

    st.divider()
    st.markdown("##### Try it yourself")
    st.caption("Pick a stream size and window, then see the speed difference live.")

    col1, col2 = st.columns(2)
    with col1:
        n_events = st.select_slider(
            "Number of incoming events",
            options=[500, 1_000, 2_000, 5_000, 10_000],
            value=2_000,
            key="win_n",
            help="More events = bigger speed difference. Try 10,000 for the most dramatic result.",
        )
    with col2:
        win_size = st.slider(
            "Window size (how many recent events to track)",
            50, 2_000, 500, key="win_w",
            help="Only events within this window are counted. Older events are expired.",
        )

    if st.button("Run speed test", type="primary", key="win_run"):
        events = generate_scalable_stream(n_events, n_keywords=10)

        with st.spinner("Running smart method..."):
            window, freq = deque(), {}
            t0 = time.perf_counter()
            for t, kw in events:
                window.append((t, kw))
                freq[kw] = freq.get(kw, 0) + 1
                while window and window[0][0] <= t - win_size:
                    _, old_kw = window.popleft()
                    freq[old_kw] -= 1
                    if freq[old_kw] == 0:
                        del freq[old_kw]
            smart_time = time.perf_counter() - t0
            smart_freq = dict(freq)

        with st.spinner("Running naive method (this will be slower)..."):
            t0 = time.perf_counter()
            for i, (t, _) in enumerate(events):
                if i % 100 == 0:
                    _ = compute_baseline(events[: i + 1], t, win_size)
            naive_time = time.perf_counter() - t0
            naive_freq = compute_baseline(events, events[-1][0], win_size)

        st.divider()

        # Results
        speedup = naive_time / smart_time if smart_time > 0 else 0
        agree = smart_freq == naive_freq

        st.markdown("##### Results")

        c1, c2, c3 = st.columns(3)
        c1.metric(
            "🚀 Smart method",
            f"{smart_time * 1000:.2f} ms",
            help="Time to process all events using the incremental sliding window.",
        )
        c2.metric(
            "🐢 Naive method",
            f"{naive_time * 1000:.2f} ms",
            help="Time to process all events using full recomputation (1 query per 100 events).",
        )
        c3.metric(
            "Speed advantage",
            f"{speedup:,.0f}x faster",
            help="How many times faster the smart method is.",
        )

        if agree:
            st.success(
                "✅ **Both methods produced identical results** — the smart method is faster "
                f"but just as accurate. At {n_events:,} events, it's **{speedup:,.0f}x faster**.",
                icon="✅",
            )
        else:
            st.error("Results don't match — there may be a bug.", icon="❌")

        st.caption(
            f"💡 *As data grows, this gap widens dramatically. At 100K events in our pre-run benchmarks, "
            f"the smart method took 0.13s while naive took 1,855s — a **14,000x** difference.*"
        )

        with st.expander("View final keyword counts"):
            df = pd.DataFrame(
                sorted(smart_freq.items(), key=lambda x: -x[1]),
                columns=["Keyword", "Event count in window"],
            )
            st.dataframe(df, use_container_width=True, hide_index=True)


# ╔══════════════════════════════════════════════════════════════╗
# ║  TAB 4 — TOP-K HEAP vs SORT                                 ║
# ╚══════════════════════════════════════════════════════════════╝

with tab_topk:
    st.markdown("### Finding the top trends — which algorithm is faster?")
    st.markdown(
        "Given thousands of fashion keywords, we need to find the K most popular ones. "
        "There are two approaches:"
    )

    col_sort, col_heap = st.columns(2)
    with col_sort:
        st.error("**Sort everything**", icon="📋")
        st.markdown(
            "Sort *all* M keywords by popularity, then pick the first K. "
            "Does more work than necessary when K is small."
        )
        st.code("Time: O(M log M)  ·  Space: O(M)", language=None)
    with col_heap:
        st.success("**Min-Heap (smart)**", icon="🏆")
        st.markdown(
            "Keep a small basket of K items. For each keyword, only swap it in if it "
            "beats the current smallest. Never sorts the full list."
        )
        st.code("Time: O(M log K)  ·  Space: O(K)", language=None)

    st.divider()
    st.markdown("##### Try it yourself")
    st.caption(
        "Adjust M (total keywords) and K (how many to find). "
        "The heap advantage grows when K is much smaller than M."
    )

    col1, col2 = st.columns(2)
    with col1:
        m_size = st.select_slider(
            "Total keywords (M)",
            options=[50, 100, 500, 1_000, 5_000, 10_000],
            value=1_000,
            key="tk_m",
            help="Simulates a dictionary of M fashion keywords with random popularity scores.",
        )
    with col2:
        k_size = st.slider(
            "Find the top K",
            1, min(m_size, 500), 5, key="tk_k",
            help="When K is small relative to M, the heap method shines.",
        )

    k_ratio = k_size / m_size * 100
    if k_ratio < 5:
        st.caption(f"K is {k_ratio:.1f}% of M — **heap should be significantly faster**.")
    elif k_ratio < 30:
        st.caption(f"K is {k_ratio:.0f}% of M — heap should be moderately faster.")
    else:
        st.caption(f"K is {k_ratio:.0f}% of M — methods should be close in speed (heap advantage shrinks).")

    if st.button("Run comparison", type="primary", key="tk_run"):
        random.seed(42)
        freq_map = {f"keyword_{i}": random.randint(1, 10_000) for i in range(m_size)}

        repeats = 50
        t0 = time.perf_counter()
        for _ in range(repeats):
            heap_result = top_k_heap(freq_map, k_size)
        heap_time = (time.perf_counter() - t0) / repeats

        t0 = time.perf_counter()
        for _ in range(repeats):
            sort_result = top_k_sort(freq_map, k_size)
        sort_time = (time.perf_counter() - t0) / repeats

        st.divider()
        st.markdown("##### Results")

        c1, c2, c3 = st.columns(3)
        c1.metric(
            "🏆 Heap method",
            f"{heap_time * 1e6:.1f} μs",
            help="Microseconds to find top-K using min-heap.",
        )
        c2.metric(
            "📋 Sort method",
            f"{sort_time * 1e6:.1f} μs",
            help="Microseconds to find top-K by sorting everything.",
        )
        speedup = sort_time / heap_time if heap_time > 0 else 0
        c3.metric(
            "Heap advantage",
            f"{speedup:.2f}x faster",
        )

        agree = set(heap_result) == set(sort_result)
        if agree:
            st.success(
                f"✅ Both methods found the same top {k_size} keywords. "
                f"Heap was **{speedup:.1f}x** faster on {m_size:,} keywords.",
                icon="✅",
            )
        else:
            st.error("Methods returned different results.", icon="❌")

        # Interpretation
        if speedup > 3:
            st.caption("💡 *Big advantage for heap — as expected when K is much smaller than M.*")
        elif speedup > 1.2:
            st.caption("💡 *Modest advantage for heap. Try a larger M or smaller K for a bigger gap.*")
        else:
            st.caption(
                "💡 *Methods are close in speed — this is expected when K approaches M. "
                "Both have to do similar work.*"
            )

        with st.expander(f"View top {k_size} keywords"):
            df = pd.DataFrame(heap_result, columns=["Keyword", "Popularity score"])
            st.dataframe(df, use_container_width=True, hide_index=True)


# ╔══════════════════════════════════════════════════════════════╗
# ║  TAB 5 — BURST / SPIKE DETECTION                            ║
# ╚══════════════════════════════════════════════════════════════╝

with tab_burst:
    st.markdown("### Detecting sudden spikes in popularity")
    st.markdown(
        "Compare keyword popularity between two time periods to find which items are "
        "suddenly gaining attention. Two scoring methods are available:"
    )

    col_r, col_d = st.columns(2)
    with col_r:
        st.info("**Ratio method**", icon="✖️")
        st.markdown(
            "Score = current / previous. "
            "Catches *relative* growth — great for small trends exploding (2 → 20 = 10x)."
        )
    with col_d:
        st.info("**Difference method**", icon="➕")
        st.markdown(
            "Score = current − previous. "
            "Catches *absolute* jumps — great for big trends getting bigger (500 → 700 = +200)."
        )

    st.divider()

    source = st.radio(
        "Choose data source",
        ["Google Trends (real data)", "Synthetic data (with known answers)"],
        horizontal=True,
        key="burst_src",
        help="Synthetic data has pre-defined spikes so we can verify accuracy. "
             "Real data shows how the algorithm works on actual fashion trends.",
    )

    if source == "Google Trends (real data)":
        series = load_google_trends_timeseries()
        prev_freq, curr_freq = build_prev_current_from_timeseries(series)
        ground_truth = None
    else:
        prev_freq, curr_freq, ground_truth = generate_burst_experiment_data(
            n_keywords=20, n_true_bursts=5
        )
        st.caption(f"Generated 20 synthetic keywords. 5 have injected spikes — can the algorithm find them?")

    col1, col2 = st.columns(2)
    with col1:
        method = st.selectbox(
            "Scoring method",
            ["ratio", "difference"],
            key="burst_method_tab",
        )
    with col2:
        if method == "ratio":
            thr = st.slider(
                "Sensitivity threshold",
                1.0, 10.0, 2.0, 0.1, key="burst_thr_r",
                help="A ratio of 2.0 means the keyword must have *at least doubled*. "
                     "Lower = more sensitive, higher = stricter.",
            )
        else:
            thr = st.slider(
                "Sensitivity threshold",
                1, 200, 10, key="burst_thr_d",
                help="Minimum point increase required. "
                     "Lower = catches small bumps, higher = only big jumps.",
            )

    bursts = detect_bursts(curr_freq, prev_freq, threshold=thr, method=method)

    st.divider()

    # Side-by-side windows
    left, right = st.columns(2)
    with left:
        st.markdown("##### Previous period")
        st.caption("Baseline popularity for each keyword.")
        st.dataframe(
            pd.DataFrame(
                sorted(prev_freq.items(), key=lambda x: -x[1]),
                columns=["Keyword", "Previous interest"],
            ),
            use_container_width=True,
            hide_index=True,
            height=300,
        )
    with right:
        st.markdown("##### Current period")
        st.caption("Current popularity — compared against the previous to detect spikes.")
        st.dataframe(
            pd.DataFrame(
                sorted(curr_freq.items(), key=lambda x: -x[1]),
                columns=["Keyword", "Current interest"],
            ),
            use_container_width=True,
            hide_index=True,
            height=300,
        )

    st.divider()

    # Results
    st.markdown(f"##### Spikes detected")
    if bursts:
        st.caption(
            f"**{len(bursts)} keyword(s)** exceeded the {method} threshold of {thr}. "
            "Sorted by spike intensity — highest first."
        )
        rows = []
        for kw, score in bursts:
            prev_val = prev_freq.get(kw, 0)
            curr_val = curr_freq.get(kw, 0)
            row = {
                "Keyword": kw,
                "Previous": prev_val,
                "Current": curr_val,
                "Spike score": f"{score:.1f}",
                "Change": trend_direction_text(prev_val, curr_val),
            }
            if ground_truth is not None:
                row["Correctly detected?"] = "✅ Yes" if kw in ground_truth else "⚠️ False alarm"
            rows.append(row)
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info(
            "No keywords spiked above this threshold. "
            "Try lowering the sensitivity to catch smaller changes.",
            icon="ℹ️",
        )

    # Accuracy report for synthetic data
    if ground_truth is not None:
        st.divider()
        st.markdown("##### Detection accuracy")
        st.caption(
            "Since this is synthetic data with known spikes, we can measure how well the algorithm performed."
        )
        detected_kw = {k for k, _ in bursts}
        tp = len(detected_kw & ground_truth)
        fp = len(detected_kw - ground_truth)
        fn = len(ground_truth - detected_kw)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / len(ground_truth) if ground_truth else 0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Known spikes", len(ground_truth), help="Number of keywords with injected bursts.")
        c2.metric("Correctly found", tp, help="True positives — real spikes that were detected.")
        c3.metric(
            "False alarms", fp,
            help="Keywords flagged as spiking that actually weren't.",
        )
        c4.metric(
            "Missed", fn,
            help="Real spikes the algorithm didn't catch at this threshold.",
        )
        c5.metric(
            "Accuracy",
            f"{recall * 100:.0f}%",
            help="Percentage of real spikes detected (recall).",
        )

        if recall == 1.0 and fp == 0:
            st.success("Perfect score — all real spikes found with zero false alarms!", icon="🎯")
        elif recall == 1.0:
            st.warning(
                f"All spikes found, but {fp} false alarm(s). "
                "Raising the threshold would reduce false positives.",
                icon="⚠️",
            )
        elif fp == 0:
            st.warning(
                f"No false alarms, but missed {fn} spike(s). "
                "Lowering the threshold would catch more.",
                icon="⚠️",
            )


# ╔══════════════════════════════════════════════════════════════╗
# ║  TAB 6 — PERFORMANCE BENCHMARKS                             ║
# ╚══════════════════════════════════════════════════════════════╝

with tab_bench:
    st.markdown("### Pre-computed performance benchmarks")
    st.markdown(
        "These charts show how each algorithm scales as data grows. "
        "They were generated by running experiments on stream sizes from 1,000 to 100,000 events. "
        "The key question: **does real-world performance match the theoretical predictions?**"
    )

    if not os.path.exists(RESULTS_PATH):
        st.warning(
            "Benchmark data not found. Run `python experiments.py` to generate experiment_results.json.",
            icon="⚠️",
        )
    else:
        with open(RESULTS_PATH) as f:
            data = json.load(f)

        # ── Benchmark 1: Sliding Window ──
        st.divider()
        st.markdown("##### 1. Sliding window — how speed changes with data size")
        st.caption(
            "The naive method rescans all data on every update, so it gets dramatically slower as data grows. "
            "The smart method stays near-instant regardless of size."
        )
        sw = pd.DataFrame(data["sliding_window"])
        sw_display = sw.copy()
        sw_display.columns = ["Stream size", "Naive (seconds)", "Smart (seconds)"]
        st.line_chart(sw_display.set_index("Stream size"), height=300)

        # Key insight
        if len(sw) >= 2:
            worst_naive = sw["naive_time"].max()
            worst_smart = sw["smart_time"].max()
            st.info(
                f"At the largest test ({sw['n'].max():,} events): "
                f"Naive took **{worst_naive:.1f}s** vs Smart's **{worst_smart:.3f}s** — "
                f"a **{worst_naive / worst_smart:,.0f}x** difference.",
                icon="💡",
            )

        # ── Benchmark 2: Top-K ──
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### 2a. Top-K — more keywords (K fixed at 5)")
            st.caption(
                "As the total number of keywords grows, the heap method scales "
                "better because it only tracks the top 5, not all items."
            )
            tk_m = pd.DataFrame(data["top_k_vary_m"])
            tk_m_display = tk_m.rename(columns={
                "m": "Total keywords", "heap_time": "Heap (seconds)", "sort_time": "Sort (seconds)"
            })
            st.line_chart(tk_m_display.set_index("Total keywords"), height=280)

        with c2:
            st.markdown("##### 2b. Top-K — asking for more results (M fixed at 1,000)")
            st.caption(
                "As K approaches M, both methods converge — the heap loses its advantage "
                "because it ends up tracking nearly all items anyway."
            )
            tk_k = pd.DataFrame(data["top_k_vary_k"])
            tk_k_display = tk_k.rename(columns={
                "k": "K (results requested)", "heap_time": "Heap (seconds)", "sort_time": "Sort (seconds)"
            })
            st.line_chart(tk_k_display.set_index("K (results requested)"), height=280)

        # ── Benchmark 3: Burst Detection ──
        st.divider()
        st.markdown("##### 3. Spike detection — accuracy vs sensitivity")
        st.caption(
            "How does changing the threshold affect detection? Low threshold = catches more spikes but may false-alarm. "
            "High threshold = very precise but may miss real spikes."
        )

        b = data["burst_detection"]
        c3, c4 = st.columns(2)
        with c3:
            st.markdown("**Ratio method**")
            ratio_df = pd.DataFrame(b["ratio_results"]).rename(columns={
                "detection_rate": "Detection rate",
                "false_positive_rate": "False positive rate",
            })
            st.line_chart(ratio_df.set_index("threshold")[["Detection rate", "False positive rate"]], height=260)
            st.caption("Detection rate drops above threshold 5.0 — some real spikes are missed at high thresholds.")

        with c4:
            st.markdown("**Difference method**")
            diff_df = pd.DataFrame(b["difference_results"]).rename(columns={
                "detection_rate": "Detection rate",
                "false_positive_rate": "False positive rate",
            })
            st.line_chart(diff_df.set_index("threshold")[["Detection rate", "False positive rate"]], height=260)
            st.caption("More gradual decline — difference method is more robust to threshold changes.")

        # ── Benchmark 4: Pipeline ──
        if "pipeline" in data:
            st.divider()
            st.markdown("##### 4. Full pipeline — end-to-end processing time")
            st.caption(
                "How long does it take to run the complete system (window + ranking + spike detection + classification) "
                "as data grows?"
            )
            pl = pd.DataFrame(data["pipeline"])
            pl_display = pl.rename(columns={"n": "Events", "pipeline_time": "Total time (seconds)"})
            st.line_chart(pl_display.set_index("Events"), height=280)

            if len(pl) >= 2:
                st.info(
                    f"The full pipeline processes {pl['n'].max():,} events in just "
                    f"**{pl['pipeline_time'].max():.2f} seconds** — efficient enough for real-time use.",
                    icon="💡",
                )
