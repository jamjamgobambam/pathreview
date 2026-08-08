"""Tests for review_generator.py

Covers the fix for issue #28: the generator produced duplicate feedback
when a user has multiple projects in the same tech stack. The tests in
TestConsolidateFeedback started life as the xfail reproduction for the bug
and now assert the fixed behavior: a shared observation is stated once and
attributed to every project it applies to.
"""

import json
from unittest.mock import Mock

import pytest

from rag.generator.output_parser import FeedbackSection
from rag.generator.review_generator import ReviewConfig, ReviewGenerator


def _mock_completion(content: str) -> Mock:
    """Build a mock chat completion response with the given content."""
    choice = Mock()
    choice.message.content = content
    completion = Mock()
    completion.choices = [choice]
    return completion


def _make_generator(responses: list[str]) -> ReviewGenerator:
    """Create a ReviewGenerator whose LLM client returns canned responses."""
    config = ReviewConfig(
        api_key="test-key",
        base_url="http://localhost:9999/v1",
        model="test-model",
    )
    generator = ReviewGenerator(config)
    generator.client = Mock()
    generator.client.chat.completions.create.side_effect = [_mock_completion(r) for r in responses]
    return generator


def _skills_section(key_skills: list) -> FeedbackSection:
    """Build a skills_feedback section holding the given key_skills."""
    return FeedbackSection(
        section_name="skills_feedback",
        content=json.dumps({"key_skills": key_skills}),
        confidence=0.9,
        suggestions=[],
    )


@pytest.mark.unit
class TestConsolidateFeedback:
    """Consolidation of duplicate cross-project observations (issue #28)."""

    def test_consolidate_merges_same_observation_across_projects(self) -> None:
        """A skill observation repeated for three same-stack projects is
        consolidated into a single entry attributed to all three."""
        observation = "Built a RAG pipeline with embeddings and vector search"
        sections = [
            _skills_section(
                [
                    {
                        "skill": "Python / RAG",
                        "evidence": f"{observation} in rag-chatbot-alpha",
                        "project": "rag-chatbot-alpha",
                    },
                    {
                        "skill": "Python / RAG",
                        "evidence": f"{observation} in rag-chatbot-beta",
                        "project": "rag-chatbot-beta",
                    },
                    {
                        "skill": "Python / RAG",
                        "evidence": f"{observation} in rag-chatbot-gamma",
                        "project": "rag-chatbot-gamma",
                    },
                ]
            )
        ]

        result = ReviewGenerator._consolidate_feedback(sections)

        # The shared skill should be stated once, not once per project.
        combined = " ".join(s.content for s in result)
        assert combined.count("Python / RAG") == 1

        # ...and attributed to every project that demonstrated it.
        merged = json.loads(result[0].content)["key_skills"]
        assert len(merged) == 1
        assert merged[0]["projects"] == [
            "rag-chatbot-alpha",
            "rag-chatbot-beta",
            "rag-chatbot-gamma",
        ]

    def test_full_review_does_not_repeat_feedback_per_same_stack_project(self) -> None:
        """generate_full_review consolidates near-identical entries even when
        the model ignores the prompt and emits one entry per project."""
        repeated_phrase = "solid Python and vector-database skills"
        skills_response = json.dumps(
            {
                "key_skills": [
                    {
                        "skill": "Python / vector databases",
                        "evidence": f"Demonstrates {repeated_phrase} in {repo}.",
                        "projects": [repo],
                    }
                    for repo in [
                        "rag-chatbot-alpha",
                        "rag-chatbot-beta",
                        "rag-chatbot-gamma",
                    ]
                ],
                "language_proficiency": {"Python": "advanced"},
            }
        )
        other_response = json.dumps(
            {"feedback": {"observations": ["Looks fine."], "suggestions": []}}
        )
        # generate_full_review generates 5 sections; skills_feedback is first.
        generator = _make_generator([skills_response] + [other_response] * 4)

        profile_data = {
            "github_username": "janedoe",
            "projects": [
                {"github_repo": "rag-chatbot-alpha"},
                {"github_repo": "rag-chatbot-beta"},
                {"github_repo": "rag-chatbot-gamma"},
            ],
        }
        chunks = [
            {
                "text": f"README for {repo}: a Python RAG chatbot using embeddings.",
                "score": 0.9,
                "metadata": {"source_id": repo, "chunk_index": 0, "section": "readme"},
            }
            for repo in ["rag-chatbot-alpha", "rag-chatbot-beta", "rag-chatbot-gamma"]
        ]

        sections = generator.generate_full_review(profile_data, chunks)

        # The shared observation survives as ONE consolidated statement
        # attributed to all three projects — not repeated three times.
        combined = " ".join(s.content for s in sections)
        assert combined.count(repeated_phrase) == 1
        payload = json.loads(sections[0].content.split("\nSources:")[0])
        assert [e["projects"] for e in payload["key_skills"]] == [
            ["rag-chatbot-alpha", "rag-chatbot-beta", "rag-chatbot-gamma"]
        ]

    def test_case_and_whitespace_variants_of_a_skill_merge(self) -> None:
        """'python' and ' Python ' are the same skill; 'Django' is not."""
        sections = [
            _skills_section(
                [
                    {"skill": "python", "evidence": "a", "projects": ["p1"]},
                    {"skill": " Python ", "evidence": "b", "projects": ["p2"]},
                    {"skill": "Django", "evidence": "c", "projects": ["p1"]},
                ]
            )
        ]

        result = ReviewGenerator._consolidate_feedback(sections)

        merged = json.loads(result[0].content)["key_skills"]
        assert len(merged) == 2
        assert merged[0]["skill"] == "python"  # first-seen form is kept
        assert merged[0]["projects"] == ["p1", "p2"]
        assert merged[1]["skill"] == "Django"

    def test_different_observations_for_same_stack_are_not_merged(self) -> None:
        """Three same-stack projects with genuinely different observations
        keep all three entries — merging keys on the skill, not the stack."""
        sections = [
            _skills_section(
                [
                    {"skill": "API design", "evidence": "a", "projects": ["p1"]},
                    {"skill": "Testing", "evidence": "b", "projects": ["p2"]},
                    {"skill": "Deployment", "evidence": "c", "projects": ["p3"]},
                ]
            )
        ]

        result = ReviewGenerator._consolidate_feedback(sections)

        merged = json.loads(result[0].content)["key_skills"]
        assert len(merged) == 3

    def test_single_project_entry_without_project_info_is_untouched(self) -> None:
        """A lone entry with no project attribution gains no 'projects' noise
        — single-project reviews round-trip unchanged."""
        section = _skills_section([{"skill": "Python", "evidence": "Built one solid project"}])

        result = ReviewGenerator._consolidate_feedback([section])

        assert result[0] == section

    def test_non_json_content_passes_through_unchanged(self) -> None:
        """Sections whose content is not JSON (the plaintext fallback path)
        pass through consolidation untouched."""
        sections = [
            FeedbackSection("skills_feedback", "plain text feedback", 0.7, []),
            FeedbackSection("projects_feedback", "plain text feedback", 0.7, []),
        ]

        result = ReviewGenerator._consolidate_feedback(sections)

        assert result == sections

    def test_entries_without_skill_name_are_preserved(self) -> None:
        """Malformed entries (no skill name, or not a dict) are kept as-is
        rather than dropped or crashed on."""
        sections = [
            _skills_section(
                [
                    {"skill": "Python", "evidence": "a", "projects": ["p1"]},
                    {"skill": "Python", "evidence": "b", "projects": ["p2"]},
                    {"evidence": "no skill name"},
                    "just a string",
                ]
            )
        ]

        result = ReviewGenerator._consolidate_feedback(sections)

        merged = json.loads(result[0].content)["key_skills"]
        assert len(merged) == 3
        assert {"evidence": "no skill name"} in merged
        assert "just a string" in merged


@pytest.mark.unit
class TestProjectAwareContext:
    """Project grouping in _format_context and _project_inventory."""

    def _chunk(self, source_id: str | None, text: str = "chunk text", score: float = 0.5) -> dict:
        metadata = {"chunk_index": 0, "section": "readme"}
        if source_id is not None:
            metadata["source_id"] = source_id
        return {"text": text, "score": score, "metadata": metadata}

    def test_format_context_groups_chunks_by_project(self) -> None:
        """Interleaved chunks from two projects are grouped under one header
        per project."""
        chunks = [
            self._chunk("proj-a", "a1"),
            self._chunk("proj-b", "b1"),
            self._chunk("proj-a", "a2"),
        ]

        context = ReviewGenerator._format_context(chunks)

        assert context.count("=== Project: proj-a ===") == 1
        assert context.count("=== Project: proj-b ===") == 1
        # proj-a's chunks appear together, before proj-b's header
        assert context.index("a1") < context.index("a2") < context.index("b1")

    def test_format_context_limits_to_ten_chunks(self) -> None:
        """The 10-chunk context limit is preserved."""
        chunks = [self._chunk("proj-a", f"text-{i}") for i in range(15)]

        context = ReviewGenerator._format_context(chunks)

        assert "text-9" in context
        assert "text-10" not in context

    def test_project_inventory_lists_distinct_projects_in_order(self) -> None:
        chunks = [
            self._chunk("proj-a"),
            self._chunk("proj-b"),
            self._chunk("proj-a"),
        ]

        assert ReviewGenerator._project_inventory(chunks) == ["proj-a", "proj-b"]

    def test_project_inventory_skips_chunks_without_source_id(self) -> None:
        """Chunks missing source_id don't become a phantom 'unknown' project."""
        chunks = [self._chunk("proj-a"), self._chunk(None)]

        assert ReviewGenerator._project_inventory(chunks) == ["proj-a"]

    def test_generate_section_passes_project_inventory_to_prompt(self) -> None:
        """The skills prompt receives the project inventory and grouped
        context."""
        generator = _make_generator([json.dumps({"key_skills": []})])
        chunks = [self._chunk("proj-a"), self._chunk("proj-b")]

        generator.generate_section("skills_feedback", chunks, {"projects": []})

        prompt = generator.client.chat.completions.create.call_args.kwargs["messages"][1]["content"]
        assert "- proj-a" in prompt
        assert "- proj-b" in prompt
        assert "=== Project: proj-a ===" in prompt

    def test_citations_are_added_after_consolidation(self) -> None:
        """Sections still get source citations, appended after consolidation
        so consolidation sees parseable JSON."""
        skills_response = json.dumps(
            {
                "key_skills": [
                    {"skill": "Python", "evidence": "a", "projects": ["proj-a"]},
                    {"skill": "Python", "evidence": "b", "projects": ["proj-b"]},
                ]
            }
        )
        generator = _make_generator([skills_response] * 5)
        chunks = [self._chunk("proj-a"), self._chunk("proj-b")]

        sections = generator.generate_full_review({"projects": []}, chunks)

        skills = sections[0]
        assert "Sources: proj-a, proj-b" in skills.content
        # Consolidation worked despite the citation suffix
        payload = json.loads(skills.content.split("\nSources:")[0])
        assert len(payload["key_skills"]) == 1
