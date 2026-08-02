import uuid
from typing import Any
from unittest.mock import MagicMock, Mock

import pytest


class InMemorySessionStore:
    """Mock in-memory session store for testing."""

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    def get(self, key: str) -> Any:
        return self._store.get(key)

    def set(self, key: str, value: dict[str, Any]) -> None:
        self._store[key] = value

    def delete(self, key: str) -> None:
        self._store.pop(key, None)


@pytest.fixture
def session_store() -> InMemorySessionStore:
    return InMemorySessionStore()


@pytest.fixture
def mock_context_manager() -> Mock:
    cm = Mock()
    cm.get_all_results.return_value = {}
    return cm


@pytest.fixture
def orchestrator(
    session_store: InMemorySessionStore,
    mock_context_manager: Mock,
) -> Any:
    """Instantiate orchestrator with mocked dependencies."""

    class Orchestrator:

        def __init__(
            self,
            session_store: InMemorySessionStore,
            context_manager: Mock,
        ) -> None:
            self.session_store = session_store
            self.context_manager = context_manager

        def _build_plan(self, profile_data: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
            # Return custom plan if provided in profile_data for test flexibility
            default_plan = [("github_analyzer", {"user": "octocat"})]
            return profile_data.get("mock_plan", default_plan)

        def _execute_tool(self, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
            return {"status": "ok", "executed": tool_name}

        def run(
            self,
            profile_id: str,
            profile_data: dict[str, Any],
            review_id: str | None = None,
        ) -> dict[str, Any]:
            effective_review_id = review_id or profile_data.get("review_id") or str(uuid.uuid4())
            session_key = f"{profile_id}:{effective_review_id}"

            plan = self._build_plan(profile_data)

            session_state: dict[str, Any] = {}
            if self.session_store:
                session_state = self.session_store.get(session_key) or {}

            results: dict[str, Any] = {}
            for tool_name, tool_input in plan:
                try:
                    result = self._execute_tool(tool_name, tool_input)
                    if isinstance(result, dict):
                        results[tool_name] = result.get("data", result)
                    elif hasattr(result, "data"):
                        results[tool_name] = result.data
                    else:
                        results[tool_name] = result
                except Exception as e:
                    results[tool_name] = {"error": str(e), "success": False}

            if self.session_store:
                session_state.update(results)
                self.session_store.set(session_key, session_state)

            return {
                "profile_id": profile_id,
                "review_id": effective_review_id,
                "tool_results": results,
                "cached_results": self.context_manager.get_all_results(),
            }

    return Orchestrator(session_store, mock_context_manager)


def test_session_isolation_between_distinct_reviews(
    orchestrator: Any, session_store: InMemorySessionStore
) -> None:
    """Verify that state from run #1 does not leak into run #2 for the same profile_id."""
    profile_id = "user_profile_123"

    # Run 1: Executes tool_a and tool_b
    data_run_1: dict[str, Any] = {
        "mock_plan": [
            ("tool_a", {"arg": 1}),
            ("tool_b", {"arg": 2}),
        ]
    }
    res_1 = orchestrator.run(profile_id, data_run_1, review_id="review_run_001")

    # Key check 1: Run 1 output has both tools
    assert "tool_a" in res_1["tool_results"]
    assert "tool_b" in res_1["tool_results"]
    assert session_store.get(f"{profile_id}:review_run_001") is not None

    # Run 2: Executes ONLY tool_c for the exact same profile_id
    data_run_2: dict[str, Any] = {"mock_plan": [("tool_c", {"arg": 3})]}
    res_2 = orchestrator.run(profile_id, data_run_2, review_id="review_run_002")

    # Key check 2: Run 2 MUST NOT contain tool_a or tool_b from Run 1
    assert "tool_c" in res_2["tool_results"]
    assert "tool_a" not in res_2["tool_results"]
    assert "tool_b" not in res_2["tool_results"]

    # Verify session store stored both runs under separate composite keys
    store_run_1 = session_store.get(f"{profile_id}:review_run_001")
    store_run_2 = session_store.get(f"{profile_id}:review_run_002")

    assert "tool_a" in store_run_1
    assert "tool_a" not in store_run_2


def test_auto_generates_review_id_when_omitted(
    orchestrator: Any, session_store: InMemorySessionStore
) -> None:
    """Verify that unique review IDs are generated automatically if not provided."""
    profile_id = "user_profile_456"
    profile_data: dict[str, Any] = {"mock_plan": [("tool_a", {})]}

    res_1 = orchestrator.run(profile_id, profile_data)
    res_2 = orchestrator.run(profile_id, profile_data)

    assert res_1["review_id"] != res_2["review_id"]
    assert len(session_store._store) == 2


def test_tool_failure_isolation(orchestrator: Any) -> None:
    """Verify that a failing tool records an error without throwing an unhandled exception."""
    orchestrator._execute_tool = MagicMock(side_effect=RuntimeError("API limit exceeded"))

    profile_data: dict[str, Any] = {"mock_plan": [("failing_tool", {})]}
    res = orchestrator.run("profile_789", profile_data, review_id="err_run")

    assert res["tool_results"]["failing_tool"] == {
        "error": "API limit exceeded",
        "success": False,
    }
