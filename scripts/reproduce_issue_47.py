"""Reproduction script for issue #47.

Issue: agent state is not persisted across API restarts, so in-progress
reviews lose all completed work when the server dies mid-run.

The script simulates the failure without needing Redis or the full API:

1. Start an orchestrator run where two tools complete successfully and the
   third raises a KeyboardInterrupt subclass, standing in for the API
   process being killed mid-run. KeyboardInterrupt is a BaseException, so
   the orchestrator's per-tool `except Exception` cannot swallow it, which
   matches how a real restart interrupts the loop.
2. Inspect the session store at the moment of the crash to see what, if
   anything, was persisted.
3. Simulate the restart by building a brand new Orchestrator (fresh
   in-memory ContextManager, same session store, same profile id) and
   re-running the same profile.
4. Count how many times each tool actually executed across both runs.

On main (pre-fix), the store is empty at crash time and both completed
tools run again from scratch on the retry. On the fix branch, each result
is checkpointed as it completes and the retry resumes via cache hits.

Usage:
    python scripts/reproduce_issue_47.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.memory.session_store import SessionStore  # noqa: E402
from agent.orchestrator import Orchestrator  # noqa: E402
from agent.tools.base import ToolResult  # noqa: E402


class SimulatedRestart(KeyboardInterrupt):
    """Stands in for the API process dying mid-run."""


class FakeSessionStore(SessionStore):
    """In-memory stand-in for the Redis SessionStore.

    JSON round-trips values on set/get so serialization behaves the same
    way it would against real Redis.
    """

    def __init__(self) -> None:
        self.data: dict[str, str] = {}

    def get(self, session_id: str) -> dict | None:
        raw = self.data.get(f"session:{session_id}")
        if not raw:
            return None
        parsed: dict = json.loads(raw)
        return parsed

    def set(self, session_id: str, data: dict, ttl_seconds: int = 3600) -> None:
        self.data[f"session:{session_id}"] = json.dumps(data)

    def delete(self, session_id: str) -> None:
        self.data.pop(f"session:{session_id}", None)


class CountingTool:
    """Tool that records how many times it executed."""

    def __init__(self, name: str, data: dict, crash_once: bool = False) -> None:
        self.name = name
        self.data = data
        self.calls = 0
        self.crash_once = crash_once

    def execute(self, input_data: dict) -> ToolResult:
        self.calls += 1
        if self.crash_once:
            self.crash_once = False
            raise SimulatedRestart(f"API process killed while running {self.name}")
        return ToolResult(success=True, data=self.data)


def main() -> int:
    store = FakeSessionStore()

    tech_detector = CountingTool("tech_detector", {"languages": ["python"]})
    readme_scorer = CountingTool("readme_scorer", {"score": 0.9})
    # skill_extractor is the third tool in the plan; it kills the process
    # the first time it runs, after the first two tools already finished.
    skill_extractor = CountingTool("skill_extractor", {"skills": ["fastapi"]}, crash_once=True)
    market_analyzer = CountingTool("market_analyzer", {"demand": "high"})

    tools = {
        "tech_detector": tech_detector,
        "readme_scorer": readme_scorer,
        "skill_extractor": skill_extractor,
        "market_analyzer": market_analyzer,
    }

    profile_data = {
        "files": ["app.py"],
        "readme_content": "# Demo",
        "resume_text": "python developer",
    }

    print("=" * 70)
    print("RUN 1: review starts, two tools finish, then the API dies")
    print("=" * 70)
    try:
        Orchestrator(tools, session_store=store).run("profile-47", profile_data)
        print("unexpected: run 1 finished without the simulated restart")
        return 1
    except SimulatedRestart as e:
        print(f"\n>>> simulated restart: {e}")

    completed_before_crash = tech_detector.calls + readme_scorer.calls
    print(f">>> tools completed before the crash: {completed_before_crash}")
    print(f">>> session store contents at crash time: {store.data or 'EMPTY'}")

    print()
    print("=" * 70)
    print("RUN 2: server is back up, same profile is re-run")
    print("=" * 70)
    Orchestrator(tools, session_store=store).run("profile-47", profile_data)

    print()
    print("=" * 70)
    print("RESULT")
    print("=" * 70)
    redone = 0
    for tool in (tech_detector, readme_scorer):
        print(f"{tool.name}: executed {tool.calls} time(s) total")
        if tool.calls > 1:
            redone += 1

    if redone:
        print(
            f"\nBUG REPRODUCED: {redone} tool result(s) that had already "
            "completed before the restart were thrown away and recomputed "
            "from scratch. Nothing was persisted until the full run finished."
        )
        return 1

    print(
        "\nFIXED BEHAVIOR: completed tool results were checkpointed to the "
        "session store as they finished, and the re-run resumed from the "
        "last completed step via cache hits."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
