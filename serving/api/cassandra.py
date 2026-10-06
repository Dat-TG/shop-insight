"""The API's one Cassandra session, shared by the Cassandra routers (BR1, BR3, BR5, BR6, BR8).

    from serving.api.cassandra import session
    rows = list(session().execute(statement, (event_date, category_l1)))

Connected on the first request, not at import, so the API still starts (and
/health and the Parquet screens still answer) while Cassandra is down. Once
connected, the session is kept for the life of the process, and the driver
reconnects on its own after Cassandra restarts. functools.cache keeps only a
session that connected, never an exception, so a request that finds
Cassandra down does not stop the next one from trying again.

Cassandra being down (NoHostAvailable, at connect or at any execute) becomes
HTTP 503 in one place: the exception handler in serving/api/main.py.

Built like connect_cassandra() in processing/streaming_gold.py, which is not
imported: that would pull pyspark into the API and pin its process to UTC.
"""

import functools

try:
    from cassandra.cluster import EXEC_PROFILE_DEFAULT, Cluster, ExecutionProfile, NoHostAvailable
    from cassandra.policies import DCAwareRoundRobinPolicy
except ImportError:
    class NoHostAvailable(Exception):
        pass
    Cluster = None
from fastapi import HTTPException

from serving.check_infra import read_env

DATA_CENTER = "datacenter1"  # the node's own name (check_infra.py prints it)


@functools.cache
def session():
    """A session on the shopinsight keyspace."""
    if Cluster is None:
        raise HTTPException(503, "cassandra-driver is not installed. Run pip install cassandra-driver.")
    env = read_env()
    host, port, keyspace = env["CASSANDRA_HOST"], int(env["CASSANDRA_PORT"]), env["CASSANDRA_KEYSPACE"]
    profile = ExecutionProfile(load_balancing_policy=DCAwareRoundRobinPolicy(local_dc=DATA_CENTER))
    cluster = Cluster([host], port=port, execution_profiles={EXEC_PROFILE_DEFAULT: profile})
    try:
        connected = cluster.connect()
    except NoHostAvailable:
        cluster.shutdown()  # its reconnect threads would otherwise outlive the request
        raise               # -> 503 from the handler in main.py
    # Connect first, then look the keyspace up: connect(keyspace) reports a
    # missing keyspace as NoHostAvailable too, which would send you to Docker.
    if keyspace not in cluster.metadata.keyspaces:
        cluster.shutdown()
        raise HTTPException(503, f"Keyspace {keyspace} does not exist. Run python serving/apply_schema.py.")
    connected.set_keyspace(keyspace)
    return connected
