"""Replayer: plays bronze back into data/stream_landing/ as if it were happening now.

    python processing/streaming_gold.py                  # terminal 1, FIRST: wait for READY
    python ingestion/replayer.py --speed 60              # terminal 2: 1 hour of events per minute
    python ingestion/replayer.py --speed 60 --start "2019-11-17 08:00:00"   # the demo: see below

Reads data/bronze/ in event_time order and every 5 seconds writes one JSON file
holding the next 5 x speed seconds of events. At --speed 60 that is 5 minutes of
events per file, about 550 rows on average (4,767,012 rows / 8,640 five-minute
slices = 552). The hour decides it: about 90 at 00:00 UTC, about 880 at
15:00-16:00 UTC. A whole-month replay at --speed 60 takes 12 hours; for a demo,
pick a --start and stop with Ctrl-C. --start is UTC, like bronze.
"2019-11-17 08:00:00" is 15:00 in Vietnam on the day with the most purchases
(13,076, against about 2,200 on an average day): about 2,000 rows per file.
Avoid 15 November: it has 432,575 events and not one purchase, so BR1 shows
GMV 0 all day.

START THE STREAMING JOB FIRST. Files that pile up in data/stream_landing/
before streaming_gold.py starts are all read by its first micro-batch, one
giant batch that looks nothing like real time.

Why bronze and never the raw CSV: bronze is the 7% user sample (258,390 users),
the raw file holds all 3,696,117. The stream has to see the same population as
the batch side, or the >= 99% correctness gate is out of reach by construction.
The stream cleans what it reads with batch_silver.clean(), so the replayer sends
bronze untouched: UTC times, nulls and non-positive prices included.

Four details that keep the stream correct:

- Spark writes the JSON (to_json), not Python. Timestamps come out as ISO 8601
  with their offset, "2019-11-01T00:00:02.000Z", which processing/source.py
  reads back with the default parser. A Python datetime would pick up the
  laptop's time zone on the way (see docs/STREAMING_PATTERN.md, Block 0).
- Each file is written under a hidden name (.tmp-...) and then renamed. Spark
  skips names that start with a dot, and a rename is atomic, so a micro-batch
  never reads a half-written file.
- File names are unique per run: <run start>-<sequence>.json. The streaming
  checkpoint remembers every path it has read, and a repeated name would be
  skipped without a word.
- event_date is not sent. clean() recomputes it from the Vietnam time.

Done when each file prints one line and the streaming job's log shows a
micro-batch per file. A full replay must end with REPLAY OK: every bronze row
sent exactly once. To check that in under a minute instead of 12 hours (53 s
measured on 20 cores), with the streaming job NOT running:
python ingestion/replayer.py --speed 100000
then start the next demo with streaming_gold.py --fresh, which clears those files.
"""

import argparse
import itertools
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# The same three lines open every Spark script in this repo (see processing/kata.py).
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))  # lets `python ingestion/replayer.py` import processing.*
os.environ["SPARK_CONF_DIR"] = str(REPO / "conf")  # driver memory + UTC, before the JVM starts

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from processing.schema import EVENT_SCHEMA
from processing.source import LANDING_DIR

BRONZE_DIR = REPO / "data" / "bronze"
BRONZE_ROWS = 4_767_012                 # load_bronze.py's count; a full replay sends each once
FILE_EVERY_SECONDS = 5                  # wall-clock seconds between two files
VIETNAM = timezone(timedelta(hours=7))  # only for the log line; the stream does its own shift


def parse_args():
    parser = argparse.ArgumentParser(description="Replay bronze into data/stream_landing/.")
    parser.add_argument("--speed", type=int, default=60,
                        help="event seconds per wall-clock second (default 60: 1 hour per minute)")
    parser.add_argument("--start", default=None,
                        help='first event time to send, UTC as in bronze, e.g. "2019-11-29 00:00:00" '
                             "(default: the first event)")
    args = parser.parse_args()
    if args.speed < 1:
        parser.error("--speed must be 1 or more")
    return args


def first_second(bronze, start):
    """Unix seconds of --start (read as UTC), or of the first event in bronze."""
    if start is not None:
        return int(datetime.fromisoformat(start).replace(tzinfo=timezone.utc).timestamp())
    return bronze.agg(F.unix_seconds(F.min("event_time"))).first()[0]


def events_in_order(bronze, origin, slice_seconds):
    """Bronze sorted by event_time, as (slice, line) pairs.

    slice is the number of the file a row goes into: 0 for the first
    slice_seconds of events after origin, 1 for the next, and so on.
    line is the row as one JSON object, EVENT_SCHEMA's nine columns.
    """
    return (
        bronze
        .orderBy("event_time")
        .select(
            F.floor((F.unix_seconds("event_time") - origin) / slice_seconds).alias("slice"),
            F.to_json(F.struct(*EVENT_SCHEMA.fieldNames())).alias("line"),
        )
    )


def write_file(name, lines):
    """Write under a hidden name, then rename: Spark sees the whole file or nothing."""
    tmp = LANDING_DIR / f".tmp-{name}"
    tmp.write_text("\n".join(lines) + "\n")
    os.replace(tmp, LANDING_DIR / name)


def main():
    args = parse_args()
    if not list(BRONZE_DIR.glob("event_date=*")):
        sys.exit(f"{BRONZE_DIR} is empty. Run python ingestion/load_bronze.py first.")
    LANDING_DIR.mkdir(parents=True, exist_ok=True)

    spark = (
        SparkSession.builder.master("local[*]").appName("replayer")
        .config("spark.ui.showConsoleProgress", "false")   # keep the log one line per file
        .getOrCreate()
    )
    bronze = spark.read.parquet(str(BRONZE_DIR))
    if args.start is not None:
        bronze = bronze.where(F.col("event_time") >= F.lit(args.start).cast("timestamp"))

    slice_seconds = FILE_EVERY_SECONDS * args.speed
    start_second = first_second(bronze, args.start)
    if start_second is None:
        sys.exit(f"No bronze events at or after {args.start}.")
    # Round down to a whole slice so the files cover round times: 00:00-00:05, 00:05-00:10.
    origin = start_second - start_second % slice_seconds
    run = time.strftime("%Y%m%d-%H%M%S")

    print(f"replaying {BRONZE_DIR} -> {LANDING_DIR}")
    print(f"speed {args.speed}: one file every {FILE_EVERY_SECONDS} s, "
          f"{slice_seconds:,} s of events per file")
    print("streaming_gold.py must already be running and READY. Ctrl-C stops the replay.")

    files = rows = 0
    started = time.monotonic()
    wall_zero = first_slice = None
    stopped = False
    try:
        # toLocalIterator hands the sorted rows to Python one partition at a
        # time, so the whole month never sits in memory at once. The rows arrive
        # sorted, so groupby() sees each slice as one run of consecutive rows.
        ordered = events_in_order(bronze, origin, slice_seconds).toLocalIterator(prefetchPartitions=True)
        for slice_number, group in itertools.groupby(ordered, key=lambda row: row.slice):
            lines = [row.line for row in group]
            if wall_zero is None:
                # The clock starts when the first rows arrive, not before the sort,
                # so the first files are not written back to back.
                wall_zero, first_slice = time.monotonic(), slice_number
            # Slice k goes out once its 5 seconds are over. A slice with no events
            # writes no file, but the clock still moves past it.
            due = wall_zero + (slice_number - first_slice + 1) * FILE_EVERY_SECONDS
            time.sleep(max(0.0, due - time.monotonic()))   # a late file goes out at once
            files += 1
            rows += len(lines)
            write_file(f"{run}-{files:06d}.json", lines)
            begin = datetime.fromtimestamp(origin + slice_number * slice_seconds, timezone.utc)
            end = begin + timedelta(seconds=slice_seconds)
            print(f"file {files:06d}  {begin:%Y-%m-%d %H:%M} .. {end:%H:%M} UTC"
                  f"  (Vietnam {begin.astimezone(VIETNAM):%m-%d %H:%M})"
                  f"  {len(lines):>6,} rows  total {rows:,}", flush=True)
    except KeyboardInterrupt:
        stopped = True
    finally:
        for tmp in LANDING_DIR.glob(".tmp-*"):  # a file cut off by Ctrl-C is never renamed in
            tmp.unlink()
        spark.stop()

    print(f"{files:,} files, {rows:,} rows in {time.monotonic() - started:,.0f} s")
    if stopped:
        print("REPLAY STOPPED by Ctrl-C")
    elif args.start is None and rows != BRONZE_ROWS:
        print(f"REPLAY CHECK FAILED: sent {rows:,} rows, bronze has {BRONZE_ROWS:,}")
        sys.exit(1)
    elif args.start is None:
        print(f"REPLAY OK: all {BRONZE_ROWS:,} bronze rows sent exactly once")
    else:
        print(f"REPLAY OK: every bronze row from {args.start} UTC on")


if __name__ == "__main__":
    main()
