"""Reproduction test for issue #28.

Issue: Generator produces duplicate feedback sections when a user has multiple
projects in the same tech stack.
https://github.com/ascherj/pathreview/issues/28

When a user has several projects built with the same stack (e.g. three Python
projects), the review generator emits a near-identical "Python skills"
observation for each one. ``ReviewGenerator._consolidate_feedback`` is supposed
to merge these, but it only deduplicates by ``section_name`` and never inspects
the feedback content -- so distinct per-project section names carrying identical
content all survive, and the review reads as repetitive.

Reproduction steps (also runnable standalone):
    1. Build an LLM JSON payload with one key per project, each carrying the
       same "Python skills" content.
    2. Parse it with ``parse_review_output`` -> N sections, identical content.
    3. Run ``ReviewGenerator._consolidate_feedback`` -> expected 1 section,
       actual N sections (bug).

This test asserts the *expected* (fixed) behavior and is marked ``xfail`` so it
documents the bug today (reported as XFAIL) and will flip to XPASS once the fix
lands, at which point ``strict=True`` fails the run to remind us to drop the
marker.
"""

import json

import pytest

from rag.generator.output_parser import parse_review_output
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
    """Reproduces the duplicate cross-project feedback described in issue #28."""

    def test_parsing_yields_one_section_per_project(self) -> None:
        """Baseline: the parser produces one section per project (not the bug itself)."""
        sections = parse_review_output(_three_same_stack_projects())
        assert len(sections) == 3
        # All three carry the same underlying observation.
        assert all(PY_SKILLS in s.content for s in sections)

    @pytest.mark.xfail(
        strict=True,
        reason="Issue #28: _consolidate_feedback dedupes by section_name only, "
        "so identical cross-project content is not merged. Remove this marker "
        "when the fix lands.",
    )
    def test_consolidation_merges_duplicate_cross_project_feedback(self) -> None:
        """Expected: identical feedback across same-stack projects collapses to one section."""
        sections = parse_review_output(_three_same_stack_projects())

        consolidated = ReviewGenerator._consolidate_feedback(sections)

        duplicates = [s for s in consolidated if PY_SKILLS in s.content]
        # Expected: the three duplicate observations are consolidated into one.
        # Actual (bug): all three survive because dedup is by section_name only.
        assert len(duplicates) == 1, (
            f"Expected duplicate Python-skills feedback to be consolidated to 1 "
            f"section, but found {len(duplicates)} repeating the same content."
        )
