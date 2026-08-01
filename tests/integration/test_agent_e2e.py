"""End-to-end integration tests for the Orchestrator using fully stubbed tools."""

from unittest.mock import patch

import pytest

from agent.orchestrator import Orchestrator
from agent.tools.base import BaseTool, ToolResult

# ---------------------------------------------------------------------------
# Stub infrastructure
# ---------------------------------------------------------------------------


class StubSessionStore:
    """Dict-backed stub matching the SessionStore.get / .set interface.

    Orchestrator calls get(session_id) and set(session_id, data, ttl_seconds).
    delete() exists on the real SessionStore but is never called by the
    orchestrator, so it is intentionally omitted here.
    """

    def __init__(self) -> None:
        self.data: dict = {}

    def get(self, session_id: str) -> dict | None:
        return self.data.get(session_id)

    def set(self, session_id: str, data: dict, ttl_seconds: int = 3600) -> None:
        self.data[session_id] = data


class _CountingStub(BaseTool):
    """Shared base that tracks how many times execute() is called."""

    description = "stub"

    def __init__(self) -> None:
        self.call_count = 0

    def execute(self, input_data: dict) -> ToolResult:
        self.call_count += 1
        return ToolResult(success=True, data={"stub": True})


class StubGithubTool(_CountingStub):
    name = "github_tool"


class StubTechDetector(_CountingStub):
    name = "tech_detector"


class StubReadmeScorer(_CountingStub):
    name = "readme_scorer"


class StubSkillExtractor(_CountingStub):
    name = "skill_extractor"


class StubMarketAnalyzer(_CountingStub):
    name = "market_analyzer"


ALL_TOOL_NAMES = {
    "github_tool",
    "tech_detector",
    "readme_scorer",
    "skill_extractor",
    "market_analyzer",
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestOrchestratorE2E:
    """End-to-end tests for the Orchestrator using fully stubbed tools and session store."""

    @pytest.fixture
    def stub_store(self) -> StubSessionStore:
        return StubSessionStore()

    @pytest.fixture
    def all_stubs(self) -> dict[str, BaseTool]:
        return {
            "github_tool": StubGithubTool(),
            "tech_detector": StubTechDetector(),
            "readme_scorer": StubReadmeScorer(),
            "skill_extractor": StubSkillExtractor(),
            "market_analyzer": StubMarketAnalyzer(),
        }

    @pytest.fixture
    def orchestrator(
        self, all_stubs: dict[str, BaseTool], stub_store: StubSessionStore
    ) -> Orchestrator:
        return Orchestrator(tools=all_stubs, session_store=stub_store)  # type: ignore[arg-type]

    @pytest.fixture
    def full_profile(self) -> dict:
        """Profile data that triggers all five tools."""
        return {
            "github_username": "testuser",
            "projects": [{"github_repo": "testuser/repo"}],
            "files": [{"path": "main.py", "content": "print('hi')"}],
            "readme_content": "# My Project\nA cool project.",
            "resume_text": "Python developer with 5 years of experience.",
        }

    def test_happy_path_all_tools_called(
        self, orchestrator: Orchestrator, full_profile: dict, stub_store: StubSessionStore
    ) -> None:
        """All five tools run when a full profile is supplied."""
        profile_id = "profile-001"
        result = orchestrator.run(profile_id, full_profile)

        assert result["profile_id"] == profile_id
        assert result["tool_results"].keys() == ALL_TOOL_NAMES
        for tool_name in ALL_TOOL_NAMES:
            assert result["tool_results"][tool_name] == {"stub": True}

        assert stub_store.data[profile_id].keys() == ALL_TOOL_NAMES

    def test_partial_profile_skips_missing_tools(self, stub_store: StubSessionStore) -> None:
        """Tools whose trigger fields are absent are omitted from the plan."""
        stubs = {
            "readme_scorer": StubReadmeScorer(),
            "skill_extractor": StubSkillExtractor(),
            "market_analyzer": StubMarketAnalyzer(),
        }
        orc = Orchestrator(tools=stubs, session_store=stub_store)  # type: ignore[arg-type]
        profile_data = {
            "readme_content": "# Readme",
            "resume_text": "Some resume text",
        }

        result = orc.run("profile-002", profile_data)

        assert "github_tool" not in result["tool_results"]
        assert "tech_detector" not in result["tool_results"]
        for tool_name in ("readme_scorer", "skill_extractor", "market_analyzer"):
            assert result["tool_results"][tool_name] == {"stub": True}

    def test_tool_failure_is_isolated(
        self, all_stubs: dict[str, BaseTool], stub_store: StubSessionStore, full_profile: dict
    ) -> None:
        """A single failing tool returns an error dict; other tools still succeed."""

        class FailingTool(BaseTool):
            name = "readme_scorer"
            description = "stub that always raises"

            def __init__(self) -> None:
                self.call_count = 0

            def execute(self, input_data: dict) -> ToolResult:
                self.call_count += 1
                raise RuntimeError("boom")

        failing = FailingTool()
        all_stubs["readme_scorer"] = failing
        orc = Orchestrator(tools=all_stubs, session_store=stub_store)  # type: ignore[arg-type]

        with patch("agent.error_handling.time.sleep"):
            result = orc.run("profile-003", full_profile)

        assert result["tool_results"]["readme_scorer"] == {
            "error": "boom",
            "success": False,
        }
        # retry_with_backoff(max_retries=2) calls execute() twice before giving up
        assert failing.call_count == 2

        for tool_name in ALL_TOOL_NAMES - {"readme_scorer"}:
            assert result["tool_results"][tool_name] == {"stub": True}

    def test_session_persistence_write(
        self, orchestrator: Orchestrator, full_profile: dict, stub_store: StubSessionStore
    ) -> None:
        """After run(), stub_store holds tool_results keyed by profile_id."""
        profile_id = "profile-004"
        orchestrator.run(profile_id, full_profile)

        stored = stub_store.data[profile_id]
        assert stored
        assert stored.keys() == ALL_TOOL_NAMES

    def test_session_persistence_hydration(
        self, orchestrator: Orchestrator, full_profile: dict, stub_store: StubSessionStore
    ) -> None:
        """Pre-existing session keys survive after run() merges new results into them."""
        profile_id = "profile-005"
        stub_store.data[profile_id] = {"stale_key": "stale_value"}

        orchestrator.run(profile_id, full_profile)

        stored = stub_store.data[profile_id]
        assert stored.keys() >= ALL_TOOL_NAMES
        assert stored["stale_key"] == "stale_value"

    def test_empty_profile_produces_empty_results(
        self, stub_store: StubSessionStore, all_stubs: dict[str, BaseTool]
    ) -> None:
        """An empty profile_data dict produces an empty tool_results dict."""
        orc = Orchestrator(tools=all_stubs, session_store=stub_store)  # type: ignore[arg-type]
        result = orc.run("profile-006", {})

        assert result["tool_results"] == {}
        assert result["cached_results"] == {}

    def test_repeated_run_uses_cache(
        self, orchestrator: Orchestrator, full_profile: dict, all_stubs: dict[str, BaseTool]
    ) -> None:
        """Calling run() twice with the same input only executes each tool once."""
        orchestrator.run("profile-007", full_profile)
        orchestrator.run("profile-007", full_profile)

        for stub in all_stubs.values():
            assert stub.call_count == 1, f"{stub.name} was called {stub.call_count} times"  # type: ignore[attr-defined]
