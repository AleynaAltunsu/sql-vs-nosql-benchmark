"""
analysis.py
───────────
Loads benchmark JSON results and generates publication-quality charts.

Usage:
    python analysis/analysis.py
    python analysis/analysis.py --result benchmarks/results/benchmark_20240101_120000.json
"""

import argparse
import glob
import json
import os
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# ─────────────────────────────────────────────
# Style — clean, dark technical aesthetic
# ─────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor": "#0d1117",
    "axes.facecolor":   "#161b22",
    "axes.edgecolor":   "#30363d",
    "axes.labelcolor":  "#c9d1d9",
    "axes.titlecolor":  "#f0f6fc",
    "xtick.color":      "#8b949e",
    "ytick.color":      "#8b949e",
    "text.color":       "#c9d1d9",
    "grid.color":       "#21262d",
    "grid.linewidth":   0.6,
    "font.family":      "monospace",
    "font.size":        10,
})

PG_COLOR    = "#336791"   # PostgreSQL blue
MONGO_COLOR = "#47A248"   # MongoDB green
PLOT_DIR    = "analysis/plots"

OPERATION_LABELS = {
    "insert_1000":        "Insert 1K",
    "point_lookup":       "Point Lookup",
    "filtered_search":    "Filtered Search",
    "aggregation":        "Aggregation",
    "multi_join":         "JOIN / $lookup",
    "fulltext_search":    "Full-text Search",
    "conditional_update": "Cond. Update",
    "bulk_delete":        "Bulk Delete",
}


def load_latest_result(result_path: str | None) -> dict:
    if result_path:
        with open(result_path) as f:
            return json.load(f)
    files = sorted(glob.glob("benchmarks/results/benchmark_*.json"))
    if not files:
        raise FileNotFoundError("No benchmark results found. Run benchmark_runner.py first.")
    with open(files[-1]) as f:
        return json.load(f)


def extract_medians(data: dict, db_key: str) -> dict:
    return {
        k: v["median_ms"]
        for k, v in data[db_key].items()
        if "median_ms" in v
    }


# ─────────────────────────────────────────────
# Chart 1: Grouped bar chart — all operations
# ─────────────────────────────────────────────
def plot_grouped_bars(pg: dict, mg: dict, title: str):
    ops   = list(OPERATION_LABELS.keys())
    labels = [OPERATION_LABELS[o] for o in ops]
    pg_vals = [pg.get(o, 0) for o in ops]
    mg_vals = [mg.get(o, 0) for o in ops]

    x = np.arange(len(ops))
    width = 0.38

    fig, ax = plt.subplots(figsize=(13, 6))
    ax.set_facecolor("#161b22")
    fig.patch.set_facecolor("#0d1117")

    bars_pg = ax.bar(x - width/2, pg_vals, width, label="PostgreSQL", color=PG_COLOR,
                     edgecolor="#1f6feb", linewidth=0.7, alpha=0.92)
    bars_mg = ax.bar(x + width/2, mg_vals, width, label="MongoDB", color=MONGO_COLOR,
                     edgecolor="#2ea043", linewidth=0.7, alpha=0.92)

    # Value labels on top of bars
    for bar in [*bars_pg, *bars_mg]:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2., h + 0.5,
                f"{h:.1f}", ha="center", va="bottom", fontsize=7.5, color="#c9d1d9")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha="right", fontsize=9)
    ax.set_ylabel("Median latency (ms)", labelpad=8)
    ax.set_title(f"{title}\nMedian latency per operation — lower is better",
                 fontsize=12, pad=14, color="#f0f6fc")
    ax.legend(loc="upper right", framealpha=0.3, facecolor="#161b22",
              edgecolor="#30363d", fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    ax.spines[:].set_visible(False)

    plt.tight_layout()
    path = f"{PLOT_DIR}/01_grouped_bars.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    print(f"  Saved: {path}")
    plt.close()


# ─────────────────────────────────────────────
# Chart 2: Horizontal bar — speedup ratio
# ─────────────────────────────────────────────
def plot_speedup_ratio(pg: dict, mg: dict):
    ops = list(OPERATION_LABELS.keys())
    labels = [OPERATION_LABELS[o] for o in ops]
    # ratio > 1 means MongoDB is faster; < 1 means PostgreSQL is faster
    ratios = [pg.get(o, 1) / max(mg.get(o, 1), 0.001) for o in ops]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor("#161b22")
    fig.patch.set_facecolor("#0d1117")

    colors = [MONGO_COLOR if r >= 1 else PG_COLOR for r in ratios]
    y = np.arange(len(ops))
    bars = ax.barh(y, ratios, color=colors, alpha=0.88, edgecolor="#21262d", linewidth=0.5)

    ax.axvline(1.0, color="#f0f6fc", linewidth=1.2, linestyle="--", alpha=0.6, label="Equal performance")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Speedup ratio  (PG latency / Mongo latency)\nValues > 1 → MongoDB faster | Values < 1 → PostgreSQL faster")
    ax.set_title("Performance Ratio: PostgreSQL vs MongoDB", fontsize=12, pad=12, color="#f0f6fc")
    ax.legend(fontsize=8, framealpha=0.2, facecolor="#161b22", edgecolor="#30363d")
    ax.grid(axis="x", alpha=0.25)
    ax.spines[:].set_visible(False)

    # Value annotations
    for bar, r in zip(bars, ratios):
        ax.text(r + 0.02, bar.get_y() + bar.get_height() / 2,
                f"{r:.2f}×", va="center", fontsize=8, color="#c9d1d9")

    plt.tight_layout()
    path = f"{PLOT_DIR}/02_speedup_ratio.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    print(f"  Saved: {path}")
    plt.close()


# ─────────────────────────────────────────────
# Chart 3: Radar / spider chart
# ─────────────────────────────────────────────
def plot_radar(pg: dict, mg: dict):
    ops = list(OPERATION_LABELS.keys())
    labels = [OPERATION_LABELS[o] for o in ops]
    N = len(ops)

    # Normalize: 1 = fastest observed for that operation
    pg_vals = np.array([pg.get(o, 1) for o in ops], dtype=float)
    mg_vals = np.array([mg.get(o, 1) for o in ops], dtype=float)
    max_vals = np.maximum(pg_vals, mg_vals)
    # Invert so higher value = better performance on radar
    pg_norm = 1 - (pg_vals / (max_vals + 1e-9)) * 0.9
    mg_norm = 1 - (mg_vals / (max_vals + 1e-9)) * 0.9

    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    pg_norm = np.concatenate([pg_norm, [pg_norm[0]]])
    mg_norm = np.concatenate([mg_norm, [mg_norm[0]]])
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw={"polar": True})
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    ax.plot(angles, pg_norm, color=PG_COLOR, linewidth=2, label="PostgreSQL")
    ax.fill(angles, pg_norm, color=PG_COLOR, alpha=0.25)
    ax.plot(angles, mg_norm, color=MONGO_COLOR, linewidth=2, label="MongoDB")
    ax.fill(angles, mg_norm, color=MONGO_COLOR, alpha=0.25)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=8, color="#c9d1d9")
    ax.set_yticklabels([])
    ax.grid(color="#30363d", linewidth=0.5)
    ax.spines["polar"].set_visible(False)
    ax.set_title("Performance Radar\n(higher = faster)", y=1.10, fontsize=12, color="#f0f6fc")
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.15),
              framealpha=0.3, facecolor="#161b22", edgecolor="#30363d", fontsize=9)

    plt.tight_layout()
    path = f"{PLOT_DIR}/03_radar.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    print(f"  Saved: {path}")
    plt.close()


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=str, default=None, help="Path to a specific result JSON")
    args = parser.parse_args()

    Path(PLOT_DIR).mkdir(parents=True, exist_ok=True)

    data = load_latest_result(args.result)
    timestamp = data.get("timestamp", "unknown")
    runs = data.get("runs_per_operation", "?")

    pg = extract_medians(data, "postgresql")
    mg = extract_medians(data, "mongodb")

    print(f"\n📈 Generating analysis charts (benchmark: {timestamp}, {runs} runs)...\n")

    plot_grouped_bars(pg, mg, f"SQL vs NoSQL Benchmark — {timestamp}")
    plot_speedup_ratio(pg, mg)
    plot_radar(pg, mg)

    print(f"\n✅ All charts saved to {PLOT_DIR}/")
