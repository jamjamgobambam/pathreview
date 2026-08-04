"""Tests for agent.tools.tool_dependencies (issue #54)."""

import pytest

from agent.tools.tool_dependencies import (
    TOOL_DEPENDENCIES,
    find_cycle,
    unmet_prerequisites,
    validate_plan,
)


@pytest.mark.unit
class TestValidatePlan:
    """Structural validation of a plan against the dependency graph."""

    def test_valid_plan_has_no_errors(self):
        """Prerequisites ordered before their dependent produce no errors."""
        plan = [("tech_detector", {}), ("skill_extractor", {}), ("market_analyzer", {})]
        assert validate_plan(plan) == []

    def test_dependent_before_prerequisites_is_flagged(self):
        """market_analyzer ahead of both prerequisites yields one error each."""
        plan = [("market_analyzer", {}), ("skill_extractor", {}), ("tech_detector", {})]
        errors = validate_plan(plan)
        assert len(errors) == 2
        assert any("skill_extractor" in e for e in errors)
        assert any("tech_detector" in e for e in errors)

    def test_absent_prerequisite_is_not_a_structural_error(self):
        """A prerequisite missing from the plan is left to run-time gating."""
        plan = [("market_analyzer", {})]
        assert validate_plan(plan) == []

    def test_empty_plan_is_valid(self):
        """An empty plan is trivially valid."""
        assert validate_plan([]) == []

    def test_cycle_in_graph_is_reported(self):
        """A cyclic dependency graph is reported as a single error."""
        cyclic = {"a": ["b"], "b": ["a"]}
        errors = validate_plan([("a", {})], cyclic)
        assert len(errors) == 1
        assert "cycle" in errors[0].lower()

    def test_duplicate_tool_entries_do_not_false_positive(self):
        """A tool appearing twice after its prerequisites is still valid."""
        plan = [
            ("tech_detector", {}),
            ("skill_extractor", {}),
            ("market_analyzer", {}),
            ("market_analyzer", {}),
        ]
        assert validate_plan(plan) == []


@pytest.mark.unit
class TestFindCycle:
    """Cycle detection on dependency graphs."""

    def test_default_graph_is_acyclic(self):
        """The shipped TOOL_DEPENDENCIES graph is a DAG."""
        assert find_cycle(TOOL_DEPENDENCIES) is None

    def test_self_dependency_is_a_cycle(self):
        """A node depending on itself is detected as a cycle."""
        assert find_cycle({"a": ["a"]}) is not None


@pytest.mark.unit
class TestUnmetPrerequisites:
    """Run-time prerequisite gating."""

    def test_all_prerequisites_missing(self):
        """With nothing completed, every prerequisite is unmet."""
        assert unmet_prerequisites("market_analyzer", {}) == ["skill_extractor", "tech_detector"]

    def test_all_prerequisites_satisfied(self):
        """With prerequisites succeeded, none are unmet."""
        completed = {"skill_extractor": True, "tech_detector": True}
        assert unmet_prerequisites("market_analyzer", completed) == []

    def test_failed_prerequisite_counts_as_unmet(self):
        """A prerequisite that ran but failed is still unmet."""
        completed = {"skill_extractor": True, "tech_detector": False}
        assert unmet_prerequisites("market_analyzer", completed) == ["tech_detector"]

    def test_tool_with_no_prerequisites(self):
        """A tool with no declared prerequisites is never gated."""
        assert unmet_prerequisites("tech_detector", {}) == []
