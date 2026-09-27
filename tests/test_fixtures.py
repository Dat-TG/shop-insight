"""Fixture validation for BR1–BR8.

Run with:
    python tests/test_fixtures.py

No extra dependencies — uses only stdlib json, pathlib, re, sys.

Validates:
  - Exactly 8 canonical fixture files exist in web/fixtures/.
  - No BR9 fixture exists.
  - Every fixture contains "default" and "empty" at the top level.
  - Every scenario has exactly "data" and "meta" at the response-envelope level.
  - QueryMeta contains exactly: ms, warehouse, partitions, rows.
  - ms >= 0.
  - partitions is a non-negative integer.
  - rows is a non-negative integer.
  - rows == len(data).
  - meta.warehouse is the fixture's engine from docs/API_CONTRACT.md section 2.
  - Empty scenarios have data=[] and rows=0.
  - Each default row has exactly the contract's fields: required fields typed,
    BR4's nullable fields present (null allowed), no field the contract lacks.
  - BR1/BR3 default fixtures contain at least one row with category_l1=="unknown".
  - BR6 default fixture contains the 9999.0 sentinel.
  - BR6 default fixture contains at least one urgent row (days_to_stockout < 3).
  - No field or filename containing "br9" or "BR9" exists.
  - Every router's warehouse="..." literal is "Fixture" or its section-2 engine.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

# ── Resolve paths ────────────────────────────────────────────────────────────
REPO = Path(__file__).resolve().parents[1]
FIXTURES_DIR = REPO / "web" / "fixtures"
ROUTERS_DIR = REPO / "serving" / "api" / "routers"

# ── Constants ────────────────────────────────────────────────────────────────
CANONICAL_FILES = [
    "br1-gmv-by-minute.json",
    "br2-funnel-daily.json",
    "br3-trending-products.json",
    "br4-rfm-segments.json",
    "br5-abandoned-carts.json",
    "br6-stockout-risk.json",
    "br7-product-affinity.json",
    "br8-order-velocity-alerts.json",
]

# The storage mapping frozen in docs/API_CONTRACT.md section 2. A fixture carries
# its BR's production engine. A router may also say "Fixture" while it still
# serves a fixture (section 1.2). Postgres serves no screen (SYSTEM_DESIGN 12).
EXPECTED_WAREHOUSE = {
    "br1-gmv-by-minute.json": "Cassandra",
    "br2-funnel-daily.json": "Parquet",
    "br3-trending-products.json": "Cassandra",
    "br4-rfm-segments.json": "Parquet",
    "br5-abandoned-carts.json": "Cassandra",
    "br6-stockout-risk.json": "Cassandra",
    "br7-product-affinity.json": "Parquet",
    "br8-order-velocity-alerts.json": "Cassandra",
}
META_REQUIRED_KEYS = {"ms", "warehouse", "partitions", "rows"}

# Per-BR required row fields with their allowed Python types.
# Use tuple for "one of these types" (like Optional[int] → (int, type(None))).
BR_ROW_FIELDS: dict[str, dict[str, Any]] = {
    "br1-gmv-by-minute.json": {
        "event_date": str,
        "category_l1": str,
        "window_start": str,
        "gmv": (int, float),
        "order_count": int,
    },
    "br2-funnel-daily.json": {
        "step": str,
        "count": int,
        "session_count": int,
        "conversion_rate": (int, float),
    },
    "br3-trending-products.json": {
        "window_start": str,
        "rank": int,
        "product_id": int,
        "brand": str,
        "category_l1": str,
        "view_count": int,
        "cart_count": int,
    },
    "br4-rfm-segments.json": {
        "user_id": int,
        "snapshot_date": str,
        "frequency": int,
        "monetary": (int, float),
        "segment": str,
        # nullable fields: BR_NULLABLE_FIELDS
    },
    "br5-abandoned-carts.json": {
        "event_date": str,
        "user_session": str,
        "cart_value": (int, float),
        "user_id": int,
        "item_count": int,
        "last_event_at": str,
    },
    "br6-stockout-risk.json": {
        "warehouse_id": int,
        "days_to_stockout": (int, float),
        "product_id": int,
        "stock_on_hand": int,
        "velocity_7d": (int, float),
    },
    "br7-product-affinity.json": {
        "product_a": int,
        "product_b": int,
        "co_count": int,
        "support": (int, float),
        "lift": (int, float),
    },
    "br8-order-velocity-alerts.json": {
        "event_date": str,
        "window_start": str,
        "user_id": int,
        "order_count": int,
        "total_value": (int, float),
        "severity": str,
    },
}

# Per-BR fields that must be present in every row but may be null
# (docs/API_CONTRACT.md section 6: null if the user never purchased).
BR_NULLABLE_FIELDS: dict[str, dict[str, Any]] = {
    "br4-rfm-segments.json": {
        "recency_days": int,
        "r_score": int,
        "f_score": int,
        "m_score": int,
        "rfm_cell": str,
    },
}

VALID_STEPS = {"view", "cart", "purchase"}
VALID_SEGMENTS = {
    "champion", "loyal", "promising", "needs_attention",
    "at_risk", "hibernating", "no_purchase",
}
VALID_SEVERITIES = {"low", "medium", "high"}


# ── Helper ───────────────────────────────────────────────────────────────────
def _type_ok(value: Any, expected: Any) -> bool:
    """Return True if value matches the expected type or tuple of types."""
    if isinstance(expected, tuple):
        return isinstance(value, expected)
    return isinstance(value, expected)


# ── Validation logic ─────────────────────────────────────────────────────────
def validate_all() -> list[str]:
    """Run all checks. Returns a list of error messages (empty = pass)."""
    errors: list[str] = []

    # ── 1. Exactly 8 canonical files ────────────────────────────────────────
    for fname in CANONICAL_FILES:
        if not (FIXTURES_DIR / fname).exists():
            errors.append(f"MISSING canonical fixture: {fname}")

    # ── 2. No BR9 fixture or file ────────────────────────────────────────────
    for path in FIXTURES_DIR.iterdir():
        if "br9" in path.name.lower():
            errors.append(f"BR9 fixture must not exist: {path.name}")

    # ── 3. Per-file checks ───────────────────────────────────────────────────
    for fname in CANONICAL_FILES:
        path = FIXTURES_DIR / fname
        if not path.exists():
            continue  # already reported above

        try:
            bundle = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            errors.append(f"{fname}: invalid JSON — {exc}")
            continue

        # ── 3a. Bundle must have exactly "default" and "empty" ──────────────
        # (allow extra metadata keys starting with "_")
        top_keys = {k for k in bundle if not k.startswith("_")}
        if top_keys != {"default", "empty"}:
            errors.append(
                f"{fname}: top-level keys must be exactly 'default' and 'empty', "
                f"got {sorted(top_keys)}"
            )

        for scenario_name in ("default", "empty"):
            if scenario_name not in bundle:
                continue
            scenario = bundle[scenario_name]
            prefix = f"{fname}[{scenario_name}]"

            # ── 3b. Scenario must have exactly "data" and "meta" ─────────────
            sc_keys = set(scenario.keys())
            if sc_keys != {"data", "meta"}:
                errors.append(
                    f"{prefix}: keys must be exactly 'data' and 'meta', got {sorted(sc_keys)}"
                )
                continue

            data = scenario["data"]
            meta = scenario["meta"]

            # ── 3c. data must be a list ──────────────────────────────────────
            if not isinstance(data, list):
                errors.append(f"{prefix}: data must be a list")
                continue

            # ── 3d. meta must be an object ───────────────────────────────────
            if not isinstance(meta, dict):
                errors.append(f"{prefix}: meta must be an object")
                continue

            # ── 3e. meta must have exactly ms, warehouse, partitions, rows ───
            meta_keys = set(meta.keys())
            if meta_keys != META_REQUIRED_KEYS:
                errors.append(
                    f"{prefix}.meta: must have exactly {sorted(META_REQUIRED_KEYS)}, "
                    f"got {sorted(meta_keys)}"
                )

            # ── 3f. ms >= 0 ──────────────────────────────────────────────────
            ms = meta.get("ms")
            if not isinstance(ms, (int, float)) or ms < 0:
                errors.append(f"{prefix}.meta.ms: must be a non-negative number, got {ms!r}")

            # ── 3g. warehouse is the BR's contract engine ────────────────────
            wh = meta.get("warehouse")
            if wh != EXPECTED_WAREHOUSE[fname]:
                errors.append(
                    f"{prefix}.meta.warehouse: contract §2 maps this BR to "
                    f"{EXPECTED_WAREHOUSE[fname]!r}, got {wh!r}"
                )

            # ── 3h. partitions >= 0 int ──────────────────────────────────────
            parts = meta.get("partitions")
            if not isinstance(parts, int) or parts < 0:
                errors.append(
                    f"{prefix}.meta.partitions: must be a non-negative integer, got {parts!r}"
                )

            # ── 3i. rows >= 0 int ─────────────────────────────────────────────
            rows = meta.get("rows")
            if not isinstance(rows, int) or rows < 0:
                errors.append(
                    f"{prefix}.meta.rows: must be a non-negative integer, got {rows!r}"
                )

            # ── 3j. rows == len(data) ────────────────────────────────────────
            if isinstance(rows, int) and isinstance(data, list) and rows != len(data):
                errors.append(
                    f"{prefix}: meta.rows={rows} but len(data)={len(data)}"
                )

            # ── 3k. Empty scenario must have data=[] and rows=0 ─────────────
            if scenario_name == "empty":
                if data != []:
                    errors.append(f"{prefix}: empty scenario must have data=[]")
                if rows != 0:
                    errors.append(f"{prefix}: empty scenario must have rows=0")

            # ── 3l. Per-BR row field checks (default scenario only) ──────────
            if scenario_name == "default" and isinstance(data, list):
                required_fields = BR_ROW_FIELDS.get(fname, {})
                nullable_fields = BR_NULLABLE_FIELDS.get(fname, {})
                for i, row in enumerate(data):
                    if not isinstance(row, dict):
                        errors.append(f"{prefix}.data[{i}]: must be an object")
                        continue
                    for field, expected_type in required_fields.items():
                        if field not in row:
                            errors.append(
                                f"{prefix}.data[{i}]: missing required field '{field}'"
                            )
                        elif row[field] is not None and not _type_ok(row[field], expected_type):
                            errors.append(
                                f"{prefix}.data[{i}].{field}: expected {expected_type}, "
                                f"got {type(row[field]).__name__} ({row[field]!r})"
                            )
                    # Exactly the contract's fields: nothing extra, nothing nullable omitted.
                    extra = sorted(set(row) - set(required_fields) - set(nullable_fields))
                    if extra:
                        errors.append(
                            f"{prefix}.data[{i}]: fields not in docs/API_CONTRACT.md: {extra}"
                        )
                    for field in nullable_fields:
                        if field not in row:
                            errors.append(
                                f"{prefix}.data[{i}]: missing nullable field '{field}' "
                                "(send null, do not omit it)"
                            )

                # Extra per-BR checks
                _check_br_specifics(fname, scenario_name, data, errors)

    # ── 4. Routers: warehouse literal is "Fixture" or the contract engine ────
    # The regex matches warehouse="..." or warehouse='...' keyword arguments only.
    # Docstring examples use "warehouse": "..." (a colon), so they are not matched.
    # A router with no literal at all (a constant, a variable) is reported too,
    # because this check could not see what it returns.
    for fname in CANONICAL_FILES:
        router = ROUTERS_DIR / f"{fname.split('-')[0]}.py"
        if not router.exists():
            errors.append(f"MISSING router for {fname}: {router.name}")
            continue
        allowed = {"Fixture", EXPECTED_WAREHOUSE[fname]}
        literals = re.findall(r'warehouse\s*=\s*["\']([^"\']*)["\']', router.read_text())
        if not literals:
            errors.append(
                f"{router.name}: no warehouse=\"...\" literal found; "
                "pass QueryMeta a string literal so this check can read it"
            )
        for wh in literals:
            if wh not in allowed:
                errors.append(
                    f"{router.name}: warehouse={wh!r}, must be one of {sorted(allowed)} "
                    "(contract §2, or Fixture while it serves a fixture)"
                )

    return errors


def _check_br_specifics(
    fname: str, scenario_name: str, data: list[Any], errors: list[str]
) -> None:
    """Additional per-BR semantic checks."""
    prefix = f"{fname}[{scenario_name}]"

    # ── BR1: must include category_l1 = "unknown" ────────────────────────────
    if fname == "br1-gmv-by-minute.json":
        has_unknown = any(
            row.get("category_l1") == "unknown" for row in data if isinstance(row, dict)
        )
        if not has_unknown:
            errors.append(
                f"{prefix}: must contain at least one row with category_l1='unknown' "
                "(~32.4% of source events have no category_code)"
            )

    # ── BR2: steps must be view/cart/purchase ─────────────────────────────────
    if fname == "br2-funnel-daily.json":
        steps = {row.get("step") for row in data if isinstance(row, dict)}
        invalid_steps = steps - VALID_STEPS
        if invalid_steps:
            errors.append(f"{prefix}: invalid step values: {invalid_steps}")

    # ── BR3: must include category_l1 = "unknown" ────────────────────────────
    if fname == "br3-trending-products.json":
        has_unknown = any(
            row.get("category_l1") == "unknown" for row in data if isinstance(row, dict)
        )
        if not has_unknown:
            errors.append(
                f"{prefix}: must contain at least one row with category_l1='unknown'"
            )

    # ── BR4: segment values must be valid ────────────────────────────────────
    if fname == "br4-rfm-segments.json":
        for i, row in enumerate(data):
            if not isinstance(row, dict):
                continue
            seg = row.get("segment")
            if seg not in VALID_SEGMENTS:
                errors.append(
                    f"{prefix}.data[{i}].segment: must be one of {sorted(VALID_SEGMENTS)}, "
                    f"got {seg!r}"
                )
            # Nullable fields: allowed to be None or their natural type
            for nullable_field, expected_type in BR_NULLABLE_FIELDS[fname].items():
                if nullable_field in row:
                    val = row[nullable_field]
                    if val is not None and not isinstance(val, expected_type):
                        errors.append(
                            f"{prefix}.data[{i}].{nullable_field}: must be {expected_type.__name__} "
                            f"or null, got {type(val).__name__}"
                        )

    # ── BR6: sentinel 9999.0 must exist ──────────────────────────────────────
    if fname == "br6-stockout-risk.json":
        sentinel_rows = [
            row for row in data
            if isinstance(row, dict) and row.get("days_to_stockout") == 9999.0
        ]
        if not sentinel_rows:
            errors.append(
                f"{prefix}: must contain at least one row with days_to_stockout=9999.0 "
                "(sentinel for zero-velocity stock; Cassandra clustering column cannot be null)"
            )

        urgent_rows = [
            row for row in data
            if isinstance(row, dict)
            and isinstance(row.get("days_to_stockout"), (int, float))
            and row["days_to_stockout"] < 3
        ]
        if not urgent_rows:
            errors.append(
                f"{prefix}: must contain at least one urgent row with days_to_stockout < 3"
            )

        # days_to_stockout must never be null (sentinel replaces null for Cassandra)
        for i, row in enumerate(data):
            if isinstance(row, dict) and row.get("days_to_stockout") is None:
                errors.append(
                    f"{prefix}.data[{i}].days_to_stockout: must not be null "
                    "(use 9999.0 sentinel for zero-velocity rows)"
                )

    # ── BR8: severity values must be valid ────────────────────────────────────
    if fname == "br8-order-velocity-alerts.json":
        for i, row in enumerate(data):
            if not isinstance(row, dict):
                continue
            sev = row.get("severity")
            if sev not in VALID_SEVERITIES:
                errors.append(
                    f"{prefix}.data[{i}].severity: must be one of {sorted(VALID_SEVERITIES)}, "
                    f"got {sev!r}"
                )
        # All three severity levels should appear
        severities_present = {
            row.get("severity") for row in data if isinstance(row, dict)
        }
        missing = VALID_SEVERITIES - severities_present
        if missing:
            errors.append(
                f"{prefix}: default scenario should cover all severity values; "
                f"missing: {missing}"
            )

    # ── No-BR9 check inside data keys ─────────────────────────────────────────
    for i, row in enumerate(data):
        if isinstance(row, dict):
            for key in row:
                if "br9" in key.lower():
                    errors.append(
                        f"{fname}[{scenario_name}].data[{i}]: field '{key}' references BR9 "
                        "(BR9 was removed from project scope)"
                    )


# ── Entry point ──────────────────────────────────────────────────────────────
def main() -> None:
    print("=" * 60)
    print("ShopInsight — Fixture Validation")
    print(f"Fixtures directory: {FIXTURES_DIR}")
    print(f"Routers directory:  {ROUTERS_DIR}")
    print("=" * 60)

    errors = validate_all()

    if errors:
        print(f"\n❌  {len(errors)} error(s) found:\n")
        for err in errors:
            print(f"  • {err}")
        print()
        sys.exit(1)
    else:
        print(f"\n✅  All {len(CANONICAL_FILES)} fixture bundles passed validation.\n")
        for fname in CANONICAL_FILES:
            bundle = json.loads((FIXTURES_DIR / fname).read_text())
            default_rows = len(bundle["default"]["data"])
            wh = bundle["default"]["meta"]["warehouse"]
            print(f"  {fname}  [{default_rows} default rows, warehouse={wh}]")
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
