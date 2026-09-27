"""Postgres star loader: the three small dimensions into the PostgreSQL star schema.

    python serving/load_star_postgres.py [--database NAME]

W39 scope: build three small dimensions from Python rows, because no Parquet star
exists yet, and upsert them into Postgres:
    - dim_date          (92 rows, 2019-10-01 to 2019-12-31)
    - dim_event_type    (5 rows: view, cart, purchase, remove_from_cart, unknown)
    - dim_warehouse     (5 rows: warehouse IDs 1-5)

Later (not yet): once processing/batch_warehouse.py - the Spark build,
SYSTEM_DESIGN.md 5.6 - lands, these rows move there, and this script switches to
reading the star Parquet in data/warehouse/ and loading every table from it
(SYSTEM_DESIGN.md section 10: "Star Parquet -> Postgres"):
    - dim_product SCD2
    - dim_user SCD2
    - fact_event
    - fact_session_funnel
    - fact_inventory_daily

Prerequisites:
    1. PostgreSQL running: docker compose up -d --wait postgres
    2. warehouse/ddl.sql applied to that database (the command is in its header)
    3. seed/holidays_2019.csv present in the repo (tracked by git, NOT in data/)

Connection: host, port, user, password and database come from read_env() in
serving/check_infra.py - .env.example, overridden by .env. Shell environment
variables are ignored, so PG_DSN=... does nothing. That is why --database exists:
point it at a scratch database to try a load without touching shopinsight.

Done when: 3 dimensions loaded, the GIN index on dim_product.attributes and the
fact partitions exist, all checks pass. Prints POSTGRES STAR OK at end.

Design decisions:
    - Uses psycopg2 directly, no ORM, no SQLAlchemy (CLAUDE.md hard rule 1).
    - Upsert via INSERT ... ON CONFLICT DO UPDATE so reruns are idempotent.
    - seed/holidays_2019.csv goes through git so all four machines agree on
      is_holiday values (SYSTEM_DESIGN.md 3.2).
    - date_key is INTEGER yyyymmdd for fast range scans without casting.
    - day_of_week follows ISO 8601: Monday=1, Sunday=7.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))  # lets `python serving/load_star_postgres.py` import serving.check_infra

import psycopg2
import psycopg2.extras

from serving.check_infra import GIN_OPCLASS, read_env

HOLIDAYS_CSV = REPO / "seed" / "holidays_2019.csv"

# ── dim_date ─────────────────────────────────────────────────────────────────
# Covers the full October–December 2019 window used by all fact tables.
DIM_DATE_START = date(2019, 10, 1)
DIM_DATE_END = date(2019, 12, 31)
DIM_DATE_EXPECTED_ROWS = 92   # exactly 92 days inclusive

MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}

# Keyed on the ISO weekday, not strftime("%A"), which follows the machine's locale.
DAY_NAMES = {
    1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday",
    5: "Friday", 6: "Saturday", 7: "Sunday",
}

# The four values SYSTEM_DESIGN.md 3.2 allows in seed/holidays_2019.csv.
HOLIDAY_TYPES = ("public_holiday", "retail_event", "promo_period", "observance")


def load_holidays() -> dict[date, tuple[str, str]]:
    """Load seed/holidays_2019.csv.

    Returns a dict mapping holiday_date (datetime.date) to
    (holiday_name, holiday_type). Raises FileNotFoundError early
    so the whole script fails with a clear message instead of producing
    a dim_date with no holidays, and exits on a holiday_type outside
    HOLIDAY_TYPES.
    """
    if not HOLIDAYS_CSV.exists():
        raise FileNotFoundError(
            f"{HOLIDAYS_CSV} not found. "
            "This file must be tracked by git (NOT in data/). "
            "Run: git add seed/holidays_2019.csv"
        )
    holidays: dict[date, tuple[str, str]] = {}
    with open(HOLIDAYS_CSV, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            d = date.fromisoformat(row["holiday_date"].strip())
            h_type = row["holiday_type"].strip()
            if h_type not in HOLIDAY_TYPES:
                sys.exit(
                    f"{HOLIDAYS_CSV}: {d} has holiday_type {h_type!r}, "
                    f"expected one of {', '.join(HOLIDAY_TYPES)} (SYSTEM_DESIGN.md 3.2)."
                )
            holidays[d] = (row["holiday_name"].strip(), h_type)
    return holidays


def build_dim_date_rows() -> list[dict]:
    """Generate one dict per day from DIM_DATE_START to DIM_DATE_END inclusive."""
    holidays = load_holidays()
    rows = []
    current = DIM_DATE_START
    while current <= DIM_DATE_END:
        h_name, h_type = holidays.get(current, (None, None))
        quarter = (current.month - 1) // 3 + 1
        iso_cal = current.isocalendar()   # (ISO year, ISO week, ISO weekday)
        rows.append({
            "date_key": int(current.strftime("%Y%m%d")),
            "full_date": current,
            "year": current.year,
            "quarter": quarter,
            "month": current.month,
            "month_name": MONTH_NAMES[current.month],
            "day_of_month": current.day,
            "day_of_week": iso_cal[2],          # ISO: Mon=1 … Sun=7
            "day_name": DAY_NAMES[iso_cal[2]],
            "iso_week": iso_cal[1],
            "is_weekend": iso_cal[2] >= 6,      # Saturday=6, Sunday=7
            "is_holiday": h_name is not None,   # RULE: is_holiday ⟺ holiday_name IS NOT NULL (ck_dim_date_holiday)
            "holiday_name": h_name,
            "holiday_type": h_type,
        })
        current += timedelta(days=1)
    return rows


def upsert_dim_date(conn) -> int:
    """Upsert dim_date rows. Returns number of rows inserted/updated."""
    rows = build_dim_date_rows()
    if len(rows) != DIM_DATE_EXPECTED_ROWS:
        raise AssertionError(
            f"dim_date has {len(rows)} rows, expected {DIM_DATE_EXPECTED_ROWS}. "
            f"Check DIM_DATE_START={DIM_DATE_START} and DIM_DATE_END={DIM_DATE_END}."
        )
    sql = """
        INSERT INTO dim_date (
            date_key, full_date, year, quarter, month, month_name,
            day_of_month, day_of_week, day_name, iso_week, is_weekend,
            is_holiday, holiday_name, holiday_type
        )
        VALUES (
            %(date_key)s, %(full_date)s, %(year)s, %(quarter)s,
            %(month)s, %(month_name)s, %(day_of_month)s, %(day_of_week)s,
            %(day_name)s, %(iso_week)s, %(is_weekend)s,
            %(is_holiday)s, %(holiday_name)s, %(holiday_type)s
        )
        ON CONFLICT (date_key) DO UPDATE SET
            full_date    = EXCLUDED.full_date,
            year         = EXCLUDED.year,
            quarter      = EXCLUDED.quarter,
            month        = EXCLUDED.month,
            month_name   = EXCLUDED.month_name,
            day_of_month = EXCLUDED.day_of_month,
            day_of_week  = EXCLUDED.day_of_week,
            day_name     = EXCLUDED.day_name,
            iso_week     = EXCLUDED.iso_week,
            is_weekend   = EXCLUDED.is_weekend,
            is_holiday   = EXCLUDED.is_holiday,
            holiday_name = EXCLUDED.holiday_name,
            holiday_type = EXCLUDED.holiday_type
    """
    with conn.cursor() as cur:
        psycopg2.extras.execute_batch(cur, sql, rows, page_size=100)
    conn.commit()
    return len(rows)


# ── dim_event_type ───────────────────────────────────────────────────────────
# Copied from SYSTEM_DESIGN.md 5.4's INSERT INTO dim_event_type; change both together.
# 5 rows total including an unknown sentinel with key -1.
# stage_rank: view=1, cart=2, purchase=3, remove_from_cart=9, unknown=99 (not funnel stages)
DIM_EVENT_TYPE_ROWS = [
    {
        "event_type_key": 1,
        "event_type_code": "view",
        "event_type_name": "Viewed",
        "stage_rank": 1,
        "is_funnel_stage": True,
        "is_conversion": False,
        "cart_value_sign": 0,
    },
    {
        "event_type_key": 2,
        "event_type_code": "cart",
        "event_type_name": "Added to cart",
        "stage_rank": 2,
        "is_funnel_stage": True,
        "is_conversion": False,
        "cart_value_sign": 1,     # +1: adds value to cart
    },
    {
        "event_type_key": 3,
        "event_type_code": "purchase",
        "event_type_name": "Purchased",
        "stage_rank": 3,
        "is_funnel_stage": True,
        "is_conversion": True,    # the one definition of "an order"
        "cart_value_sign": 0,
    },
    {
        "event_type_key": 4,
        "event_type_code": "remove_from_cart",
        "event_type_name": "Removed from cart",
        "stage_rank": 9,
        "is_funnel_stage": False,
        "is_conversion": False,
        "cart_value_sign": -1,    # -1: removes value from cart
    },
    {
        "event_type_key": -1,
        "event_type_code": "unknown",
        "event_type_name": "Unknown",
        "stage_rank": 99,
        "is_funnel_stage": False,
        "is_conversion": False,
        "cart_value_sign": 0,
    },
]


def upsert_dim_event_type(conn) -> int:
    sql = """
        INSERT INTO dim_event_type (
            event_type_key, event_type_code, event_type_name,
            stage_rank, is_funnel_stage, is_conversion, cart_value_sign
        )
        VALUES (
            %(event_type_key)s, %(event_type_code)s, %(event_type_name)s,
            %(stage_rank)s, %(is_funnel_stage)s, %(is_conversion)s, %(cart_value_sign)s
        )
        ON CONFLICT (event_type_key) DO UPDATE SET
            event_type_code = EXCLUDED.event_type_code,
            event_type_name = EXCLUDED.event_type_name,
            stage_rank      = EXCLUDED.stage_rank,
            is_funnel_stage = EXCLUDED.is_funnel_stage,
            is_conversion   = EXCLUDED.is_conversion,
            cart_value_sign = EXCLUDED.cart_value_sign
    """
    with conn.cursor() as cur:
        psycopg2.extras.execute_batch(cur, sql, DIM_EVENT_TYPE_ROWS)
    conn.commit()
    return len(DIM_EVENT_TYPE_ROWS)


# ── dim_warehouse ─────────────────────────────────────────────────────────────
# 5 fictional warehouses across Vietnam regions.
# warehouse_key: the surrogate key, equal to warehouse_id for these five rows.
# warehouse_type: central | regional | fulfilment_partner (SYSTEM_DESIGN.md 5.4).
# lead_time_days: typical replenishment lead time from supplier.
# capacity_units: maximum stock-keeping units the warehouse can hold.
# All five are active: ingestion/gen_inventory.py (branch w39-khang-warehouse)
# sends every purchase to warehouse 1 + pmod(xxhash64(user_id), 5), so
# warehouse 5 gets about a fifth of them.
DIM_WAREHOUSE_ROWS = [
    {
        "warehouse_key": 1,
        "warehouse_id": 1,
        "warehouse_code": "HAN-01",
        "warehouse_name": "Hanoi Central",
        "region": "North",
        "city": "Hanoi",
        "warehouse_type": "central",
        "lead_time_days": 2,
        "capacity_units": 50000,
        "is_active": True,
    },
    {
        "warehouse_key": 2,
        "warehouse_id": 2,
        "warehouse_code": "SGN-01",
        "warehouse_name": "Ho Chi Minh South",
        "region": "South",
        "city": "Ho Chi Minh City",
        "warehouse_type": "central",
        "lead_time_days": 2,
        "capacity_units": 80000,
        "is_active": True,
    },
    {
        "warehouse_key": 3,
        "warehouse_id": 3,
        "warehouse_code": "DAD-01",
        "warehouse_name": "Da Nang Central Hub",
        "region": "Central",
        "city": "Da Nang",
        "warehouse_type": "regional",
        "lead_time_days": 3,
        "capacity_units": 30000,
        "is_active": True,
    },
    {
        "warehouse_key": 4,
        "warehouse_id": 4,
        "warehouse_code": "VCA-01",
        "warehouse_name": "Can Tho Mekong",
        "region": "Mekong Delta",
        "city": "Can Tho",
        "warehouse_type": "regional",
        "lead_time_days": 4,
        "capacity_units": 20000,
        "is_active": True,
    },
    {
        "warehouse_key": 5,
        "warehouse_id": 5,
        "warehouse_code": "HPH-01",
        "warehouse_name": "Hai Phong Port",
        "region": "North",
        "city": "Hai Phong",
        "warehouse_type": "fulfilment_partner",
        "lead_time_days": 3,
        "capacity_units": 40000,
        "is_active": True,
    },
]


def upsert_dim_warehouse(conn) -> int:
    sql = """
        INSERT INTO dim_warehouse (
            warehouse_key, warehouse_id, warehouse_code, warehouse_name,
            city, region, warehouse_type,
            lead_time_days, capacity_units, is_active
        )
        VALUES (
            %(warehouse_key)s, %(warehouse_id)s, %(warehouse_code)s, %(warehouse_name)s,
            %(city)s, %(region)s, %(warehouse_type)s,
            %(lead_time_days)s, %(capacity_units)s, %(is_active)s
        )
        ON CONFLICT (warehouse_key) DO UPDATE SET
            warehouse_id   = EXCLUDED.warehouse_id,
            warehouse_code = EXCLUDED.warehouse_code,
            warehouse_name = EXCLUDED.warehouse_name,
            city           = EXCLUDED.city,
            region         = EXCLUDED.region,
            warehouse_type = EXCLUDED.warehouse_type,
            lead_time_days = EXCLUDED.lead_time_days,
            capacity_units = EXCLUDED.capacity_units,
            is_active      = EXCLUDED.is_active
    """
    with conn.cursor() as cur:
        psycopg2.extras.execute_batch(cur, sql, DIM_WAREHOUSE_ROWS)
    conn.commit()
    return len(DIM_WAREHOUSE_ROWS)


# ── Verification ──────────────────────────────────────────────────────────────

# Child tables per partitioned fact: warehouse/ddl.sql creates 31 days + DEFAULT
# for the two date-partitioned facts and one partition per warehouse for inventory.
EXPECTED_PARTITIONS = {
    "fact_event": 32,
    "fact_inventory_daily": 5,
    "fact_session_funnel": 32,
}


def verify(conn) -> bool:
    """Read back counts and spot-check business rules. Returns True if all pass."""
    ok = True
    with conn.cursor() as cur:
        # dim_date: count and check 29/11 is_holiday
        cur.execute("SELECT COUNT(*) FROM dim_date")
        n_date = cur.fetchone()[0]
        ok_date = n_date == DIM_DATE_EXPECTED_ROWS
        print(f"dim_date rows        {n_date:>6}  (expect {DIM_DATE_EXPECTED_ROWS})  {'OK' if ok_date else 'FAIL'}")
        ok = ok and ok_date

        cur.execute(
            "SELECT is_holiday, holiday_name FROM dim_date WHERE date_key = 20191129"
        )
        row = cur.fetchone()
        if row is None:
            print("dim_date 2019-11-29  NOT FOUND  FAIL")
            ok = False
        else:
            bfriday_ok = row[0] is True and row[1] == "Black Friday"
            print(
                f"dim_date 2019-11-29  is_holiday={row[0]} name={row[1]!r}"
                f"  {'OK' if bfriday_ok else 'FAIL'}"
            )
            ok = ok and bfriday_ok

        # Every seed row must land in dim_date: a date outside 2019-10-01..12-31
        # would be dropped without a word.
        cur.execute("SELECT COUNT(*) FROM dim_date WHERE is_holiday")
        n_hol = cur.fetchone()[0]
        n_seed = len(load_holidays())
        ok_hol = n_hol == n_seed
        print(
            f"dim_date holidays    {n_hol:>6}  (expect {n_seed}: seed/holidays_2019.csv)  "
            f"{'OK' if ok_hol else 'FAIL'}"
        )
        ok = ok and ok_hol

        # dim_event_type: exactly 5 rows
        cur.execute("SELECT COUNT(*) FROM dim_event_type")
        n_et = cur.fetchone()[0]
        ok_et = n_et == 5
        print(f"dim_event_type rows  {n_et:>6}  (expect 5)  {'OK' if ok_et else 'FAIL'}")
        ok = ok and ok_et

        # dim_warehouse: exactly 5 rows
        cur.execute("SELECT COUNT(*) FROM dim_warehouse")
        n_wh = cur.fetchone()[0]
        ok_wh = n_wh == 5
        print(f"dim_warehouse rows   {n_wh:>6}  (expect 5)  {'OK' if ok_wh else 'FAIL'}")
        ok = ok and ok_wh

        # GIN index on dim_product.attributes must exist, with the operator
        # class check_infra.py proved the server has.
        cur.execute(
            "SELECT indexdef FROM pg_indexes WHERE indexname = 'ix_dim_product_attrs'"
        )
        row = cur.fetchone()
        gin_ok = row is not None and f"USING gin (attributes {GIN_OPCLASS})" in row[0]
        print(
            f"GIN index ix_dim_product_attrs  {GIN_OPCLASS}  "
            f"{'OK' if gin_ok else 'MISSING or wrong  FAIL'}"
        )
        ok = ok and gin_ok

        # Partitions: relkind 'r' keeps the tables and drops the index partitions
        # that pg_inherits lists too.
        cur.execute(
            """
            SELECT inhparent::regclass::text, COUNT(*)
            FROM pg_inherits i JOIN pg_class c ON c.oid = i.inhrelid
            WHERE c.relkind = 'r'
            GROUP BY 1
            """
        )
        partitions = dict(cur.fetchall())
        for table, want in EXPECTED_PARTITIONS.items():
            got = partitions.get(table, 0)
            ok_part = got == want
            print(
                f"partitions {table:<21} {got:>3}  (expect {want})  "
                f"{'OK' if ok_part else 'FAIL'}"
            )
            ok = ok and ok_part

    return ok


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    env = read_env()
    if "POSTGRES_DB" not in env:
        sys.exit("POSTGRES_DB not found in .env.example or .env: run this from your "
                 "clone of the repo, docs/SETUP_SPARK.md step 9.")

    parser = argparse.ArgumentParser(
        description="Load the three small dimensions into the Postgres star schema.")
    parser.add_argument(
        "--database", metavar="NAME", default=env["POSTGRES_DB"],
        help=f"database to load (default: {env['POSTGRES_DB']}, POSTGRES_DB from .env.example / .env)")
    database = parser.parse_args().database

    host, port = env["POSTGRES_HOST"], int(env["POSTGRES_PORT"])
    print(f"Connecting to {host}:{port}/{database} ...")
    started = time.monotonic()
    try:
        conn = psycopg2.connect(
            host=host, port=port, dbname=database,
            user=env["POSTGRES_USER"], password=env["POSTGRES_PASSWORD"],
            connect_timeout=5)
    except psycopg2.OperationalError as exc:
        sys.exit(
            f"Cannot connect to Postgres: {str(exc).strip()}\n"
            "Start it: docker compose up -d --wait postgres\n"
            f"Or check --database: {database!r} must exist and have warehouse/ddl.sql applied."
        )

    try:
        print("Upserting dim_date ...", end=" ", flush=True)
        n = upsert_dim_date(conn)
        print(f"{n} rows")

        print("Upserting dim_event_type ...", end=" ", flush=True)
        n = upsert_dim_event_type(conn)
        print(f"{n} rows")

        print("Upserting dim_warehouse ...", end=" ", flush=True)
        n = upsert_dim_warehouse(conn)
        print(f"{n} rows")

        print()
        ok = verify(conn)
    finally:
        conn.close()

    print(f"\ntook  {time.monotonic() - started:.1f} s")
    if ok:
        print("POSTGRES STAR OK")
    else:
        print("POSTGRES STAR CHECK FAILED — see lines above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
