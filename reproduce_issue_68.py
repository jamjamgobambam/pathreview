"""Reproduce issue #68: get_event_count ignores window_hours.

WHY get_event_count STRUCTURALLY CANNOT HONOR window_hours
==========================================================
`SafetyMonitor.log_event` stores each event as a single flat integer
counter in Redis, keyed only by event type:

    key = f"safety:events:{event_type}"
    self.redis.incr(key)            # one number, monotonically increasing
    self.redis.expire(key, 86400)   # whole key expires after 24h

There is NO per-event timestamp anywhere. Every call to log_event just
bumps one counter; the individual events and the times they occurred are
not retained. Redis only knows "this many events total" plus a single
24h TTL on the key as a whole.

`get_event_count` then does:

    count = self.redis.get(key)     # reads that one number
    return int(count) if count else 0

It never looks at `window_hours` at all. Because the underlying data is a
single scalar with no time dimension, there is simply nothing to filter
on -- you cannot reconstruct "how many events in the last hour" from a
lone total. Therefore get_event_count(window_hours=1) and
get_event_count(window_hours=24) return the identical total, and would do
so for ANY window value. Honoring a time window would require storing
per-event timestamps (e.g. a Redis sorted set scored by time, or
time-bucketed keys) -- a different data model than the flat counter.

This script demonstrates the defect empirically.

Requires a running Redis on localhost:6379 (or set REDIS_URL).
Run from the repo root:  python reproduce_issue_68.py
"""

import os

import redis

from safety.monitoring import SafetyMonitor


def main() -> None:
    redis_url = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
    client = redis.Redis.from_url(redis_url, decode_responses=True)

    event_type = "pii_detected"
    key = f"safety:events:{event_type}"

    # Start from a clean slate so the demonstration is deterministic.
    client.delete(key)

    monitor = SafetyMonitor(client)

    # (1) Log a few safety events.
    print("=== (1) Logging safety events ===")
    for i in range(5):
        monitor.log_event(event_type, {"detail": f"sample event #{i}"})
    print(f"Logged 5 '{event_type}' events via log_event()\n")

    # (2) Directly inspect the Redis key that log_event writes to.
    print("=== (2) Inspecting the Redis key directly ===")
    print(f"Key name : {key}")
    print(f"Redis type: {client.type(key)}")  # 'string' -- INCR stores an int as a string
    print(f"Value     : {client.get(key)!r}")
    ttl = client.ttl(key)
    print(f"TTL (sec) : {ttl}  (single 24h TTL on the whole key -- no per-event timing)\n")

    # (3) Call get_event_count with two different windows.
    print("=== (3) get_event_count with different windows ===")
    count_1h = monitor.get_event_count(event_type, window_hours=1)
    count_24h = monitor.get_event_count(event_type, window_hours=24)
    print(f"get_event_count(window_hours=1)  -> {count_1h}")
    print(f"get_event_count(window_hours=24) -> {count_24h}")

    print()
    if count_1h == count_24h:
        print(
            "BUG CONFIRMED: both windows returned the same total "
            f"({count_1h}). window_hours has no effect -- the flat counter "
            "cannot honor a time window."
        )
    else:
        print("Unexpected: the two windows returned different values.")


if __name__ == "__main__":
    main()
