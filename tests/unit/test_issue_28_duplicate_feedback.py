"""Tests for issue #28 — duplicate feedback across same-stack projects.

Issue: Generator produces duplicate feedback sections when a user has multiple
projects in the same tech stack.
https://github.com/ascherj/pathreview/issues/28

When a user has several projects built with the same stack (e.g. three Python
projects), the review generator emits a near-identical "Python skills"
observation for each one. ``ReviewGenerator._consolidate_feedback`` now groups
sections by content similarity and merges each group into a single
cross-project comment, instead of deduplicating by ``section_name`` alone.

These tests started as a reproduction (originally ``xfail``) and now assert the
fixed behavior plus the edge cases documented in PLAN.md.
"""

import json

import pytest

from rag.generator.output_parser import FeedbackSection, parse_review_output
from rag.generator.review_generator import ReviewGenerator

PY_SKILLS = (
    "Strong Python fundamentals: clean use of type hints, virtual environments, "
    "and pytest. Consider adding more docstrings."
)


def _three_same_stack_projects() -> str:
    """Return an LLM JSON payload for three Python projects with identical feedback."""
    return json.dumps(
        {
            "skills_feedback_flask_api": {
                "content": PY_SKILLS,
                "suggestions": ["Add docstrings"],
            },
            "skills_feedback_data_pipeline": {
                "content": PY_SKILLS,
                "suggestions": ["Add docstrings"],
            },
            "skills_feedback_cli_tool": {
                "content": PY_SKILLS,
                "suggestions": ["Add docstrings"],
            },
        }
    )


@pytest.mark.unit
class TestIssue28DuplicateFeedback:
    """Consolidation of duplicate cross-project feedback (issue #28)."""

    def test_parsing_yields_one_section_per_project(self) -> None:
        """The parser produces one section per project (input to consolidation)."""
        sections = parse_review_output(_three_same_stack_projects())
        assert len(sections) == 3
        assert all(PY_SKILLS in s.content for s in sections)

    def test_consolidation_merges_duplicate_cross_project_feedback(self) -> None:
        """Identical feedback across same-stack projects collapses to one section."""
        sections = parse_review_output(_three_same_stack_projects())

        consolidated = ReviewGenerator._consolidate_feedback(sections)

        duplicates = [s for s in consolidated if PY_SKILLS in s.content]
        assert len(duplicates) == 1, (
            f"Expected duplicate Python-skills feedback to be consolidated to 1 "
            f"section, but found {len(duplicates)}."
        )

    def test_merged_section_records_all_projects(self) -> None:
        """The consolidated section names every project it was merged from."""
        sections = parse_review_output(_three_same_stack_projects())

        consolidated = ReviewGenerator._consolidate_feedback(sections)

        merged = consolidated[0]
        assert set(merged.projects) == {
            "skills_feedback_flask_api",
            "skills_feedback_data_pipeline",
            "skills_feedback_cli_tool",
        }

    def test_near_identical_content_is_consolidated(self) -> None:
        """Near-identical (not byte-identical) observations are still merged."""
        base = "Solid Python skills across the project: good use of type hints and tests."
        payload = json.dumps(
            {
                "proj_a": {"content": base + " Overall a strong effort.", "suggestions": []},
                "proj_b": {"content": base + " Overall a strong effort here.", "suggestions": []},
            }
        )
        consolidated = ReviewGenerator._consolidate_feedback(parse_review_output(payload))
        assert len(consolidated) == 1

    def test_distinct_feedback_is_preserved(self) -> None:
        """Genuinely different feedback is not merged."""
        payload = json.dumps(
            {
                "python_project": {
                    "content": "Excellent Python typing discipline.",
                    "suggestions": [],
                },
                "docs_gap": {
                    "content": "The README is missing setup instructions.",
                    "suggestions": [],
                },
            }
        )
        consolidated = ReviewGenerator._consolidate_feedback(parse_review_output(payload))
        assert len(consolidated) == 2

    def test_suggestions_are_unioned_and_deduped(self) -> None:
        """Merging unions suggestions across the group without duplicates."""
        payload = json.dumps(
            {
                "a": {"content": PY_SKILLS, "suggestions": ["Add docstrings", "Add CI"]},
                "b": {"content": PY_SKILLS, "suggestions": ["Add docstrings", "Add badges"]},
            }
        )
        merged = ReviewGenerator._consolidate_feedback(parse_review_output(payload))[0]
        assert merged.suggestions == ["Add docstrings", "Add CI", "Add badges"]

    def test_empty_list_returns_empty(self) -> None:
        """No sections in, no sections out."""
        assert ReviewGenerator._consolidate_feedback([]) == []

    def test_single_section_unchanged(self) -> None:
        """A single section passes through untouched (no merge, no projects tag)."""
        section = FeedbackSection(
            section_name="skills_feedback", content=PY_SKILLS, confidence=0.9, suggestions=[]
        )
        result = ReviewGenerator._consolidate_feedback([section])
        assert result == [section]

    def test_same_section_name_different_content_not_dropped(self) -> None:
        """Distinct content under a repeated section_name must not be lost.

        The old name-based dedup silently dropped the second section here; the
        content-based approach keeps both.
        """
        sections = [
            FeedbackSection(
                section_name="skills_feedback",
                content="Strong Python fundamentals.",
                confidence=0.9,
                suggestions=[],
            ),
            FeedbackSection(
                section_name="skills_feedback",
                content="Weak test coverage on the API layer.",
                confidence=0.9,
                suggestions=[],
            ),
        ]
        result = ReviewGenerator._consolidate_feedback(sections)
        assert len(result) == 2
