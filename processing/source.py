"""The stream's source reader. Every streaming job reads its events through here.

    from processing.source import read_events
    events = read_events(spark)       # a streaming DataFrame, EVENT_SCHEMA columns

Today the source is a directory of JSON files: ingestion/replayer.py writes one
file into data/stream_landing/ every 5 seconds and Spark picks each new file up
in its next micro-batch. The Kafka swap (a W44 option behind a gate, PLAN.md)
changes the body of read_events() and nothing else in processing/ - which is
the reason this function lives in its own file. The replayer changes too, since
it would produce to a topic instead of writing files.

Three choices below, each one load-bearing:

- .schema(EVENT_SCHEMA). Structured Streaming cannot infer a schema: without it
  the query refuses to start. The schema is declared once, in processing/schema.py.
- No timestampFormat option. The replayer lets Spark write the JSON (to_json),
  which renders event_time as ISO 8601 with its offset, "2019-11-01T00:00:02.000Z",
  and the reader's default parser reads exactly that back. Nothing depends on the
  laptop's time zone.
- mode FAILFAST, as in load_bronze.py. Under the default PERMISSIVE mode a line
  that does not parse becomes nulls, and clean() does not drop a null
  event_time: it would reach the window as null and fail later, far from the
  cause. FAILFAST stops the query on the bad file itself.
"""

from pathlib import Path

from processing.schema import EVENT_SCHEMA

REPO = Path(__file__).resolve().parents[1]
LANDING_DIR = REPO / "data" / "stream_landing"   # the replayer writes here, the jobs read here


def read_events(spark):
    """The raw event stream: EVENT_SCHEMA's nine columns, times still in UTC.

    Every writeStream started on this DataFrame gets its own source and reads
    the whole directory on its own, so the four jobs never share progress -
    each keeps it in its own checkpoint.
    """
    return (
        spark.readStream
        .format("json")
        .schema(EVENT_SCHEMA)          # never inferred: see the docstring above
        .option("mode", "FAILFAST")    # a bad line stops the query, never becomes nulls
        .load(str(LANDING_DIR))
    )
