"""LLM-based review generation."""

import json
from dataclasses import dataclass

import openai
import structlog

from .output_parser import FeedbackSection, parse_section_output
from .prompt_templates import get_current_version, get_template

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
        # Get template (skills_feedback uses the project-aware v2)
        template = get_template(section_name, get_current_version(section_name))

        # Format context, grouped by project
        context_text = self._format_context(context_chunks)
        inventory = self._project_inventory(context_chunks)
        github_username = profile_data.get("github_username", "")
        project_count = len(profile_data.get("projects", []))

        prompt = template.format(
            context=context_text,
            github_username=github_username,
            project_count=project_count,
            project_inventory="\n".join(f"- {project}" for project in inventory)
            or "- (no projects identified)",
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

        # Parse output, preserving the full structured payload for this section
        return parse_section_output(content, section_name)

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

        # Add citations after consolidation, which needs content to still be
        # parseable JSON
        all_sections = [self._add_citations(section, retrieved_chunks) for section in all_sections]

        logger.info("full_review_generated", section_count=len(all_sections))
        return all_sections

    @staticmethod
    def _format_context(chunks: list[dict]) -> str:
        """Format retrieved chunks into a context string grouped by project.

        Chunks are grouped under an explicit '=== Project: <id> ===' header
        per source project so the model sees project boundaries instead of
        one flat blob (issue #28).

        Args:
            chunks: List of retrieved chunks

        Returns:
            Formatted context string with per-project headers
        """
        grouped: dict[str, list[dict]] = {}
        for chunk in chunks[:10]:  # Limit to 10 chunks
            source = chunk.get("metadata", {}).get("source_id", "unknown")
            grouped.setdefault(source, []).append(chunk)

        parts = []
        i = 1
        for source, source_chunks in grouped.items():
            parts.append(f"=== Project: {source} ===")
            for chunk in source_chunks:
                score = chunk.get("score", 0)
                text = chunk.get("text", "")
                parts.append(f"[{i}] (relevance: {score:.2f})\n{text}")
                i += 1

        return "\n\n".join(parts)

    @staticmethod
    def _project_inventory(chunks: list[dict]) -> list[str]:
        """List distinct project ids present in the retrieved chunks.

        Args:
            chunks: List of retrieved chunks

        Returns:
            Distinct source_id values in retrieval order; chunks without a
            source_id are skipped rather than reported as a project
        """
        inventory: list[str] = []
        for chunk in chunks:
            source = chunk.get("metadata", {}).get("source_id")
            if source and source not in inventory:
                inventory.append(source)
        return inventory

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
        """Consolidate duplicate cross-project observations in each section.

        When several projects share a tech stack, the model may emit one
        near-identical key_skills entry per project. Entries whose normalized
        skill name matches are merged into a single entry whose "projects"
        list is the union of the originals' (issue #28). Sections without
        structured key_skills data pass through unchanged.

        Args:
            sections: List of feedback sections

        Returns:
            Consolidated list of sections, same length and order
        """
        return [ReviewGenerator._merge_duplicate_skills(s) for s in sections]

    @staticmethod
    def _merge_duplicate_skills(section: FeedbackSection) -> FeedbackSection:
        """Merge key_skills entries that describe the same skill.

        Args:
            section: Feedback section whose content may be a JSON object
                with a key_skills list

        Returns:
            Section with same-skill entries merged and their project lists
            unioned; the original section if content has no key_skills data
        """
        try:
            data = json.loads(section.content)
        except (json.JSONDecodeError, TypeError):
            return section
        if not isinstance(data, dict) or not isinstance(data.get("key_skills"), list):
            return section

        merged: dict[str, dict] = {}  # normalized skill name -> merged entry
        result: list = []
        for entry in data["key_skills"]:
            if not isinstance(entry, dict) or not str(entry.get("skill", "")).strip():
                result.append(entry)  # no skill name to merge on
                continue

            key = " ".join(str(entry["skill"]).split()).casefold()
            projects = ReviewGenerator._entry_projects(entry)

            if key not in merged:
                new_entry = dict(entry)
                # Normalize to a "projects" list, but only when the entry
                # carries project info — don't add noise to entries without it
                if "project" in new_entry or "projects" in new_entry:
                    new_entry.pop("project", None)
                    new_entry["projects"] = projects
                merged[key] = new_entry
                result.append(new_entry)
                continue

            # Duplicate skill: union its projects into the first entry
            existing = merged[key]
            if projects:
                existing_projects = existing.setdefault("projects", [])
                existing.pop("project", None)
                for project in projects:
                    if project not in existing_projects:
                        existing_projects.append(project)

        if len(result) == len(data["key_skills"]) and not any(
            "project" in e for e in data["key_skills"] if isinstance(e, dict)
        ):
            # Nothing merged and nothing renamed: keep the section as-is so
            # single-project reviews round-trip byte-identically
            return section

        data["key_skills"] = result
        logger.info(
            "duplicate_skills_consolidated",
            section_name=section.section_name,
            merged_count=len(data["key_skills"]),
        )
        return FeedbackSection(
            section_name=section.section_name,
            content=json.dumps(data),
            confidence=section.confidence,
            suggestions=section.suggestions,
        )

    @staticmethod
    def _entry_projects(entry: dict) -> list[str]:
        """Extract the project ids a key_skills entry cites.

        Accepts both the v2 "projects" list and a legacy singular "project"
        string.

        Args:
            entry: A key_skills entry dict

        Returns:
            List of project id strings (possibly empty)
        """
        projects = entry.get("projects")
        if isinstance(projects, list):
            return [str(p) for p in projects if p]
        project = entry.get("project")
        if isinstance(project, str) and project:
            return [project]
        return []
