from typing import Any

from agent.memory.session_store import SessionStore
from agent.orchestrator import Orchestrator


class FakeRedis:
    """Minimal fake Redis compatible interface for testing."""

    def __init__(self) -> None:
        self.store: dict[str, Any] = {}

    def get(self, key: str) -> Any | None:
        return self.store.get(key)

    def setex(self, key: str, ttl: int, value: str) -> None:
        # store value as JSON string to mimic redis behavior
        self.store[key] = value

    def delete(self, key: str) -> None:
        self.store.pop(key, None)


class ToolResult:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data


class DummyTool:
    name = "skill_extractor"

    def __init__(self) -> None:
        self.count: int = 0

    def execute(self, input_data: dict[str, Any]) -> ToolResult:
        # Increment an execution counter so test can assert whether tool ran
        self.count += 1
        return ToolResult({"executions": self.count})


def test_orchestrator_should_use_session_store_results_in_new_instance() -> None:
    """
    Reproduction test (intentionally asserting the expected behavior):

    The orchestrator should reuse results persisted to the session store when a
    new Orchestrator instance is created for the same profile_id. The current
    implementation loads session_state from Redis but does not use it to avoid
    re-executing tools, so this test documents that gap by failing under the
    current behavior.

    Steps:
    - Run orchestrator (instance A) to produce and persist results
    - Create a new orchestrator (instance B) with the same SessionStore
    - Run orchestrator B and assert that the tool was NOT re-executed

    Expected (correct) behavior: tool.count == 1 after second run (reused cached result)
    Current (observed) behavior: tool.count == 2 because session_state is loaded but ignored
    """
    fake_redis = FakeRedis()
    session_store = SessionStore(fake_redis)  # type: ignore[arg-type]

    tool = DummyTool()
    tools: dict[str, DummyTool] = {"skill_extractor": tool}

    profile_id = "user-123"
    profile_data: dict[str, str] = {"resume_text": "initial resume content"}

    # First orchestrator instance -> executes tool and persists results
    orch1 = Orchestrator(tools, session_store=session_store)
    _ = orch1.run(profile_id, profile_data)
    assert tool.count == 1

    # New orchestrator instance (simulating a separate request/process)
    orch2 = Orchestrator(tools, session_store=session_store)
    _ = orch2.run(profile_id, profile_data)

    # The correct implementation would reuse the persisted session result and
    # not execute the tool again. This assertion documents that expected
    # behavior; currently this test will fail because tool.count == 2.
    assert (
        tool.count == 1
    ), "Orchestrator re-executed the tool instead of using session store results"
