"""Deterministic mock review generator for offline evaluation.

Mirrors MockEmbeddingProvider: no real API calls, same input always
produces the same output. Used by scripts/run_evals.py so the eval
runner can execute without an API key or network access.
"""

import hashlib

import structlog

from rag.generator.output_parser import FeedbackSection

logger = structlog.get_logger()

SECTION_NAMES = [
    "skills_feedback",
    "projects_feedback",
    "presentation_feedback",
    "gaps_feedback",
    "first_impression",
]


class MockReviewGenerator:
    """Generate deterministic fake review sections without calling an LLM."""

    def generate_section(
        self, section_name: str, context_chunks: list[dict], profile_data: dict
    ) -> FeedbackSection:
        """Generate one deterministic feedback section.

        Args:
            section_name: Section name (skills_feedback, projects_feedback, etc.)
            context_chunks: Retrieved context chunks
            profile_data: Profile metadata

        Returns:
            FeedbackSection with deterministic fake content
        """
        github_username = profile_data.get("github_username", "unknown")
        chunk_count = len(context_chunks)

        # Deterministic confidence derived from a hash, same pattern as
        # MockEmbeddingProvider's deterministic seed.
        seed_text = f"{section_name}:{github_username}:{chunk_count}"
        digest = hashlib.sha256(seed_text.encode()).hexdigest()
        confidence = 0.5 + (int(digest[:4], 16) % 50) / 100

        content = (
            f"Mock {section_name.replace('_', ' ')} for {github_username}. "
            f"Based on {chunk_count} retrieved chunks."
        )

        return FeedbackSection(
            section_name=section_name,
            content=content,
            confidence=round(confidence, 2),
            suggestions=[f"Mock suggestion for {section_name}"],
        )

    def generate_full_review(
        self, profile_data: dict, retrieved_chunks: list[dict]
    ) -> list[FeedbackSection]:
        """Generate a complete deterministic review across all sections.

        Args:
            profile_data: Profile metadata and projects
            retrieved_chunks: Context chunks from retrieval

        Returns:
            List of FeedbackSections for all review areas
        """
        sections = [
            self.generate_section(name, retrieved_chunks, profile_data) for name in SECTION_NAMES
        ]
        logger.info("mock_full_review_generated", section_count=len(sections))
        return sections
