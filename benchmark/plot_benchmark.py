#!/usr/bin/env python3
"""Draw the storage benchmark chart for report 4.4 and slide 5 from measured numbers.

    python benchmark/plot_benchmark.py [--summary PATH]

Reads the newest benchmark/results/summary_*.csv, the file benchmark/run_benchmark.py
(task T12) writes, or the file given with --summary. The CSV has exactly these columns:

    system,query,variant,runs,p50_ms,p95_ms

and this script draws one bar per (system, query, variant) row: the bar is p50, the
whisker above it reaches p95, the y-axis is log scale, and the footnote states how many
timed runs each number comes from (the runs column). The chart is written to
benchmark/results/benchmark_comparison.png. No number is hardcoded here: if no summary
CSV exists the script prints what to run and exits 1.

matplotlib is an OPTIONAL plotting dependency. It is not in requirements.txt and must
not be added there (the pinned .venv only holds what the pipeline and API need). Install
it in a separate virtualenv and run this script from that one:

    python3.14 -m venv /path/to/plot-venv
    /path/to/plot-venv/bin/pip install matplotlib
    /path/to/plot-venv/bin/python benchmark/plot_benchmark.py

The script only uses the Python standard library besides matplotlib.
"""

import argparse
import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO / "benchmark" / "results"
OUTPUT_PNG = RESULTS_DIR / "benchmark_comparison.png"
COLUMNS = ["system", "query", "variant", "runs", "p50_ms", "p95_ms"]

# Categorical colours, assigned to systems in a fixed order (first appearance in the
# CSV), never by value. Text stays in the ink colours below, never in a series colour.
SYSTEM_COLOURS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
INK = "#1f1f1e"
INK_MUTED = "#6b6a63"
GRID = "#e4e3dd"


def newest_summary():
    """Return the newest benchmark/results/summary_*.csv, or None if there is none.

    The timestamp in the name sorts the same way as time, so the last name wins.
    """
    found = sorted(RESULTS_DIR.glob("summary_*.csv"))
    return found[-1] if found else None


def read_summary(path):
    """Read the summary CSV into a list of dicts with numeric runs, p50_ms and p95_ms."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != COLUMNS:
            sys.exit(f"{path}: expected columns {','.join(COLUMNS)}, "
                     f"found {','.join(reader.fieldnames or [])}")
        rows = []
        for row in reader:
            rows.append({
                "system": row["system"],
                "query": row["query"],
                "variant": row["variant"],
                "runs": int(row["runs"]),
                "p50_ms": float(row["p50_ms"]),
                "p95_ms": float(row["p95_ms"]),
            })
    if not rows:
        sys.exit(f"{path}: no data rows")
    return rows


def runs_footnote(rows, path):
    """Build the footnote from the runs column, e.g. '20 timed runs per bar'."""
    runs = sorted({row["runs"] for row in rows})
    if len(runs) == 1:
        count = f"{runs[0]} timed runs per bar"
    else:
        count = f"{runs[0]}-{runs[-1]} timed runs per bar (see the runs column)"
    source = path.relative_to(REPO) if path.is_relative_to(REPO) else path
    return f"Bar = p50, whisker = p95; {count}. Source: {source}"


def format_ms(value):
    """1.53 -> '1.5 ms', 1580 -> '1,580 ms'."""
    return f"{value:,.1f} ms" if value < 100 else f"{value:,.0f} ms"


def plot(rows, path, output):
    import matplotlib
    matplotlib.use("Agg")  # no display needed, write the PNG only
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    systems = []
    for row in rows:
        if row["system"] not in systems:
            systems.append(row["system"])
    if len(systems) > len(SYSTEM_COLOURS):
        sys.exit(f"{len(systems)} systems in {path}; the chart has colours for {len(SYSTEM_COLOURS)}")
    colour_of = {name: SYSTEM_COLOURS[i] for i, name in enumerate(systems)}

    fig, ax = plt.subplots(figsize=(max(8, 1.3 * len(rows) + 2), 6.5), dpi=200)
    xs = range(len(rows))
    p50 = [row["p50_ms"] for row in rows]
    p95 = [row["p95_ms"] for row in rows]

    ax.bar(xs, p50, width=0.6, color=[colour_of[r["system"]] for r in rows],
           edgecolor="white", linewidth=2, zorder=2)
    # Whisker from p50 up to p95, with a short cap at p95.
    ax.vlines(xs, p50, p95, color=INK, linewidth=1.5, zorder=3)
    ax.hlines(p95, [x - 0.12 for x in xs], [x + 0.12 for x in xs], color=INK, linewidth=1.5, zorder=3)

    for x, row in zip(xs, rows):
        ax.annotate("p50 " + format_ms(row["p50_ms"]), xy=(x, row["p95_ms"]), xytext=(0, 4),
                    textcoords="offset points", ha="center", va="bottom", fontsize=8, color=INK)

    ax.set_yscale("log")
    ax.set_ylim(min(p50) / 3, max(p95) * 4)
    ax.set_ylabel("Query latency, ms (log scale)", color=INK)
    ax.set_xticks(list(xs))
    ax.set_xticklabels([f"{r['system']}\n{r['query']}\n{r['variant']}" for r in rows],
                       fontsize=8, color=INK)
    ax.set_title("ShopInsight storage benchmark: p50 and p95 latency per query",
                 fontsize=12, color=INK, loc="left")
    ax.grid(True, which="major", axis="y", color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(colors=INK_MUTED)

    ax.legend(handles=[Patch(color=colour_of[s], label=s) for s in systems],
              loc="upper left", frameon=False, fontsize=9)
    fig.text(0.01, 0.01, runs_footnote(rows, path), fontsize=8, color=INK_MUTED)
    fig.tight_layout(rect=(0, 0.04, 1, 1))

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    print(f"Chart written to {output} ({len(rows)} bars from {path})")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--summary", type=Path,
                        help="summary CSV to plot (default: newest benchmark/results/summary_*.csv)")
    args = parser.parse_args()

    path = args.summary.resolve() if args.summary else newest_summary()
    if path is None or not path.is_file():
        where = args.summary if args.summary else RESULTS_DIR / "summary_*.csv"
        print(f"No benchmark summary found at {where}.\n"
              "Run benchmark/run_benchmark.py first (task T12); it writes "
              "benchmark/results/summary_<timestamp>.csv.")
        sys.exit(1)

    plot(read_summary(path), path, OUTPUT_PNG)


if __name__ == "__main__":
    main()
