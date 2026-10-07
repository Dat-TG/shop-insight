import os
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
os.environ["SPARK_CONF_DIR"] = str(REPO / "conf")

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

DIM_USER_DIR = REPO / "data" / "warehouse" / "dim_user"
RFM_SEGMENTS_DIR = REPO / "data" / "gold" / "rfm_segments"
LAST_SNAPSHOT = date(2019, 11, 30)
RFM_GOLD_COLUMNS = ["user_id", "recency_days", "frequency", "monetary", "r_score", "f_score", "m_score", "segment"]
SEGMENTS = ["champion", "loyal", "promising", "needs_attention", "at_risk", "hibernating", "no_purchase"]
MANY_CURRENT_VERSIONS = "SELECT user_id FROM dim_user WHERE is_current GROUP BY user_id HAVING count(*) > 1"

FACT_SESSION_FUNNEL_DIR = REPO / "data" / "warehouse" / "fact_session_funnel"
FACT_EVENT_DIR = REPO / "data" / "warehouse" / "fact_event"
DIM_PRODUCT_DIR = REPO / "data" / "warehouse" / "dim_product"
FUNNEL_DAILY_DIR = REPO / "data" / "gold" / "funnel_daily"
ALL_CATEGORIES = "all"  # a stored total row per day, never a sum of the categories (as BR1's 'all')
VIEW_KEY, CART_KEY, PURCHASE_KEY = 1, 2, 3  # dim_event_type.event_type_key
# views/carts/purchases count SESSIONS that reached the step (funnel_stage >= 1 / >= 2 / = 3);
# the *_events columns count raw events. The API's session_count and count come from them.
FUNNEL_GOLD_COLUMNS = [
    "event_date", "category_l1", "views", "carts", "purchases", "cr_view_to_cart", "cr_cart_to_purchase",
    "view_events", "cart_events", "purchase_events",
]


def build_rfm_segments(dim):
    return dim.where("is_current").select(*RFM_GOLD_COLUMNS).withColumn("snapshot_date", F.lit(LAST_SNAPSHOT))


def rfm_segments_stats(gold):
    unscored = F.col("r_score").isNull()
    no_purchase = F.col("segment") == "no_purchase"
    return gold.agg(
        F.count("*").alias("rfm_segments rows"),
        F.countDistinct("user_id").alias("distinct users"),
        F.count_if(~unscored).alias("buyers"),
        F.countDistinct("segment").alias("segments"),
        F.count_if(unscored != no_purchase).alias("score and segment disagree"),
        F.count_if(~F.col("segment").isin(SEGMENTS)).alias("unknown segment"),
        F.countDistinct("snapshot_date").alias("snapshot partitions"),
    ).first().asDict()


def report(stats):
    for name, value in stats.items():
        print(f"{name:<30}{value:>10,}")


def run_rfm_segments(spark):
    dim = spark.read.parquet(str(DIM_USER_DIR))
    dim.createOrReplaceTempView("dim_user")
    many = spark.sql(MANY_CURRENT_VERSIONS).count()
    report({"users with >1 current version": many})
    if many:
        print("RFM_SEGMENTS MISMATCH: nothing was overwritten")
        return False
    build_rfm_segments(dim).write.mode("overwrite").partitionBy("snapshot_date").parquet(str(RFM_SEGMENTS_DIR))
    gold = spark.read.parquet(str(RFM_SEGMENTS_DIR))
    stats = {"current versions": dim.where("is_current").count(), **rfm_segments_stats(gold)}
    report(stats)
    ok = (
        stats["rfm_segments rows"] == stats["current versions"] == stats["distinct users"]
        and stats["score and segment disagree"] == 0
        and stats["unknown segment"] == 0
        and stats["snapshot partitions"] == 1
    )
    print("RFM_SEGMENTS OK" if ok else "RFM_SEGMENTS MISMATCH")
    return ok


def furthest_stage(view_events, cart_events, purchase_events):
    """The rule build_fact_session_funnel() in batch_warehouse.py uses for funnel_stage."""
    return (
        F.when(F.col(purchase_events) > 0, 3)
        .when(F.col(cart_events) > 0, 2)
        .when(F.col(view_events) > 0, 1)
        .otherwise(0)
    )


def build_session_categories(fact_event, dim_product, sessions):
    """One row per (session, category_l1) the session touched, with the furthest
    stage it reached on that category's products alone.

    A session that views a phone and buys a fridge has reached purchase for
    appliances but only view for electronics; giving both categories the
    session's own funnel_stage would count a purchase that never happened.
    """
    key = F.col("event_type_key")
    categories = F.broadcast(dim_product.select("product_sk", "category_l1"))
    return (
        fact_event.select("user_session", "product_sk", "event_type_key")
        # Equality join on the version key fact_event already carries, as gold_br7.py does.
        # Never look the version up again with a range join on the SCD2 validity dates:
        # on dim_product that measured 305,663,175 intermediate rows (SYSTEM_DESIGN 5.4).
        .join(categories, "product_sk", "left")  # left: an event that lost its category shows as null
        .join(sessions.select("user_session", "session_start_date", "funnel_stage"), "user_session")
        .groupBy("session_start_date", "user_session", "category_l1")
        .agg(
            F.count_if(key == VIEW_KEY).alias("view_events"),
            F.count_if(key == CART_KEY).alias("cart_events"),
            F.count_if(key == PURCHASE_KEY).alias("purchase_events"),
            F.max("funnel_stage").alias("funnel_stage"),  # one value per session, kept for the check
        )
        .withColumn("category_stage", furthest_stage("view_events", "cart_events", "purchase_events"))
    )


def funnel_measures(stage, view_events, cart_events, purchase_events):
    """A session reaches a step when its furthest stage is at least that step."""
    return [
        F.count_if(F.col(stage) >= 1).alias("views"),
        F.count_if(F.col(stage) >= 2).alias("carts"),
        F.count_if(F.col(stage) == 3).alias("purchases"),
        F.sum(view_events).cast("long").alias("view_events"),
        F.sum(cart_events).cast("long").alias("cart_events"),
        F.sum(purchase_events).cast("long").alias("purchase_events"),
    ]


def build_funnel_daily(sessions, pairs):
    """One row per (session start date, category_l1), plus a stored 'all' row per date.

    'all' comes straight from fact_session_funnel. It is not the sum of the
    categories: 12% of sessions touch more than one category and would count twice.
    """
    all_rows = (
        sessions.groupBy("session_start_date")
        .agg(*funnel_measures("funnel_stage", "view_count", "cart_count", "purchase_count"))
        .withColumn("category_l1", F.lit(ALL_CATEGORIES))
    )
    category_rows = pairs.groupBy("session_start_date", "category_l1").agg(
        *funnel_measures("category_stage", "view_events", "cart_events", "purchase_events")
    )
    return (
        all_rows.unionByName(category_rows)
        .withColumnRenamed("session_start_date", "event_date")  # the session's start day, Vietnam time
        .withColumn("cr_view_to_cart", F.try_divide("carts", "views"))  # null, not an ANSI error, on 0
        .withColumn("cr_cart_to_purchase", F.try_divide("purchases", "carts"))
        .select(*FUNNEL_GOLD_COLUMNS)
    )


def session_category_checks(pairs, fact_event_rows):
    """Checked before the write; any non-zero line means nothing is overwritten."""
    events = F.col("view_events") + F.col("cart_events") + F.col("purchase_events")
    joined = pairs.agg(
        F.sum(events).alias("events"),
        F.sum(F.when(F.col("category_l1").isNull(), events).otherwise(0)).alias("no_category"),
    ).first()
    disagree = (
        pairs.groupBy("user_session")
        .agg(F.max("category_stage").alias("best"), F.max("funnel_stage").alias("funnel_stage"))
        .where(F.col("best") != F.col("funnel_stage"))
        .count()
    )
    return {
        "events lost in the joins": fact_event_rows - joined["events"],
        "events with no category": joined["no_category"],
        "sessions with another stage": disagree,
    }


def funnel_daily_stats(gold):
    is_all = F.col("category_l1") == ALL_CATEGORIES

    def total(column, rows):
        return F.coalesce(F.sum(F.when(rows, F.col(column))), F.lit(0))

    return gold.agg(
        F.count("*").alias("funnel_daily rows"),
        F.countDistinct("event_date").alias("event_date partitions"),
        F.countDistinct("category_l1").alias("categories incl. all"),
        F.count_if(F.col("category_l1").isNull()).alias("null category_l1"),
        total("views", is_all).alias("all: view sessions"),
        total("carts", is_all).alias("all: cart sessions"),
        total("purchases", is_all).alias("all: purchase sessions"),
        total("view_events", is_all).alias("all: view events"),
        total("cart_events", is_all).alias("all: cart events"),
        total("purchase_events", is_all).alias("all: purchase events"),
        total("view_events", ~is_all).alias("categories: view events"),
        total("cart_events", ~is_all).alias("categories: cart events"),
        total("purchase_events", ~is_all).alias("categories: purchase events"),
        F.count_if((F.col("carts") > F.col("views")) | (F.col("purchases") > F.col("carts"))).alias(
            "rows where sessions rise"
        ),
    ).first().asDict()


def run_funnel_daily(spark):
    sessions = spark.read.parquet(str(FACT_SESSION_FUNNEL_DIR))
    fact_event = spark.read.parquet(str(FACT_EVENT_DIR))
    dim_product = spark.read.parquet(str(DIM_PRODUCT_DIR))
    pairs = build_session_categories(fact_event, dim_product, sessions)

    key = F.col("event_type_key")
    source = fact_event.agg(
        F.count("*").alias("rows"),
        F.count_if(key == VIEW_KEY).alias("views"),
        F.count_if(key == CART_KEY).alias("carts"),
        F.count_if(key == PURCHASE_KEY).alias("purchases"),
    ).first()
    checks = session_category_checks(pairs, source["rows"])
    report({"fact_event rows": source["rows"], **checks})
    if any(checks.values()):
        print("FUNNEL_DAILY MISMATCH: nothing was overwritten")
        return False

    funnel = build_funnel_daily(sessions, pairs)
    funnel.repartition("event_date").write.mode("overwrite").partitionBy("event_date").parquet(str(FUNNEL_DAILY_DIR))
    gold = spark.read.parquet(str(FUNNEL_DAILY_DIR))

    expected = sessions.agg(
        F.count("*").alias("sessions"),
        F.count_if(F.col("funnel_stage") >= 2).alias("cart sessions"),
        F.count_if(F.col("funnel_stage") == 3).alias("purchase sessions"),
        F.countDistinct("session_start_date").alias("session_start_date dirs"),
    ).first().asDict()
    stats = funnel_daily_stats(gold)
    report({**expected, **stats})
    low = gold.where(F.col("category_l1") == ALL_CATEGORIES).orderBy(F.asc_nulls_last("cr_cart_to_purchase")).first()
    print(f"{'lowest cart->purchase day':<30}{low['event_date'].isoformat():>10}   ({low['cr_cart_to_purchase']:.4f})")

    ok = (
        stats["all: view sessions"] == expected["sessions"]
        and stats["all: cart sessions"] == expected["cart sessions"]
        and stats["all: purchase sessions"] == expected["purchase sessions"]
        and stats["all: view events"] == stats["categories: view events"] == source["views"]
        and stats["all: cart events"] == stats["categories: cart events"] == source["carts"]
        and stats["all: purchase events"] == stats["categories: purchase events"] == source["purchases"]
        and stats["event_date partitions"] == expected["session_start_date dirs"]
        and stats["null category_l1"] == 0
        and stats["rows where sessions rise"] == 0
    )
    print("FUNNEL_DAILY OK" if ok else "FUNNEL_DAILY MISMATCH")
    return ok


def main():
    for path in (DIM_USER_DIR, FACT_SESSION_FUNNEL_DIR, FACT_EVENT_DIR, DIM_PRODUCT_DIR):
        if not (path / "_SUCCESS").exists():
            sys.exit(f"{path} is missing. Run python processing/batch_warehouse.py first.")
    spark = SparkSession.builder.master("local[*]").appName("batch_gold").getOrCreate()
    ok_rfm = run_rfm_segments(spark)
    ok_funnel = run_funnel_daily(spark)  # runs even when BR4 failed, so both report
    spark.stop()
    if not (ok_rfm and ok_funnel):
        sys.exit(1)
    print("GOLD OK")


if __name__ == "__main__":
    main()
