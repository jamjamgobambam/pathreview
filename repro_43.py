"""Reproduce issue #43: agent session state not cleared between reviews.

Run from the repo root:  python repro_43.py

Scenario: the same user (profile_id) runs two reviews. Between reviews the
user's portfolio changes so the *plan* is different (a project/repo is
removed, so github_tool no longer runs). Because Orchestrator.run() loads the
previous session_state from Redis and does session_state.update(results),
stale results from the first review leak into the second review's stored
state -- they are never cleared/invalidated.
"""

import json

from agent.memory.session_store import SessionStore
from agent.orchestrator import Orchestrator
from agent.tools.base import BaseTool, ToolResult


class FakeRedis:
    """Minimal in-memory stand-in for redis.Redis used by SessionStore."""

    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, ttl, value):
        self.store[key] = value

    def delete(self, key):
        self.store.pop(key, None)


class EchoTool(BaseTool):
    def __init__(self, name):
        self.name = name
        self.description = name
        self.calls = 0

    def execute(self, input_data: dict) -> ToolResult:
        self.calls += 1
        return ToolResult(success=True, data={"tool": self.name, "input": input_data})


def main():
    tools = {
        "github_tool": EchoTool("github_tool"),
        "readme_scorer": EchoTool("readme_scorer"),
        "market_analyzer": EchoTool("market_analyzer"),
    }

    store = SessionStore(FakeRedis())
    orch = Orchestrator(tools, session_store=store)

    profile_id = "user-123"

    # --- Review 1: user has a GitHub repo + README ---
    profile_v1 = {
        "github_username": "janedoe",
        "projects": [{"github_repo": "weather-app"}],
        "readme_content": "# Weather App v1",
    }
    orch.run(profile_id, profile_v1)

    state_after_1 = json.loads(store.redis.store[f"session:{profile_id}"])
    print("After review 1, stored session keys:", sorted(state_after_1.keys()))

    # --- Review 2: user REMOVED the GitHub project, only README remains (updated) ---
    profile_v2 = {
        "readme_content": "# Weather App v2 (repo removed)",
    }
    # Fresh orchestrator to simulate a new request/process (new ContextManager),
    # but the SAME Redis-backed session store, as in production.
    orch2 = Orchestrator(tools, session_store=store)
    orch2.run(profile_id, profile_v2)

    state_after_2 = json.loads(store.redis.store[f"session:{profile_id}"])
    print("After review 2, stored session keys:", sorted(state_after_2.keys()))

    print("\n--- Diagnosis ---")
    if "github_tool" in state_after_2:
        print("BUG REPRODUCED: stale 'github_tool' result from review 1 is still")
        print("present in the session state after review 2, even though the user")
        print("removed that project and github_tool never ran in review 2.")
        print("Stale value:", state_after_2["github_tool"])
    else:
        print("No stale state -- bug not reproduced.")


if __name__ == "__main__":
    main()
