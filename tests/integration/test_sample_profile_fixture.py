"""Integration tests for the basic_profile.json fixture.

These tests load tests/fixtures/sample_profiles/basic_profile.json and validate
that it contains a well-formed portfolio that the agent pipeline can consume.
They skip automatically when the fixture file is absent, which is the exact
symptom described in issue #106.
"""

import json
from pathlib import Path
from typing import Any

import pytest

# Resolve path relative to this file so it works regardless of cwd
FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "fixtures"
    / "sample_profiles"
    / "basic_profile.json"
)

# All tests in this module skip when the fixture is missing — that is the
# reproduction of issue #106: deleting the file causes silent test skips.
pytestmark = pytest.mark.skipif(
    not FIXTURE_PATH.exists(),
    reason=(
        f"Fixture file missing: {FIXTURE_PATH}. "
        "Reproduces issue #106 — restore the file to un-skip these tests."
    ),
)


@pytest.fixture(scope="module")
def basic_profile() -> Any:
    """Load basic_profile.json once for the entire module."""
    with open(FIXTURE_PATH, encoding="utf-8") as fh:
        return json.load(fh)


@pytest.mark.integration
class TestBasicProfileFixtureStructure:
    """Validate the top-level structure of basic_profile.json."""

    def test_fixture_loads_as_valid_json(self, basic_profile: Any) -> None:
        """Fixture file parses as a non-empty dict."""
        assert isinstance(basic_profile, dict)
        assert basic_profile, "Fixture must not be empty"

    def test_fixture_has_github_username(self, basic_profile: Any) -> None:
        """Fixture includes a non-empty github_username string."""
        assert "github_username" in basic_profile, "Missing key: github_username"
        assert isinstance(basic_profile["github_username"], str)
        assert basic_profile["github_username"].strip(), "github_username must not be blank"

    def test_fixture_has_resume_text(self, basic_profile: Any) -> None:
        """Fixture includes a non-empty resume_text string."""
        assert "resume_text" in basic_profile, "Missing key: resume_text"
        assert isinstance(basic_profile["resume_text"], str)
        assert len(basic_profile["resume_text"].strip()) > 0, "resume_text must not be blank"

    def test_fixture_has_projects_list(self, basic_profile: Any) -> None:
        """Fixture includes a 'projects' list."""
        assert "projects" in basic_profile, "Missing key: projects"
        assert isinstance(basic_profile["projects"], list), "projects must be a list"

    def test_fixture_has_exactly_two_repositories(self, basic_profile: Any) -> None:
        """Fixture contains data for exactly two repositories (per issue spec)."""
        projects = basic_profile["projects"]
        assert len(projects) == 2, (
            f"Expected 2 repositories, got {len(projects)}. "
            "Issue #106 specifies a two-repo sample portfolio."
        )


@pytest.mark.integration
class TestBasicProfileRepositoryFields:
    """Validate each repository entry inside basic_profile.json."""

    def test_each_repository_has_github_repo_key(self, basic_profile: Any) -> None:
        """Every project entry exposes a github_repo name for the GitHubTool."""
        for i, project in enumerate(basic_profile["projects"]):
            assert "github_repo" in project, (
                f"projects[{i}] is missing 'github_repo' — "
                "the orchestrator uses this key to fetch repo metadata"
            )
            assert isinstance(project["github_repo"], str)
            assert project["github_repo"].strip()

    def test_each_repository_has_name_and_description(self, basic_profile: Any) -> None:
        """Every project entry has a human-readable name and description."""
        for i, project in enumerate(basic_profile["projects"]):
            assert "name" in project, f"projects[{i}] missing 'name'"
            assert "description" in project, f"projects[{i}] missing 'description'"
            assert project["name"].strip(), f"projects[{i}] name must not be blank"

    def test_each_repository_has_readme_content(self, basic_profile: Any) -> None:
        """Every project entry includes readme_content for the README scorer."""
        for i, project in enumerate(basic_profile["projects"]):
            assert "readme_content" in project, (
                f"projects[{i}] missing 'readme_content' — "
                "the orchestrator passes this to the readme_scorer tool"
            )
            assert isinstance(project["readme_content"], str)
            assert project["readme_content"].strip()

    def test_repositories_have_distinct_names(self, basic_profile: Any) -> None:
        """The two repositories have different names (not duplicates)."""
        names = [p["github_repo"] for p in basic_profile["projects"]]
        assert len(set(names)) == len(names), "Repository names must be unique"


@pytest.mark.integration
class TestBasicProfileOrchestratorCompatibility:
    """Validate basic_profile.json is compatible with Orchestrator._build_plan."""

    def test_orchestrator_build_plan_accepts_fixture(self, basic_profile: Any) -> None:
        """Orchestrator._build_plan runs without error on the fixture data."""
        from agent.orchestrator import Orchestrator

        orchestrator = Orchestrator(tools={})
        # _build_plan should not raise even with no tools registered
        plan = orchestrator._build_plan(basic_profile)
        assert isinstance(plan, list)

    def test_resume_text_feeds_skill_extractor_step(self, basic_profile: Any) -> None:
        """resume_text key means the orchestrator queues a skill_extractor step."""
        from agent.orchestrator import Orchestrator

        orchestrator = Orchestrator(tools={})
        plan = orchestrator._build_plan(basic_profile)
        tool_names = [step[0] for step in plan]
        assert (
            "skill_extractor" in tool_names
        ), "Orchestrator should queue skill_extractor when resume_text is present"
