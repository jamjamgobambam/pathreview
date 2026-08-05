"""Reproduction driver for issue #47 (agent state not persisted on restart).

Run 1: simulates the API server dying partway through a review's tool plan
        -- tool_a succeeds, then the process is killed during tool_b.
Run 2: simulates the server restarting and the same review being re-attempted.

What this proves:
  - After the crash, Redis has NOTHING saved for the profile, even though
    tool_a completed successfully -- because Orchestrator.run() only writes
    to session_store at the very end of the loop (agent/orchestrator.py:65-67).
  - On the "restart" run, tool_a executes again from scratch. There is no
    checkpoint to consult, so no already-completed step can be skipped.

Prereq: Redis reachable at localhost:6379 (`docker compose up -d redis`).
Run:    .venv/bin/python scripts/repro_issue47.py
"""

import os
import subprocess
import sys

import redis

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKER = os.path.join(REPO_ROOT, "scripts", "repro_issue47_worker.py")
LOG_FILE = "/tmp/repro_issue47_log.txt"
PROFILE_ID = "repro-profile-1"


def run_worker(crash_on: str) -> None:
    subprocess.run([sys.executable, WORKER, crash_on])


def main() -> None:
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    client.delete(f"session:{PROFILE_ID}")

    print("=== Run 1: server crashes during tool_b (after tool_a succeeded) ===")
    run_worker(crash_on="tool_b")

    saved = client.get(f"session:{PROFILE_ID}")
    print(f"Redis state after crash: {saved!r}\n")

    print("=== Run 2: server 'restarts', same review re-attempted ===")
    run_worker(crash_on="")

    saved = client.get(f"session:{PROFILE_ID}")
    print(f"Redis state after run 2: {saved!r}\n")

    print("=== Execution log across both runs ===")
    with open(LOG_FILE) as f:
        print(f.read())


if __name__ == "__main__":
    main()
