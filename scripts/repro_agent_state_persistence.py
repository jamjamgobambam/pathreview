"""Verify issue #47 fix: agent session state is checkpointed mid-run.

After the fix, Orchestrator.run() writes to Redis after each tool. Killing the
process mid-plan leaves a partial session; a restarted run skips finished tools
and continues from the checkpoint.

Usage:
    docker compose up -d
    source .venv/bin/activate
    python scripts/repro_agent_state_persistence.py
"""

from __future__ import annotations

import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import redis

# Make repo imports work when run as: python scripts/this_file.py
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent.memory.session_store import SessionStore  # noqa: E402
from agent.orchestrator import Orchestrator  # noqa: E402
from agent.tools.base import BaseTool, ToolResult  # noqa: E402
from core.config import settings  # noqa: E402

PROFILE_ID = "repro-issue-47"
TOOL_SLEEP_SECONDS = 2.0
# Kill after ~2 tools finish (each sleeps 2s) but before the full 5-tool plan ends.
KILL_AFTER_SECONDS = 5.0


class SlowMockTool(BaseTool):
    """Stand-in for a real agent tool; sleeps to simulate slow work."""

    def __init__(self, name: str, sleep_seconds: float = TOOL_SLEEP_SECONDS):
        self.name = name
        self.description = f"Slow mock for {name}"
        self.sleep_seconds = sleep_seconds
        self.call_count = 0

    def execute(self, input_data: dict) -> ToolResult:
        self.call_count += 1
        print(f"  [{self.name}] starting (call #{self.call_count})...", flush=True)
        time.sleep(self.sleep_seconds)
        print(f"  [{self.name}] done", flush=True)
        return ToolResult(
            success=True,
            data={"tool": self.name, "input": input_data, "call": self.call_count},
        )


def build_tools(sleep_seconds: float = TOOL_SLEEP_SECONDS) -> dict[str, SlowMockTool]:
    names = [
        "github_tool",
        "tech_detector",
        "readme_scorer",
        "skill_extractor",
        "market_analyzer",
    ]
    return {name: SlowMockTool(name, sleep_seconds=sleep_seconds) for name in names}


def build_profile_data() -> dict:
    """Profile that produces a 5-tool Orchestrator plan."""
    return {
        "github_username": "repro-user",
        "projects": [{"github_repo": "repro-repo"}],
        "files": ["main.py", "requirements.txt"],
        "readme_content": "# Repro Repo\n\nDemonstration readme for issue #47.",
        "resume_text": "Software engineer with Python and FastAPI experience.",
        "repo_metadata": {"stars": 0},
    }


def session_key(profile_id: str = PROFILE_ID) -> str:
    return f"session:{profile_id}"


def redis_client() -> redis.Redis:
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


def clear_session(client: redis.Redis) -> None:
    client.delete(session_key())


def session_exists(client: redis.Redis) -> bool:
    return bool(client.exists(session_key()))


def load_session(client: redis.Redis) -> dict:
    raw = client.get(session_key())
    if not raw:
        return {}
    parsed = json.loads(raw)
    return parsed if isinstance(parsed, dict) else {}


def _child_run_until_killed() -> None:
    """Child process: long Orchestrator.run() that the parent will interrupt."""
    client = redis_client()
    store = SessionStore(client)
    tools = build_tools()
    orch = Orchestrator(tools=tools, session_store=store, tool_timeout=60.0)

    print("\n=== Interrupted mid-run (child process) ===", flush=True)
    orch.run(PROFILE_ID, build_profile_data())
    print("  WARNING: run finished before kill — increase KILL_AFTER_SECONDS", flush=True)


def run_interrupted() -> None:
    """Spawn child → wait partway through the plan → kill child."""
    print("\n=== Step 1: Start multi-tool run, kill mid-plan ===", flush=True)
    proc = mp.Process(target=_child_run_until_killed, name="orchestrator-repro")
    proc.start()
    time.sleep(KILL_AFTER_SECONDS)

    if not proc.is_alive():
        print("  FAIL: child exited before kill window — tools may be too fast", flush=True)
        proc.join()
        sys.exit(1)

    print(f"  killing child pid={proc.pid} after {KILL_AFTER_SECONDS}s...", flush=True)
    proc.terminate()
    proc.join(timeout=5)
    if proc.is_alive():
        proc.kill()
        proc.join(timeout=2)


def main() -> int:
    print("Issue #47 verification — mid-run checkpoints + resume")
    print(f"Redis: {settings.redis_url}")
    print(f"Session key: {session_key()}")

    client = redis_client()
    try:
        client.ping()
    except redis.ConnectionError as exc:
        print(f"\nFAIL: cannot reach Redis ({exc})")
        print("Start infra first: docker compose up -d")
        return 1

    clear_session(client)
    print("Cleared any existing repro session key.")

    # ===================================================================
    # STEP 1 — Interrupt mid-run
    # ===================================================================
    run_interrupted()

    # ===================================================================
    # STEP 2 — After fix: Redis MUST have a partial checkpoint
    # ===================================================================
    mid_run_persisted = session_exists(client)
    partial = load_session(client)
    print("\n=== Step 2: Inspect Redis after kill ===", flush=True)
    print(f"  {session_key()} exists? {mid_run_persisted}", flush=True)
    print(f"  checkpointed steps: {len(partial)}", flush=True)

    if not mid_run_persisted or len(partial) == 0:
        print(
            "  FAIL: no Redis checkpoint after mid-run kill "
            "(bug still present — SessionStore.set only at end?).",
            flush=True,
        )
        return 1

    if len(partial) >= 5:
        print(
            "  FAIL: full session written — kill window too late; " "decrease KILL_AFTER_SECONDS.",
            flush=True,
        )
        return 1

    print(
        f"  OBSERVED: partial checkpoint kept ({len(partial)} step(s) survived the kill).",
        flush=True,
    )
    checkpointed_before_resume = set(partial.keys())

    # ===================================================================
    # STEP 3 — Resume: only remaining tools should execute
    # ===================================================================
    print("\n=== Step 3: Fresh process resumes from checkpoint ===", flush=True)
    store = SessionStore(client)
    tools = build_tools(sleep_seconds=0.05)
    orch = Orchestrator(tools=tools, session_store=store, tool_timeout=60.0)
    result = orch.run(PROFILE_ID, build_profile_data())

    executed_again = [name for name, tool in tools.items() if tool.call_count > 0]
    skipped = [name for name, tool in tools.items() if tool.call_count == 0]
    print(f"  tools re-executed: {executed_again}", flush=True)
    print(f"  tools skipped (resumed): {skipped}", flush=True)
    print(f"  final tool_results: {list(result['tool_results'].keys())}", flush=True)

    if not skipped:
        print("  FAIL: expected at least one tool to be skipped from Redis resume", flush=True)
        return 1

    if len(result["tool_results"]) != 5:
        print("  FAIL: expected full 5-tool results after resume", flush=True)
        return 1

    # ===================================================================
    # STEP 4 — Session is complete after resume
    # ===================================================================
    final = load_session(client)
    print("\n=== Step 4: Session after resume ===", flush=True)
    print(f"  total checkpointed steps: {len(final)}", flush=True)
    print(f"  steps that existed before resume: {len(checkpointed_before_resume)}", flush=True)

    if len(final) < 5:
        print("  FAIL: expected all plan steps checkpointed after resume", flush=True)
        return 1

    print("\n=== Verdict ===")
    print(
        "FIX VERIFIED: mid-run kill left a Redis checkpoint; resume skipped "
        "finished tools and completed the remaining plan."
    )

    clear_session(client)
    return 0


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    raise SystemExit(main())
