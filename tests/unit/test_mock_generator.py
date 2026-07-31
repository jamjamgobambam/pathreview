"""Tests for mock_generator.py"""

import pytest

from rag.generator.mock_generator import SECTION_NAMES, MockReviewGenerator


@pytest.mark.unit
class TestMockReviewGenerator:
    """Test suite for MockReviewGenerator."""

    @pytest.fixture
    def generator(self) -> MockReviewGenerator:
        """Create a MockReviewGenerator instance."""
        return MockReviewGenerator()

    def test_generate_section_returns_feedback_section(
        self, generator: MockReviewGenerator
    ) -> None:
        """Test generate_section returns a FeedbackSection with expected fields."""
        section = generator.generate_section(
            "skills_feedback", [], {"github_username": "testuser"}
        )

        assert section.section_name == "skills_feedback"
        assert "testuser" in section.content
        assert 0.0 <= section.confidence <= 1.0
        assert isinstance(section.suggestions, list)
        assert len(section.suggestions) > 0

    def test_generate_section_is_deterministic(
        self, generator: MockReviewGenerator
    ) -> None:
        """Test the same input always produces the same output."""
        profile_data = {"github_username": "sameuser"}
        chunks: list[dict] = [{"text": "some chunk"}]

        section1 = generator.generate_section("skills_feedback", chunks, profile_data)
        section2 = generator.generate_section("skills_feedback", chunks, profile_data)

        assert section1.content == section2.content
        assert section1.confidence == section2.confidence

    def test_generate_section_varies_with_chunk_count(
        self, generator: MockReviewGenerator
    ) -> None:
        """Test confidence and content reflect the number of chunks passed in."""
        profile_data = {"github_username": "testuser"}

        section_no_chunks = generator.generate_section("skills_feedback", [], profile_data)
        section_with_chunks = generator.generate_section(
            "skills_feedback", [{"text": "a"}, {"text": "b"}], profile_data
        )

        assert section_no_chunks.content != section_with_chunks.content

    def test_generate_full_review_returns_all_sections(
        self, generator: MockReviewGenerator
    ) -> None:
        """Test generate_full_review returns one section per known section name."""
        sections = generator.generate_full_review({"github_username": "testuser"}, [])

        assert len(sections) == len(SECTION_NAMES)
        returned_names = {s.section_name for s in sections}
        assert returned_names == set(SECTION_NAMES)

    def test_generate_full_review_handles_missing_username(
        self, generator: MockReviewGenerator
    ) -> None:
        """Test generate_full_review does not crash when github_username is missing."""
        sections = generator.generate_full_review({}, [])

        assert len(sections) == len(SECTION_NAMES)
        for section in sections:
            assert "unknown" in section.content

    def test_no_network_or_api_calls(self, generator: MockReviewGenerator) -> None:
        """Test the generator works with no API key or network access configured.

        This is the core requirement for offline evaluation: MockReviewGenerator
        must never attempt a real API call.
        """
        sections = generator.generate_full_review(
            {"github_username": "offline-user"}, [{"text": "chunk text"}]
        )

        assert len(sections) == len(SECTION_NAMES)
