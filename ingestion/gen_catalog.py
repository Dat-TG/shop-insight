import hashlib
import json
import os
import sys
import time
from pathlib import Path
 
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
os.environ["SPARK_CONF_DIR"] = str(REPO / "conf")
 
from pyspark.sql import SparkSession  # noqa: E402
 
SILVER_DIR = REPO / "data" / "silver"
CATALOG_DIR = REPO / "data" / "catalog"
CATALOG_FILE = CATALOG_DIR / "products.json"
 

COLORS = [
    "space_grey", "black", "white", "silver", "gold",
    "midnight_blue", "crimson_red", "forest_green", "rose_gold", "graphite",
]
TAGS = [
    "flagship", "5g", "budget", "bestseller", "new_arrival",
    "eco_friendly", "limited_edition", "wireless", "waterproof", "gaming",
]
 
 
def _digest_ints(product_id: int) -> list:
    digest = hashlib.sha256(str(product_id).encode("utf-8")).hexdigest()
    return [int(digest[i:i + 8], 16) for i in range(0, 64, 8)]
 
 
def build_attributes(product_id: int) -> dict:
    """Create one synthetic attribute document for a product."""
    h = _digest_ints(product_id)
    color = COLORS[h[0] % len(COLORS)]
    weight_grams = 50 + (h[1] % 4951)          
    warranty_months = [6, 12, 18, 24, 36][h[2] % 5]
    length_mm = 50 + (h[3] % 450)
    width_mm = 30 + (h[4] % 350)
    depth_mm = 5 + (h[5] % 195)
 
    n_tags = 1 + (h[6] % 3)                    
    start = h[6] % len(TAGS)
    stride = 1 + (h[7] % (len(TAGS) - 1))      
    tags = [TAGS[(start + i * stride) % len(TAGS)] for i in range(n_tags)]
 
    screen_inches = round(4.0 + (h[7] % 140) / 10, 1)   
    battery_mah = 1000 + ((h[0] ^ h[7]) % 9001)          
 
    return {
        "product_id": product_id,
        "attributes": {
            "color": color,
            "weight_grams": weight_grams,
            "warranty_months": warranty_months,
            "dimensions": {
                "length_mm": length_mm,
                "width_mm": width_mm,
                "depth_mm": depth_mm,
            },
            "tags": tags,
            "specs": {
                "screen_inches": screen_inches,
                "battery_mah": battery_mah,
            },
        },
    }
 
 
def read_product_ids(spark) -> list:
    if not (SILVER_DIR / "_SUCCESS").exists():
        print(f"{SILVER_DIR} has no data yet (no _SUCCESS marker). Run processing/batch_silver.py first.")
        sys.exit(1)
    silver = spark.read.parquet(str(SILVER_DIR))
    rows = silver.select("product_id").distinct().collect()
    return sorted(r["product_id"] for r in rows)
 
 
def write_catalog(product_ids: list) -> None:
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = CATALOG_FILE.with_suffix(".json.tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        for pid in product_ids:
            f.write(json.dumps(build_attributes(pid), separators=(",", ":")))
            f.write("\n")
    tmp_path.replace(CATALOG_FILE)  
 
 
def main():
    start = time.time()
    spark = (
        SparkSession.builder
        .appName("gen_catalog")
        .master("local[*]")
        .getOrCreate()
    )
    try:
        product_ids = read_product_ids(spark)
    finally:
        spark.stop()
 
    write_catalog(product_ids)
 
    # Re-read from disk, never trust the in-memory state.
    with open(CATALOG_FILE, encoding="utf-8") as f:
        lines = f.readlines()
    distinct_ids = {json.loads(line)["product_id"] for line in lines}
    took = time.time() - start
 
    print(f"products               {len(lines):>10,}")
    print(f"distinct product_id    {len(distinct_ids):>10,}   (expect equal to the line count above)")
    print(f"took                   {took:>9.0f} s")
 
    if len(lines) != len(distinct_ids):
        print("CATALOG CHECK FAILED: duplicate product_id in products.json")
        sys.exit(1)
    print("CATALOG OK")
 
 
if __name__ == "__main__":
    main()