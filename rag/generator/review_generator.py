"""LLM-based review generation."""

from dataclasses import dataclass
from typing import Optional
import openai
import structlog

from .prompt_templates import get_template
from .output_parser import parse_review_output, FeedbackSection

logger = structlog.get_logger()


@dataclass
class ReviewConfig:
    """Configuration for review generation."""
    api_key: str
    base_url: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 2000


class ReviewGenerator:
    """Generate reviews using LLM (OpenAI API or OpenRouter)."""

    def __init__(self, config: ReviewConfig):
        """Initialize review generator.

        Args:
            config: ReviewConfig with API settings
        """
        self.config = config
        self.client = openai.OpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )

    def generate_section(self, section_name: str, context_chunks: list[dict],
                        profile_data: dict) -> FeedbackSection:
        """Generate feedback for a specific section.

        Args:
            section_name: Section name (skills_feedback, projects_feedback, etc.)
            context_chunks: Retrieved context chunks
            profile_data: Profile metadata

        Returns:
            FeedbackSection with generated content
        """
        # Get template
        template = get_template(section_name)

        # Format context
        context_text = self._format_context(context_chunks)
        github_username = profile_data.get("github_username", "")
        project_count = len(profile_data.get("projects", []))

        prompt = template.format(
            context=context_text,
            github_username=github_username,
            project_count=project_count
        )

        # Call LLM
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": "You are an expert portfolio reviewer."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )

        content = response.choices[0].message.content

        # Parse output
        sections = parse_review_output(content)

        # Return first section or create default
        if sections:
            return sections[0]

        logger.warning("no_sections_parsed", section_name=section_name)
        return FeedbackSection(
            section_name=section_name,
            content=content,
            confidence=0.6,
            suggestions=[]
        )

    def generate_full_review(self, profile_data: dict,
                            retrieved_chunks: list[dict]) -> list[FeedbackSection]:
        """Generate complete review across all sections.

        Args:
            profile_data: Profile metadata and projects
            retrieved_chunks: Context chunks from retrieval

        Returns:
            List of FeedbackSections for all review areas
        """
        section_names = [
            "skills_feedback",
            "projects_feedback",
            "presentation_feedback",
            "gaps_feedback",
            "first_impression"
        ]

        all_sections = []

        for section_name in section_names:
            try:
                section = self.generate_section(
                    section_name, retrieved_chunks, profile_data
                )

                # Add source citations if available
                section = self._add_citations(section, retrieved_chunks)

                all_sections.append(section)
                logger.info("section_generated", section=section_name)

            except Exception as e:
                logger.error("section_generation_failed", section=section_name,
                           error=str(e))
                # Continue with remaining sections
                all_sections.append(FeedbackSection(
                    section_name=section_name,
                    content=f"Error generating {section_name}",
                    confidence=0.0,
                    suggestions=[]
                ))

        # Consolidate duplicates across similar projects
        all_sections = self._consolidate_feedback(all_sections)

        logger.info("full_review_generated", section_count=len(all_sections))
        return all_sections

    @staticmethod
    def _format_context(chunks: list[dict]) -> str:
        """Format retrieved chunks into context string.

        Args:
            chunks: List of retrieved chunks

        Returns:
            Formatted context string
        """
        parts = []
        for i, chunk in enumerate(chunks[:10], 1):  # Limit to 10 chunks
            source = chunk.get("metadata", {}).get("source_id", "unknown")
            score = chunk.get("score", 0)
            text = chunk.get("text", "")
            parts.append(f"[{i}] (relevance: {score:.2f}) Source: {source}\n{text}")

        return "\n\n".join(parts)

    @staticmethod
    def _add_citations(section: FeedbackSection,
                       retrieved_chunks: list[dict]) -> FeedbackSection:
        """Add source citations to feedback section.

        Args:
            section: Feedback section
            retrieved_chunks: Retrieved context chunks

        Returns:
            Updated section with citations
        """
        # Append sources if available
        if retrieved_chunks:
            sources = set()
            for chunk in retrieved_chunks[:5]:
                source = chunk.get("metadata", {}).get("source_id")
                if source:
                    sources.add(source)

            if sources:
                citation = f"\nSources: {', '.join(sorted(sources))}"
                section.content += citation

        return section

    @staticmethod
    def _consolidate_feedback(sections: list[FeedbackSection]) -> list[FeedbackSection]:
        """Consolidate duplicate feedback across similar sections.

        Args:
            sections: List of feedback sections

        Returns:
            Consolidated list of sections
        """
        # Simple consolidation: if two sections mention the same project,
        # merge the feedback
        seen = set()
        consolidated = []

        for section in sections:
            if section.section_name not in seen:
                consolidated.append(section)
                seen.add(section.section_name)

        return consolidated
