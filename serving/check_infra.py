"""Infrastructure check: the two containers answer from Python.

    docker compose up -d --wait
    python serving/check_infra.py

Connects to Cassandra with cassandra-driver and to Postgres with psycopg2 - the
two clients every later script uses - and reads back a handful of values that
prove the containers are the ones docker-compose.yml describes. It is the
Docker half of what kata.py is for Spark.

It creates nothing: no keyspace, no table, no row. serving/apply_schema.py
(Nguyen) makes the Cassandra keyspace and tables, and warehouse/ddl.sql (Tin,
W39) makes the Postgres star schema. This check must pass BEFORE either of
those exists, so it must not depend on them.

Why these lines and not just "connected":
- The two version lines catch a stale image cached from before the tags were
  pinned. `docker compose pull` fixes that; editing the tag does not.
- shared_buffers and maintenance_work_mem are set in docker-compose.yml and
  read back here out of the running server, so a setting that did not take
  effect is visible in one command instead of at the end of a W39 index build.
- jsonb_path_ops is the operator class of the GIN index Tin builds on
  dim_product.attributes in W39 (SYSTEM_DESIGN.md section 5.4). postgres:16
  ships it in core, so warehouse/ddl.sql needs no CREATE EXTENSION. The real
  index is W39's job; this only proves the build has the operator class.
- data_center is the name a DCAwareRoundRobinPolicy would need in W40.

Done when the script prints INFRA OK. Post the whole block in the group chat,
the way you posted KATA OK:

    cassandra 127.0.0.1:9042
      release_version       4.1.12          (expect 4.1.12: the docker-compose.yml tag)
      data_center           datacenter1     (the name the W40 driver will need)
      keyspace shopinsight  absent          (created by serving/apply_schema.py; either state is fine here)
    postgres 127.0.0.1:5432
      server_version        16.15           (expect 16.15: the docker-compose.yml tag)
      current_database      shopinsight     (connected as shopinsight)
      shared_buffers        512MB           (expect 512MB: docker-compose.yml)
      maintenance_work_mem  256MB           (expect 256MB: room for the W39 GIN build)
      gin jsonb_path_ops    present         (expect present: postgres:16 needs no extension)
    took                       0.2 s
    INFRA OK

There is no retry loop on purpose: `docker compose up -d --wait` returns only
when both healthchecks pass, so a failure here means something real rather
than "Cassandra is still starting". Plain `up -d` returns too early - that is
what the --wait is for.
"""

import sys
import time
from pathlib import Path

import psycopg2
from cassandra.cluster import Cluster, NoHostAvailable

REPO = Path(__file__).resolve().parents[1]
ENV_EXAMPLE = REPO / ".env.example"
ENV_FILE = REPO / ".env"

# docker-compose.yml pins these; change them together.
EXPECTED_CASSANDRA_VERSION = "4.1.12"
EXPECTED_POSTGRES_VERSION = "16.15"
EXPECTED_SHARED_BUFFERS = "512MB"
EXPECTED_MAINTENANCE_WORK_MEM = "256MB"

# The GIN operator class of the W39 index on dim_product.attributes.
GIN_OPCLASS = "jsonb_path_ops"


def read_env():
    """The values from .env.example, overridden by .env when it exists.

    Eight lines instead of python-dotenv: one pin fewer (CLAUDE.md hard rule 1)
    and one place to look when a password is wrong. Shell environment variables
    are NOT read, on purpose. KEY=value, one per line, no quotes and no
    trailing comment - the same subset docker compose reads out of .env.

    W39 imports this rather than copying it: `from serving.check_infra import
    read_env` in serving/apply_schema.py and serving/load_star_postgres.py, the
    way processing/streaming_gold.py imports clean() from batch_silver.py. When
    a caller outside serving/ needs it - the FastAPI app in W42 - move it to
    serving/config.py in that same PR and update the imports.
    """
    values = {}
    for path in (ENV_EXAMPLE, ENV_FILE):       # .env wins where the two overlap
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    return values


def row(label, value, note=""):
    """One aligned result line, in the shape kata.py and load_bronze.py print."""
    print(f"  {label:<22}{value:<16}{note}")


def expected(actual, want, why, fix):
    """The note beside a value: the reason when it matches, the fix when it does not."""
    return f"(expect {want}: {why})" if actual == want else f"<-- expected {want}: {fix}"


def check_cassandra(env):
    """Connect with cassandra-driver and read the node's own system tables."""
    host, port = env["CASSANDRA_HOST"], int(env["CASSANDRA_PORT"])
    keyspace = env["CASSANDRA_KEYSPACE"]
    print(f"cassandra {host}:{port}")

    cluster = Cluster([host], port=port)
    try:
        session = cluster.connect()
    except NoHostAvailable as error:
        row("connect", "FAILED", f"<-- {error}")
        return False

    try:
        # system.local is fully qualified, so this needs no keyspace and no USE.
        local = session.execute(
            "SELECT release_version, data_center FROM system.local").one()
        row("release_version", local.release_version,
            expected(local.release_version, EXPECTED_CASSANDRA_VERSION,
                     "the docker-compose.yml tag",
                     "docker compose pull, then up -d --wait"))
        row("data_center", local.data_center, "(the name the W40 driver will need)")

        # keyspace_name is the partition key, so this is a legal single-partition
        # read. Reported either way and never part of the pass/fail: the check has
        # to keep passing after apply_schema.py creates the keyspace.
        found = session.execute(
            "SELECT keyspace_name FROM system_schema.keyspaces WHERE keyspace_name = %s",
            (keyspace,)).one()
        row(f"keyspace {keyspace}", "present" if found else "absent",
            "(created by serving/apply_schema.py; either state is fine here)")
    finally:
        cluster.shutdown()

    return local.release_version == EXPECTED_CASSANDRA_VERSION


def check_postgres(env):
    """Connect with psycopg2 and read back the settings docker-compose.yml sets."""
    host, port = env["POSTGRES_HOST"], int(env["POSTGRES_PORT"])
    print(f"postgres {host}:{port}")

    try:
        connection = psycopg2.connect(
            host=host, port=port, dbname=env["POSTGRES_DB"],
            user=env["POSTGRES_USER"], password=env["POSTGRES_PASSWORD"],
            connect_timeout=5)
    except psycopg2.OperationalError as error:
        row("connect", "FAILED", f"<-- {str(error).strip()}")
        return False

    try:
        cursor = connection.cursor()

        # SHOW server_version gives "16.15 (Debian 16.15-1.pgdg120+1)"; the first
        # word is the number. SELECT version() buries it in a much longer string.
        cursor.execute("SHOW server_version")
        version = cursor.fetchone()[0].split()[0]
        row("server_version", version,
            expected(version, EXPECTED_POSTGRES_VERSION, "the docker-compose.yml tag",
                     "docker compose pull, then up -d --wait"))

        # Catches the nastiest trap here: editing POSTGRES_USER or POSTGRES_DB in
        # .env after the volume was initialised, which the image silently ignores.
        cursor.execute("SELECT current_database(), current_user")
        database, user = cursor.fetchone()
        row("current_database", database, f"(connected as {user})")

        cursor.execute("SHOW shared_buffers")
        shared_buffers = cursor.fetchone()[0]
        row("shared_buffers", shared_buffers,
            expected(shared_buffers, EXPECTED_SHARED_BUFFERS, "docker-compose.yml",
                     "docker compose up -d --wait picks up the command: line"))

        cursor.execute("SHOW maintenance_work_mem")
        work_mem = cursor.fetchone()[0]
        row("maintenance_work_mem", work_mem,
            expected(work_mem, EXPECTED_MAINTENANCE_WORK_MEM,
                     "room for the W39 GIN build", "docker-compose.yml's command: line"))

        # One query, no side effects: is the operator class W39's index needs in
        # this build at all. The real CREATE INDEX is warehouse/ddl.sql's job.
        cursor.execute(
            "SELECT count(*) FROM pg_opclass c JOIN pg_am a ON a.oid = c.opcmethod "
            "WHERE a.amname = 'gin' AND c.opcname = %s", (GIN_OPCLASS,))
        opclass = "present" if cursor.fetchone()[0] else "absent"
        row(f"gin {GIN_OPCLASS}", opclass,
            expected(opclass, "present", "postgres:16 needs no extension",
                     "not a postgres:16 image - check docker compose ps"))
    finally:
        connection.close()

    return (version == EXPECTED_POSTGRES_VERSION
            and shared_buffers == EXPECTED_SHARED_BUFFERS
            and work_mem == EXPECTED_MAINTENANCE_WORK_MEM
            and opclass == "present")


def main():
    env = read_env()
    if "CASSANDRA_HOST" not in env:
        sys.exit(f"{ENV_EXAMPLE} not found: run this from your clone of the repo, "
                 "docs/SETUP_SPARK.md step 9.")

    started = time.monotonic()
    # Both always run: one dead store must not hide the state of the other.
    cassandra_ok = check_cassandra(env)
    postgres_ok = check_postgres(env)

    print(f"{'took':<24}{time.monotonic() - started:>6.1f} s")
    if cassandra_ok and postgres_ok:
        print("INFRA OK")
    else:
        print("INFRA CHECK FAILED: see the lines above. If a store did not answer, run "
              "docker compose up -d --wait, then this again (docs/SETUP_SPARK.md step 9).")
        sys.exit(1)


if __name__ == "__main__":
    main()
