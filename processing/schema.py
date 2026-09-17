"""The event schema. Declared here and nowhere else; every script imports it.

The columns are the nine columns of data/raw/2019-Nov.csv, in file order. The
same schema reads the raw CSV (kata.py, load_bronze.py) and, from W40, the JSON
files the replayer writes (Structured Streaming cannot infer a schema).

Never let Spark guess the types with inferSchema:

- It scans the whole 9 GB file once more just to guess.
- It reads user_id as INT, because the largest id (579,969,851) fits in 32
  bits. Spark's hash() gives a different value for an INT than for a BIGINT, so
  the 7% sample in load_bronze.py becomes a different set of users: measured,
  only 18,150 users are shared with the BIGINT sample of about 258,000. The
  four machines would stop agreeing.
"""

from pyspark.sql.types import (
    DecimalType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

EVENT_SCHEMA = StructType([
    StructField("event_time", TimestampType()),     # 2019-11-01 00:00:00 UTC
    StructField("event_type", StringType()),        # view | cart | purchase (see note below)
    StructField("product_id", LongType()),          # 1003461
    StructField("category_id", LongType()),         # 2053013555631882655, needs 64 bits
    StructField("category_code", StringType()),     # electronics.smartphone; empty in the CSV, so NULL once read (32.4% of rows)
    StructField("brand", StringType()),             # xiaomi; empty in the CSV, so NULL once read (14.9% of rows)
    StructField("price", DecimalType(10, 2)),       # 489.07, same type as the star's numeric(10,2)
    StructField("user_id", LongType()),             # 520088904, must stay BIGINT: see the docstring
    StructField("user_session", StringType()),      # 4d3b30da-a5e4-49df-b1a8-ba5943f1dd33
])

# The dataset documents a fourth event type, remove_from_cart, but
# 2019-Nov.csv contains none: view 63,556,110 + cart 3,028,930 +
# purchase 916,939 = 67,501,979 rows.

# How event_time is written in the raw CSV: "2019-11-01 00:00:00 UTC".
# The trailing "z" reads the zone name, so the value is UTC no matter which
# time zone the machine is set to.
RAW_TIMESTAMP_FORMAT = "yyyy-MM-dd HH:mm:ss z"
