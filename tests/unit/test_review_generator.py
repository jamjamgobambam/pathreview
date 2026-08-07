"""Tests for review_generator.py"""

import pytest

from rag.generator.output_parser import FeedbackSection
from rag.generator.prompt_templates import get_template
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

        # Grouping must not lose the individual project sources/text --
        # consolidation means "present together", not "discard detail".
        assert "repo_1_todo-api" in context
        assert "repo_2_cli-tool" in context
        assert "repo_3_data-pipeline" in context

    def test_single_project_output_is_unchanged(self) -> None:
        """A single chunk has nothing to group with -- output must match
        today's plain per-chunk format exactly (no regressions for the
        common single-project case)."""
        chunks = [
            _repo_chunk("repo_1_todo-api", ["Python", "Flask"], "Flask REST API.", score=0.87),
        ]

        context = ReviewGenerator._format_context(chunks)

        assert context == "[1] (relevance: 0.87) Source: repo_1_todo-api\nFlask REST API."

    def test_mixed_stack_chunks_are_not_merged(self) -> None:
        """Projects in genuinely different stacks must stay in separate
        blocks -- grouping must not erase meaningful differences."""
        chunks = [
            _repo_chunk("repo_1_todo-api", ["Python", "Flask"], "Flask REST API."),
            _repo_chunk("repo_2_dashboard", ["JavaScript", "React"], "React dashboard app."),
        ]

        context = ReviewGenerator._format_context(chunks)

        assert context.count("[1]") == 1
        assert context.count("[2]") == 1
        assert "repo_1_todo-api" in context
        assert "repo_2_dashboard" in context

    def test_chunks_missing_stack_metadata_degrade_gracefully(self) -> None:
        """Chunks without primary_language/tech_stack (e.g. resume or README
        chunks) must not crash and must not be merged with unrelated chunks."""
        readme_chunk = {
            "metadata": {"source_id": "readme_chunk"},
            "score": 0.5,
            "text": "Personal portfolio site built with love.",
        }
        python_chunk = _repo_chunk("repo_1_todo-api", ["Python"], "Flask REST API.")

        context = ReviewGenerator._format_context([readme_chunk, python_chunk])

        assert "readme_chunk" in context
        assert "repo_1_todo-api" in context
        assert context.count("[1]") == 1
        assert context.count("[2]") == 1

    def test_grouping_respects_existing_top_10_chunk_limit(self) -> None:
        """Grouping happens within the existing top-10 truncation, not
        before it -- an 11th same-stack chunk must not appear at all."""
        chunks = [
            _repo_chunk(f"repo_{i}", ["Python"], f"Project {i} description.") for i in range(11)
        ]

        context = ReviewGenerator._format_context(chunks)

        assert "repo_10" not in context
        for i in range(10):
            assert f"repo_{i}" in context


@pytest.mark.unit
class TestPromptTemplateConsolidationInstruction:
    """The grouping fix in _format_context only works because the prompt
    templates tell the model what a "Shared stack" block means. These
    tests pin that wording so an edit to prompt_templates.py can't silently
    break the contract _format_context depends on."""

    @pytest.mark.parametrize("template_name", ["skills_feedback", "projects_feedback"])
    def test_template_instructs_model_to_consolidate_shared_stack_blocks(
        self, template_name: str
    ) -> None:
        template = get_template(template_name)

        assert "Shared stack" in template
        assert "consolidat" in template.lower() or "don't repeat" in template.lower()


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
