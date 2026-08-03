"""LLM-based review generation."""

from dataclasses import dataclass

import openai
import structlog

from .output_parser import FeedbackSection, parse_review_output
from .prompt_templates import get_template

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
        self.client = openai.OpenAI(api_key=config.api_key, base_url=config.base_url)

    def generate_section(
        self, section_name: str, context_chunks: list[dict], profile_data: dict
    ) -> FeedbackSection:
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
            context=context_text, github_username=github_username, project_count=project_count
        )

        # Call LLM
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": "You are an expert portfolio reviewer."},
                {"role": "user", "content": prompt},
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        content = response.choices[0].message.content

        # Parse output
        sections = parse_review_output(content)

        # Return first section or create default
        if sections:
            return sections[0]

        logger.warning("no_sections_parsed", section_name=section_name)
        return FeedbackSection(
            section_name=section_name, content=content, confidence=0.6, suggestions=[]
        )

    def generate_full_review(
        self, profile_data: dict, retrieved_chunks: list[dict]
    ) -> list[FeedbackSection]:
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
            "first_impression",
        ]

        all_sections = []

        for section_name in section_names:
            try:
                section = self.generate_section(section_name, retrieved_chunks, profile_data)

                # Add source citations if available
                section = self._add_citations(section, retrieved_chunks)

                all_sections.append(section)
                logger.info("section_generated", section=section_name)

            except Exception as e:
                logger.error("section_generation_failed", section=section_name, error=str(e))
                # Continue with remaining sections
                all_sections.append(
                    FeedbackSection(
                        section_name=section_name,
                        content=f"Error generating {section_name}",
                        confidence=0.0,
                        suggestions=[],
                    )
                )

        # Consolidate duplicates across similar projects
        all_sections = self._consolidate_feedback(all_sections)

        logger.info("full_review_generated", section_count=len(all_sections))
        return all_sections

    @staticmethod
    def _group_chunks_by_stack(chunks: list[dict]) -> list[list[dict]]:
        """Group chunks that share a tech stack so same-stack projects are
        presented to the LLM as one related group instead of independent
        blocks (see issue #28).

        Args:
            chunks: Context chunks, already truncated to the retrieval limit

        Returns:
            List of chunk groups, in first-seen order. Chunks with no
            language/stack metadata each form their own single-chunk group
            rather than being merged together.
        """
        groups: dict[str, list[dict]] = {}
        order: list[str] = []

        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            primary_language = metadata.get("primary_language")
            tech_stack = metadata.get("tech_stack")

            if primary_language:
                key = f"lang:{primary_language}"
            elif isinstance(tech_stack, list) and tech_stack:
                key = f"stack:{'+'.join(sorted(tech_stack))}"
            else:
                key = f"ungrouped:{id(chunk)}"

            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(chunk)

        return [groups[key] for key in order]

    @staticmethod
    def _stack_label(group: list[dict]) -> str:
        """Human-readable label for a chunk group's shared stack.

        Args:
            group: Chunks that were grouped together by
                ``_group_chunks_by_stack``

        Returns:
            The shared primary language, or the joined tech stack if no
            primary language is present
        """
        metadata = group[0].get("metadata", {})
        primary_language = metadata.get("primary_language")
        if primary_language:
            return str(primary_language)

        tech_stack = metadata.get("tech_stack")
        if isinstance(tech_stack, list) and tech_stack:
            return ", ".join(tech_stack)

        return "unknown"

    @staticmethod
    def _format_context(chunks: list[dict]) -> str:
        """Format retrieved chunks into context string.

        Chunks that share a tech stack are grouped into a single numbered
        block so the LLM sees them as related projects to consolidate
        feedback for, instead of independent projects to write one
        near-duplicate paragraph per (issue #28).

        Args:
            chunks: List of retrieved chunks

        Returns:
            Formatted context string
        """
        limited_chunks = chunks[:10]  # Limit to 10 chunks
        groups = ReviewGenerator._group_chunks_by_stack(limited_chunks)

        parts = []
        for i, group in enumerate(groups, 1):
            if len(group) == 1:
                chunk = group[0]
                source = chunk.get("metadata", {}).get("source_id", "unknown")
                score = chunk.get("score", 0)
                text = chunk.get("text", "")
                parts.append(f"[{i}] (relevance: {score:.2f}) Source: {source}\n{text}")
                continue

            stack_label = ReviewGenerator._stack_label(group)
            header = (
                f"[{i}] Shared stack: {stack_label} "
                f"-- {len(group)} related projects (consolidate into one observation)"
            )
            body = "\n".join(
                f"- Source: {chunk.get('metadata', {}).get('source_id', 'unknown')} "
                f"(relevance: {chunk.get('score', 0):.2f})\n  {chunk.get('text', '')}"
                for chunk in group
            )
            parts.append(f"{header}\n{body}")

        return "\n\n".join(parts)

    @staticmethod
    def _add_citations(section: FeedbackSection, retrieved_chunks: list[dict]) -> FeedbackSection:
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
