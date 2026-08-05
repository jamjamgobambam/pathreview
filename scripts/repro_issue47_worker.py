"""Worker process for issue #47 repro.

Runs ONE Orchestrator.run() pass over a fixed 3-step plan (tool_a, tool_b,
tool_c). If invoked with a tool name as argv[1], that tool hard-crashes the
process (os._exit) right after logging that it ran -- simulating the API
server dying mid-review, before Orchestrator.run() ever reaches its final
session_store.set() call.

Usage: python scripts/repro_issue47_worker.py [crash_on_tool_name]
"""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import redis  # noqa: E402

from agent.memory.session_store import SessionStore  # noqa: E402
from agent.orchestrator import Orchestrator  # noqa: E402
from agent.tools.base import BaseTool, ToolResult  # noqa: E402

LOG_FILE = "/tmp/repro_issue47_log.txt"
PROFILE_ID = "repro-profile-1"


def log(msg: str) -> None:
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")


class FakeTool(BaseTool):
    def __init__(self, name: str, crash: bool):
        self.name = name
        self.description = f"fake tool {name}"
        self.crash = crash

    def execute(self, input_data: dict) -> ToolResult:
        log(f"EXECUTED {self.name}")
        if self.crash:
            log(f"CRASHING during {self.name} (simulating server restart)")
            os._exit(1)
        return ToolResult(success=True, data={"tool": self.name})


class FixedPlanOrchestrator(Orchestrator):
    """Skips the real _build_plan (which reads profile_data shape) and just
    always runs a fixed 3-step plan, so we can isolate the persistence bug."""

    def _build_plan(self, profile_data: dict) -> list[tuple[str, dict]]:
        return [("tool_a", {}), ("tool_b", {}), ("tool_c", {})]


def main() -> None:
    crash_on = sys.argv[1] if len(sys.argv) > 1 else None

    tools = {
        name: FakeTool(name, crash=(name == crash_on)) for name in ("tool_a", "tool_b", "tool_c")
    }

    client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    store = SessionStore(client)
    orch = FixedPlanOrchestrator(tools=tools, session_store=store)

    result = orch.run(PROFILE_ID, {})
    log(f"RUN COMPLETED: {sorted(result['tool_results'].keys())}")


if __name__ == "__main__":
    main()
