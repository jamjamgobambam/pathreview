"""Tests for mock_generator.py"""

import sys

import pytest

from rag.evaluator.faithfulness_checker import FaithfulnessChecker
from rag.generator.mock_generator import SECTION_NAMES, MockReviewGenerator
from rag.generator.output_parser import FeedbackSection


@pytest.mark.unit
class TestMockReviewGenerator:
    """Test suite for MockReviewGenerator."""

    @pytest.fixture
    def generator(self):
        """Create a MockReviewGenerator instance."""
        return MockReviewGenerator()

    @pytest.fixture
    def chunks(self):
        """Return retrieved chunks resembling hybrid retriever output."""
        return [
            {
                "id": "resume_bench_chunk_0",
                "text": (
                    "Built REST APIs using Python and FastAPI backed by PostgreSQL "
                    "with Docker based deployments"
                ),
                "metadata": {"source_id": "resume_bench"},
                "score": 0.91,
            },
            {
                "id": "readme_bench_chunk_1",
                "text": (
                    "Weather forecasting application built with React TypeScript "
                    "Tailwind and OpenWeatherMap"
                ),
                "metadata": {"source_id": "readme_bench"},
                "score": 0.54,
            },
        ]

    @pytest.fixture
    def profile_data(self):
        """Return profile metadata for generation."""
        return {
            "github_username": "janedoe",
            "projects": [{"name": "weather-app", "language": "TypeScript"}],
        }

    def test_generate_section_returns_feedback_section(self, generator, chunks, profile_data):
        """Test generate_section returns a populated FeedbackSection."""
        section = generator.generate_section("skills_feedback", chunks, profile_data)

        assert isinstance(section, FeedbackSection)
        assert section.section_name == "skills_feedback"
        assert section.content
        assert 0.0 <= section.confidence <= 1.0
        assert isinstance(section.suggestions, list)

    def test_generate_full_review_covers_all_sections(self, generator, chunks, profile_data):
        """Test generate_full_review returns one section per review area."""
        sections = generator.generate_full_review(profile_data, chunks)

        assert [s.section_name for s in sections] == SECTION_NAMES

    def test_generation_is_deterministic(self, generator, chunks, profile_data):
        """Test identical inputs produce identical feedback."""
        first = generator.generate_full_review(profile_data, chunks)
        second = MockReviewGenerator().generate_full_review(profile_data, chunks)

        assert [s.content for s in first] == [s.content for s in second]
        assert [s.confidence for s in first] == [s.confidence for s in second]
        assert [s.suggestions for s in first] == [s.suggestions for s in second]

    def test_generation_is_stable_across_retrieval_tie_order(self, generator, chunks, profile_data):
        """Test chunk ordering does not change output when scores are unchanged."""
        forward = generator.generate_full_review(profile_data, chunks)
        reversed_order = generator.generate_full_review(profile_data, list(reversed(chunks)))

        assert [s.content for s in forward] == [s.content for s in reversed_order]

    def test_content_is_grounded_in_supplied_chunks(self, generator, chunks, profile_data):
        """Test generated feedback quotes terms taken from the retrieved chunks."""
        section = generator.generate_section("skills_feedback", chunks, profile_data)

        chunk_tokens = set()
        for chunk in chunks:
            chunk_tokens.update(chunk["text"].lower().split())

        quoted = chunk_tokens & set(section.content.lower().split())
        assert len(quoted) >= 2

    def test_feedback_scores_above_zero_faithfulness(self, generator, chunks, profile_data):
        """Test generated feedback is measurably supported by its own context."""
        sections = generator.generate_full_review(profile_data, chunks)
        feedback = "\n\n".join(s.content for s in sections)

        score = FaithfulnessChecker().check(feedback, chunks)

        assert score > 0.0

    def test_faithfulness_varies_with_evidence_quality(self, generator, profile_data):
        """Test faithfulness is not a constant across portfolios of differing richness."""
        rich = [
            {
                "id": "rich_chunk_0",
                "text": (
                    "Python FastAPI PostgreSQL Docker Redis Alembic pytest "
                    "asyncio SQLAlchemy migrations observability"
                ),
                "metadata": {},
                "score": 0.9,
            }
        ]
        thin = [{"id": "thin_chunk_0", "text": "Todo app.", "metadata": {}, "score": 0.9}]

        checker = FaithfulnessChecker()
        rich_feedback = "\n\n".join(
            s.content for s in generator.generate_full_review(profile_data, rich)
        )
        thin_feedback = "\n\n".join(
            s.content for s in generator.generate_full_review(profile_data, thin)
        )

        assert checker.check(rich_feedback, rich) > checker.check(thin_feedback, thin)

    def test_thin_chunks_lower_faithfulness_than_dense_chunks(self, generator, profile_data):
        """Test per-chunk grounding keeps faithfulness from saturating on any corpus."""
        dense = [
            {
                "id": f"dense_chunk_{i}",
                "text": f"python fastapi postgresql docker redis {i}00",
                "score": 0.9 - i / 10,
            }
            for i in range(4)
        ]
        thin = [
            {"id": f"thin_chunk_{i}", "text": f"Notes. Todo{i}.", "score": 0.9 - i / 10}
            for i in range(4)
        ]

        checker = FaithfulnessChecker()
        dense_feedback = "\n\n".join(
            s.content for s in generator.generate_full_review(profile_data, dense)
        )
        thin_feedback = "\n\n".join(
            s.content for s in generator.generate_full_review(profile_data, thin)
        )

        assert checker.check(dense_feedback, dense) > checker.check(thin_feedback, thin)

    def test_sections_cite_different_chunks(self, generator, profile_data):
        """Test sections start at different offsets into the ranked chunk list."""
        chunks = [
            {
                "id": f"c_chunk_{i}",
                "text": f"alpha{i} beta{i} gamma{i} delta{i}",
                "score": 0.9 - i / 10,
            }
            for i in range(5)
        ]

        sections = generator.generate_full_review(profile_data, chunks)

        assert "alpha0" in sections[0].content
        assert "alpha1" in sections[1].content

    def test_feedback_is_not_verbatim_copy_of_context(self, generator, chunks, profile_data):
        """Test feedback recombines evidence rather than echoing chunk text."""
        section = generator.generate_section("skills_feedback", chunks, profile_data)

        for chunk in chunks:
            assert chunk["text"] not in section.content

    def test_sections_differ_from_each_other(self, generator, chunks, profile_data):
        """Test each section quotes a different slice of the evidence."""
        sections = generator.generate_full_review(profile_data, chunks)
        contents = [s.content for s in sections]

        assert len(set(contents)) == len(contents)

    def test_empty_chunks_returns_no_evidence_section(self, generator, profile_data):
        """Test empty retrieval yields an explicit no-evidence section, not a crash."""
        sections = generator.generate_full_review(profile_data, [])

        assert len(sections) == len(SECTION_NAMES)
        for section in sections:
            assert section.confidence == 0.0
            assert section.suggestions == []
            assert "no evidence" in section.content.lower()

    def test_chunks_without_text_key_handled(self, generator, profile_data):
        """Test chunks missing the 'text' key degrade to the no-evidence path."""
        sections = generator.generate_full_review(profile_data, [{"id": "x", "score": 0.5}])

        assert all(s.confidence == 0.0 for s in sections)

    def test_chunks_without_score_key_handled(self, generator, profile_data):
        """Test chunks missing the 'score' key still produce grounded feedback."""
        chunks = [{"id": "a_chunk_0", "text": "Python FastAPI PostgreSQL Docker"}]

        sections = generator.generate_full_review(profile_data, chunks)

        assert all(s.content for s in sections)

    def test_missing_github_username_handled(self, generator, chunks):
        """Test profile data without a username still generates feedback."""
        section = generator.generate_section("skills_feedback", chunks, {})

        assert section.content
        assert "this candidate" in section.content

    def test_unknown_section_name_supported(self, generator, chunks, profile_data):
        """Test an unrecognised section name still returns grounded feedback."""
        section = generator.generate_section("custom_feedback", chunks, profile_data)

        assert section.section_name == "custom_feedback"
        assert section.content

    def test_sentences_are_long_enough_to_be_scored(self, generator, chunks, profile_data):
        """Test every sentence exceeds the 10-character floor FaithfulnessChecker applies."""
        section = generator.generate_section("skills_feedback", chunks, profile_data)

        claims = FaithfulnessChecker._extract_claims(section.content)

        assert claims
        assert all(len(claim) > 10 for claim in claims)

    def test_confidence_tracks_available_evidence(self, generator, profile_data):
        """Test confidence is higher when more evidence is retrieved."""
        rich = [
            {
                "id": "rich_chunk_0",
                "text": "Python FastAPI PostgreSQL Docker Redis Alembic pytest asyncio",
                "score": 0.9,
            }
        ]
        thin = [{"id": "thin_chunk_0", "text": "Python", "score": 0.9}]

        rich_section = generator.generate_section("skills_feedback", rich, profile_data)
        thin_section = generator.generate_section("skills_feedback", thin, profile_data)

        assert rich_section.confidence > thin_section.confidence

    def test_module_imports_no_http_client(self):
        """Test the mock generator module pulls in no networking library."""
        module = sys.modules["rag.generator.mock_generator"]

        assert not hasattr(module, "openai")
        assert not hasattr(module, "httpx")

    def test_suggestions_are_deterministic_and_grounded(self, generator, chunks, profile_data):
        """Test suggestions repeat across runs and reference retrieved evidence."""
        first = generator.generate_section("projects_feedback", chunks, profile_data)
        second = generator.generate_section("projects_feedback", chunks, profile_data)

        assert first.suggestions == second.suggestions
        assert all(s for s in first.suggestions)
