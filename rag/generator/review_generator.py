"""LLM-based review generation."""

import difflib
import json
from dataclasses import dataclass

import openai
import structlog

from .output_parser import FeedbackSection, parse_review_output
from .prompt_templates import get_template

logger = structlog.get_logger()

# Two sections whose normalized content is at least this similar are treated as
# the same observation and consolidated. Deliberately conservative so genuinely
# distinct feedback is never merged.
CONSOLIDATION_SIMILARITY_THRESHOLD = 0.9


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
        """Consolidate duplicate feedback across same-stack projects.

        When a user has multiple projects in the same tech stack, the generator
        emits a near-identical observation for each one (e.g. the same "Python
        skills" feedback three times). Those sections have distinct
        ``section_name`` values but equivalent content, so deduplicating by name
        alone leaves every copy in place. This groups sections by content
        similarity and merges each group into a single cross-project comment,
        preserving genuinely distinct feedback and its original order.

        Args:
            sections: List of feedback sections

        Returns:
            Consolidated list of sections
        """
        groups: list[list[FeedbackSection]] = []
        group_keys: list[str] = []

        for section in sections:
            key = ReviewGenerator._normalize_content(section.content)
            match_index = None
            for i, existing_key in enumerate(group_keys):
                ratio = difflib.SequenceMatcher(None, key, existing_key).ratio()
                if ratio >= CONSOLIDATION_SIMILARITY_THRESHOLD:
                    match_index = i
                    break

            if match_index is None:
                groups.append([section])
                group_keys.append(key)
            else:
                groups[match_index].append(section)

        consolidated = [
            group[0] if len(group) == 1 else ReviewGenerator._merge_sections(group)
            for group in groups
        ]

        if len(consolidated) < len(sections):
            logger.info(
                "feedback_consolidated",
                original_count=len(sections),
                consolidated_count=len(consolidated),
            )
        return consolidated

    @staticmethod
    def _normalize_content(content: str) -> str:
        """Normalize feedback content for similarity comparison.

        Unwraps the JSON payload produced by the parser (so key ordering and the
        surrounding braces don't affect the comparison) and collapses whitespace
        and case.

        Args:
            content: Raw section content

        Returns:
            Normalized comparison string
        """
        text = content
        try:
            data = json.loads(content)
            if isinstance(data, dict) and "content" in data:
                text = str(data["content"])
        except (json.JSONDecodeError, TypeError):
            pass
        return " ".join(text.lower().split())

    @staticmethod
    def _merge_sections(group: list[FeedbackSection]) -> FeedbackSection:
        """Merge a group of near-identical sections into one cross-project section.

        Args:
            group: Two or more sections with equivalent content

        Returns:
            A single consolidated FeedbackSection
        """
        representative = group[0]

        projects: list[str] = []
        for section in group:
            if section.section_name not in projects:
                projects.append(section.section_name)

        suggestions: list[str] = []
        for section in group:
            for suggestion in section.suggestions:
                if suggestion not in suggestions:
                    suggestions.append(suggestion)

        content = (
            f"Across {len(projects)} projects ({', '.join(projects)}): " f"{representative.content}"
        )

        return FeedbackSection(
            section_name=representative.section_name,
            content=content,
            confidence=min(section.confidence for section in group),
            suggestions=suggestions,
            projects=projects,
        )
