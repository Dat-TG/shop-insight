"""Warehouse batch loader: dim tables and facts into PostgreSQL star schema.

    python processing/batch_warehouse.py

W39 scope: load three small dimensions into Postgres:
    - dim_date          (92 rows, 2019-10-01 to 2019-12-31)
    - dim_event_type    (5 rows: view, cart, purchase, other, unknown)
    - dim_warehouse     (5 rows: warehouse IDs 1-5)

W40 scope (not yet):
    - dim_product SCD2
    - dim_user SCD2
    - fact_event
    - fact_session_funnel
    - fact_inventory_daily

Prerequisites:
    1. PostgreSQL running (Docker: docker compose up -d postgres)
    2. warehouse/ddl.sql already applied:
          docker exec -i shopinsight-postgres psql -U shopinsight -d shopinsight < warehouse/ddl.sql
    3. seed/holidays_2019.csv present in the repo (tracked by git, NOT in data/)

Connection: reads PG_DSN from environment, falls back to the Docker default
    PG_DSN=postgresql://shopinsight:shopinsight@localhost:5432/shopinsight

Done when: 3 dimensions loaded, GIN index on dim_product.attributes exists,
all constraint checks pass. Prints WAREHOUSE OK at end.

Design decisions:
    - Uses psycopg2 directly (CLAUDE.md hard rule 2: no ORM, no SQLAlchemy).
    - Upsert via INSERT ... ON CONFLICT DO UPDATE so reruns are idempotent.
    - seed/holidays_2019.csv goes through git so all four machines agree on
      is_holiday values (PLAN.md section "Nguyên tắc giữ cho bốn người
      chạy song song").
    - date_key is INTEGER yyyymmdd for fast range scans without casting.
    - day_of_week follows ISO 8601: Monday=1, Sunday=7.
"""

from __future__ import annotations

import csv
import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    sys.exit("psycopg2-binary not installed. Run: pip install psycopg2-binary==2.9.13")

# ── Connection ───────────────────────────────────────────────────────────────
DEFAULT_DSN = "postgresql://shopinsight:shopinsight@localhost:5432/shopinsight"
PG_DSN = os.environ.get("PG_DSN", DEFAULT_DSN)

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


def load_holidays() -> dict[date, tuple[str, str]]:
    """Load seed/holidays_2019.csv.

    Returns a dict mapping holiday_date (datetime.date) to
    (holiday_name, holiday_type). Raises FileNotFoundError early
    so the whole script fails with a clear message instead of producing
    a dim_date with no holidays.
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
            holidays[d] = (row["holiday_name"].strip(), row["holiday_type"].strip())
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
            "iso_week": iso_cal[1],
            "is_weekend": iso_cal[2] >= 6,      # Saturday=6, Sunday=7
            "is_holiday": h_name is not None,   # RULE: is_holiday ⟺ holiday_name IS NOT NULL
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
            day_of_month, day_of_week, iso_week, is_weekend,
            is_holiday, holiday_name, holiday_type
        )
        VALUES (
            %(date_key)s, %(full_date)s, %(year)s, %(quarter)s,
            %(month)s, %(month_name)s, %(day_of_month)s, %(day_of_week)s,
            %(iso_week)s, %(is_weekend)s,
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
# 5 rows total including an unknown sentinel with key -1.
# stage_rank: view=1, cart=2, purchase=3, other=9, unknown=0 (not a funnel stage)
DIM_EVENT_TYPE_ROWS = [
    {
        "event_type_key": -1,
        "event_code": "unknown",
        "display_name": "Unknown",
        "stage_rank": 0,
        "is_funnel_stage": False,
        "is_conversion": False,
        "cart_value_sign": 0,
    },
    {
        "event_type_key": 1,
        "event_code": "view",
        "display_name": "View",
        "stage_rank": 1,
        "is_funnel_stage": True,
        "is_conversion": False,
        "cart_value_sign": 0,
    },
    {
        "event_type_key": 2,
        "event_code": "cart",
        "display_name": "Add to Cart",
        "stage_rank": 2,
        "is_funnel_stage": True,
        "is_conversion": False,
        "cart_value_sign": 1,     # +1: adds value to cart
    },
    {
        "event_type_key": 3,
        "event_code": "purchase",
        "display_name": "Purchase",
        "stage_rank": 3,
        "is_funnel_stage": True,
        "is_conversion": True,
        "cart_value_sign": -1,    # -1: removes from cart (checkout)
    },
    {
        "event_type_key": 9,
        "event_code": "other",
        "display_name": "Other",
        "stage_rank": 9,
        "is_funnel_stage": False,
        "is_conversion": False,
        "cart_value_sign": 0,
    },
]


def upsert_dim_event_type(conn) -> int:
    sql = """
        INSERT INTO dim_event_type (
            event_type_key, event_code, display_name,
            stage_rank, is_funnel_stage, is_conversion, cart_value_sign
        )
        VALUES (
            %(event_type_key)s, %(event_code)s, %(display_name)s,
            %(stage_rank)s, %(is_funnel_stage)s, %(is_conversion)s, %(cart_value_sign)s
        )
        ON CONFLICT (event_type_key) DO UPDATE SET
            event_code      = EXCLUDED.event_code,
            display_name    = EXCLUDED.display_name,
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
# lead_time_days: typical replenishment lead time from supplier.
# capacity_units: maximum stock-keeping units the warehouse can hold.
DIM_WAREHOUSE_ROWS = [
    {
        "warehouse_id": 1,
        "warehouse_name": "Hanoi Central",
        "region": "North",
        "city": "Hanoi",
        "lead_time_days": 2,
        "capacity_units": 50000,
        "is_active": True,
    },
    {
        "warehouse_id": 2,
        "warehouse_name": "Ho Chi Minh South",
        "region": "South",
        "city": "Ho Chi Minh City",
        "lead_time_days": 2,
        "capacity_units": 80000,
        "is_active": True,
    },
    {
        "warehouse_id": 3,
        "warehouse_name": "Da Nang Central Hub",
        "region": "Central",
        "city": "Da Nang",
        "lead_time_days": 3,
        "capacity_units": 30000,
        "is_active": True,
    },
    {
        "warehouse_id": 4,
        "warehouse_name": "Can Tho Mekong",
        "region": "Mekong Delta",
        "city": "Can Tho",
        "lead_time_days": 4,
        "capacity_units": 20000,
        "is_active": True,
    },
    {
        "warehouse_id": 5,
        "warehouse_name": "Hai Phong Port",
        "region": "North",
        "city": "Hai Phong",
        "lead_time_days": 3,
        "capacity_units": 40000,
        "is_active": False,   # decommissioned: used for historical data only
    },
]


def upsert_dim_warehouse(conn) -> int:
    sql = """
        INSERT INTO dim_warehouse (
            warehouse_id, warehouse_name, region, city,
            lead_time_days, capacity_units, is_active
        )
        VALUES (
            %(warehouse_id)s, %(warehouse_name)s, %(region)s, %(city)s,
            %(lead_time_days)s, %(capacity_units)s, %(is_active)s
        )
        ON CONFLICT (warehouse_id) DO UPDATE SET
            warehouse_name = EXCLUDED.warehouse_name,
            region         = EXCLUDED.region,
            city           = EXCLUDED.city,
            lead_time_days = EXCLUDED.lead_time_days,
            capacity_units = EXCLUDED.capacity_units,
            is_active      = EXCLUDED.is_active
    """
    with conn.cursor() as cur:
        psycopg2.extras.execute_batch(cur, sql, DIM_WAREHOUSE_ROWS)
    conn.commit()
    return len(DIM_WAREHOUSE_ROWS)


# ── Verification ──────────────────────────────────────────────────────────────

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

        # is_holiday must equal (holiday_name IS NOT NULL) for every row
        cur.execute(
            """
            SELECT COUNT(*) FROM dim_date
            WHERE is_holiday != (holiday_name IS NOT NULL)
            """
        )
        bad = cur.fetchone()[0]
        consistency_ok = bad == 0
        print(
            f"is_holiday consistency {bad:>4} bad rows  (expect 0)  "
            f"{'OK' if consistency_ok else 'FAIL'}"
        )
        ok = ok and consistency_ok

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

        # GIN index on dim_product.attributes must exist
        cur.execute(
            """
            SELECT COUNT(*) FROM pg_indexes
            WHERE tablename = 'dim_product'
              AND indexname  = 'idx_dim_product_attributes_gin'
            """
        )
        gin_exists = cur.fetchone()[0] == 1
        print(
            f"GIN index dim_product.attributes  "
            f"{'exists  OK' if gin_exists else 'MISSING  FAIL'}"
        )
        ok = ok and gin_exists

    return ok


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"Connecting to {PG_DSN.split('@')[-1]} ...")
    started = time.monotonic()
    try:
        conn = psycopg2.connect(PG_DSN)
    except psycopg2.OperationalError as exc:
        sys.exit(
            f"Cannot connect to Postgres: {exc}\n"
            "Start Docker: docker compose up -d postgres\n"
            "Or set PG_DSN= to your database URL."
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
        print("WAREHOUSE OK")
    else:
        print("WAREHOUSE CHECK FAILED — see lines above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
