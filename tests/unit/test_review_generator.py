"""Tests for review_generator.py"""

import pytest

from rag.generator.output_parser import FeedbackSection
from rag.generator.review_generator import ReviewGenerator


def _repo_chunk(source_id: str, tech_stack: list[str], text: str, score: float = 0.9) -> dict:
    """Build a context chunk shaped like ingestion/pipeline.py's repo chunk output."""
    return {
        "metadata": {
            "source_id": source_id,
            "primary_language": tech_stack[0],
            "tech_stack": tech_stack,
        },
        "score": score,
        "text": text,
    }


@pytest.mark.unit
class TestFormatContext:
    """Reproduction tests for issue #28: duplicate feedback across same-stack projects."""

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Issue #28: _format_context concatenates chunks without grouping "
            "by tech_stack, so same-stack projects are presented to the LLM "
            "as fully independent blocks and it writes a near-duplicate "
            "'Python skills' paragraph per project instead of one "
            "consolidated observation."
        ),
    )
    def test_same_stack_chunks_are_grouped_not_repeated(self) -> None:
        chunks = [
            _repo_chunk(
                "repo_1_todo-api",
                ["Python", "Flask"],
                "Flask REST API with SQLAlchemy models and pytest coverage.",
            ),
            _repo_chunk(
                "repo_2_cli-tool",
                ["Python"],
                "Command-line tool using argparse and rich for output formatting.",
            ),
            _repo_chunk(
                "repo_3_data-pipeline",
                ["Python", "Pandas"],
                "ETL pipeline using pandas and SQLAlchemy for data warehousing.",
            ),
        ]

        context = ReviewGenerator._format_context(chunks)

        # Three independent projects share the "Python" stack. A grouped
        # context would surface that shared stack once, framing the three
        # chunks as related observations for the LLM to consolidate --
        # not as three standalone numbered blocks with no shared framing,
        # which is what currently prompts the LLM to write three
        # near-identical "Python skills" paragraphs.
        assert context.count("[1]") + context.count("[2]") + context.count("[3]") <= 1, (
            "Expected same-stack chunks to be collapsed into a single "
            "grouped block; _format_context still emits one independent "
            "numbered block per chunk (see issue #28)."
        )


@pytest.mark.unit
class TestConsolidateFeedback:
    """Confirms _consolidate_feedback is not a safety net for issue #28."""

    def test_noop_when_duplicate_content_has_unique_section_names(self) -> None:
        # generate_full_review always calls generate_section with the same
        # 5 fixed section_names, so section_name is already unique across
        # the list before _consolidate_feedback ever runs. Duplicate content
        # *within* a section (the actual bug) is invisible to this method,
        # which only dedupes on section_name.
        sections = [
            FeedbackSection(
                section_name="skills_feedback",
                content=(
                    "Strong Python skills demonstrated in todo-api. "
                    "Strong Python skills demonstrated in cli-tool. "
                    "Strong Python skills demonstrated in data-pipeline."
                ),
                confidence=0.9,
                suggestions=[],
            ),
            FeedbackSection(
                section_name="projects_feedback",
                content="Three well-organized Python projects.",
                confidence=0.9,
                suggestions=[],
            ),
        ]

        result = ReviewGenerator._consolidate_feedback(sections)

        assert result == sections
