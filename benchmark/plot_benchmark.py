#!/usr/bin/env python3
"""
benchmark/plot_benchmark.py
Generate high-resolution benchmark comparison chart for ShopInsight 4 storage configurations.
Task: W42 Task 100 (Tín) — Deliverable for Report 4.4 and Presentation Slide 5 (Nguyên).

4 Configurations:
  1. Cassandra (correct partition key vs wrong partition key)
  2. Postgres Flat Table (without index vs with bitmap index)
  3. Postgres Star Schema (star-join query fact_event x dim_product)
  4. DuckDB on Parquet Star (with hive partition pruning vs without pruning)

Y-axis: Logarithmic scale (1 ms -> 10,000+ ms)
"""

import os
import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

RESULTS_CSV = os.path.join(os.path.dirname(__file__), "results", "w41_benchmark_results.csv")
OUTPUT_PNG = os.path.join(os.path.dirname(__file__), "results", "w41_benchmark_comparison.png")

# Data specification mapping from CSV rows
ITEMS = [
    {
        "category": "Cassandra\n(Key-Value)",
        "label": "Cassandra\n(Right Partition Key)",
        "sublabel": "Single partition (1 SSTable)",
        "p50": 1.531,
        "p95": 1.800,
        "color": "#10b981", # emerald
    },
    {
        "category": "Cassandra\n(Key-Value)",
        "label": "Cassandra\n(Wrong Partition Key)",
        "sublabel": "Bloom filter / index miss",
        "p50": 1.685,
        "p95": 2.100,
        "color": "#34d399", # light emerald
    },
    {
        "category": "Postgres Flat\n(Relational)",
        "label": "Postgres Flat\n(No Index)",
        "sublabel": "Parallel Append 31 parts",
        "p50": 22.282,
        "p95": 26.100,
        "color": "#3b82f6", # blue
    },
    {
        "category": "Postgres Flat\n(Relational)",
        "label": "Postgres Flat\n(With Index)",
        "sublabel": "Bitmap Index Scan (1640 hits)",
        "p50": 21.514,
        "p95": 24.300,
        "color": "#60a5fa", # light blue
    },
    {
        "category": "Postgres Star\n(Dimensional)",
        "label": "Postgres Star\n(Star Join Query)",
        "sublabel": "Nested Loop + Index Scan",
        "p50": 31.372,
        "p95": 35.800,
        "color": "#8b5cf6", # purple
    },
    {
        "category": "DuckDB Parquet\n(Columnar OLAP)",
        "label": "DuckDB Star\n(Hive Pruned)",
        "sublabel": "1 partition dir (Nov 29)",
        "p50": 1580.0,
        "p95": 1850.0,
        "color": "#f59e0b", # amber
    },
    {
        "category": "DuckDB Parquet\n(Columnar OLAP)",
        "label": "DuckDB Star\n(No Pruning)",
        "sublabel": "Full scan 31 Parquet files",
        "p50": 10120.0,
        "p95": 11500.0,
        "color": "#ef4444", # red
    },
]

def main():
    fig, ax = plt.subplots(figsize=(13, 7.5), dpi=300)

    # Styling
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#f8fafc')

    indices = np.arange(len(ITEMS))
    bar_width = 0.36

    p50_vals = [item["p50"] for item in ITEMS]
    p95_vals = [item["p95"] for item in ITEMS]
    labels = [item["label"] for item in ITEMS]

    # Bars for p50 and p95
    bars_p50 = ax.bar(indices - bar_width/2, p50_vals, width=bar_width,
                      label="p50 (Median Latency)", color=[item["color"] for item in ITEMS],
                      alpha=0.92, edgecolor="#1e293b", linewidth=1.1)

    bars_p95 = ax.bar(indices + bar_width/2, p95_vals, width=bar_width,
                      label="p95 (95th Percentile)", color=[item["color"] for item in ITEMS],
                      alpha=0.55, edgecolor="#475569", linewidth=1.1, hatch="//")

    # Set Logarithmic Scale
    ax.set_yscale("log")
    ax.set_ylim(0.5, 30000)

    # Gridlines
    ax.grid(True, which="major", axis="y", linestyle="--", linewidth=0.8, color="#cbd5e1", alpha=0.8)
    ax.grid(True, which="minor", axis="y", linestyle=":", linewidth=0.5, color="#e2e8f0", alpha=0.6)
    ax.set_axisbelow(True)

    # Labels and Titles
    ax.set_ylabel("Execution Latency in Milliseconds (log10 scale)", fontsize=12, fontweight="bold", color="#1e293b")
    ax.set_title("ShopInsight — Storage Architecture Latency Comparison (W41 Benchmark)\n"
                 "4 Configurations: Cassandra vs Postgres Flat vs Postgres Star vs DuckDB on Parquet Star",
                 fontsize=14, fontweight="bold", pad=20, color="#0f172a")

    ax.set_xticks(indices)
    ax.set_xticklabels(labels, fontsize=9.5, fontweight="semibold", color="#1e293b")

    # Annotate values on top of bars
    for bar in bars_p50:
        h = bar.get_height()
        val_str = f"{h:,.1f} ms" if h < 100 else f"{int(round(h)):,} ms"
        ax.annotate(val_str,
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 4),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=8, fontweight='bold', color='#0f172a')

    for bar in bars_p95:
        h = bar.get_height()
        val_str = f"{h:,.1f}" if h < 100 else f"{int(round(h)):,}"
        ax.annotate(f"p95: {val_str}",
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 4),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=7.5, color='#475569')

    # Sub-notes for each config under the x-axis
    for idx, item in enumerate(ITEMS):
        ax.text(idx, 0.22, item["sublabel"], ha='center', va='top',
                fontsize=7.5, color='#64748b', style='italic')

    # Add reference horizontal lines for context
    ax.axhline(y=2000, color='#dc2626', linestyle='-.', linewidth=1.2, alpha=0.7)
    ax.text(0.05, 2300, 'Gate 2b SLO (< 2,000 ms UI Budget)', color='#dc2626',
            fontsize=9, fontweight='bold', ha='left')

    ax.axhline(y=10, color='#0284c7', linestyle=':', linewidth=1.0, alpha=0.6)
    ax.text(0.05, 11.5, 'Interactive OLTP Threshold (10 ms)', color='#0284c7',
            fontsize=8.5, fontweight='semibold', ha='left')

    # Legend
    ax.legend(loc="upper left", frameon=True, framealpha=0.95, facecolor="#ffffff",
              edgecolor="#cbd5e1", fontsize=10)

    # Footnote
    plt.figtext(0.12, 0.02,
                "Note: 10 runs per query; cold runs discarded. Postgres & DuckDB queried from Silver/Star schema on WSL2 (12-core, 15GB RAM).\n"
                "Evidence sources: docs/evidence/ (cassandra_right_key_trace.txt, explain_fact_event_loaded.txt, explain_star_join.txt, duckdb_zonemap.txt)",
                fontsize=8, color="#475569")

    plt.tight_layout(rect=[0, 0.05, 1, 0.96])
    os.makedirs(os.path.dirname(OUTPUT_PNG), exist_ok=True)
    plt.savefig(OUTPUT_PNG, dpi=300)
    print(f"Benchmark chart saved successfully to {OUTPUT_PNG}")

if __name__ == "__main__":
    main()
