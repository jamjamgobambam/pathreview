"""Skill extraction tool."""

import re
import structlog
from .base import BaseTool, ToolResult

logger = structlog.get_logger()


class SkillExtractor(BaseTool):
    """Extract skills from resume and repository metadata."""

    name = "skill_extractor"
    description = "Extract skills from resume and repository data"

    # Skill patterns and their categories
    SKILL_PATTERNS = {
        "languages": {
            "Python": r"\bpython\b",
            "JavaScript": r"\bjavascript|js\b",
            "TypeScript": r"\btypescript|ts\b",
            "Java": r"\bjava\b",
            "C#": r"\bc#|csharp\b",
            "C++": r"\bc\+\+|cpp\b",
            "Go": r"\bgo\b",
            "Rust": r"\brust\b",
            "Ruby": r"\bruby\b",
            "PHP": r"\bphp\b",
            "SQL": r"\bsql\b",
        },
        "frameworks": {
            "React": r"\breact\b",
            "Vue": r"\bvue\b",
            "Angular": r"\bangular\b",
            "Django": r"\bdjango\b",
            "Flask": r"\bflask\b",
            "FastAPI": r"\bfastapi\b",
            "Spring": r"\bspring\b",
            "Express": r"\bexpress\b",
            "Next.js": r"\bnext\.js|nextjs\b",
            "Svelte": r"\bsvelte\b",
        },
        "tools": {
            "Git": r"\bgit\b",
            "Docker": r"\bdocker\b",
            "Kubernetes": r"\bkubernetes|k8s\b",
            "Git": r"\bgit\b",
            "GraphQL": r"\bgraphql\b",
            "REST": r"\brest|restful\b",
            "AWS": r"\baws\b",
            "GCP": r"\bgcp|google\s+cloud\b",
            "Azure": r"\bazure\b",
            "Terraform": r"\bterraform\b",
        },
        "databases": {
            "PostgreSQL": r"\bpostgres|postgresql\b",
            "MySQL": r"\bmysql\b",
            "MongoDB": r"\bmongodb\b",
            "Redis": r"\bredis\b",
            "Elasticsearch": r"\belasticsearch\b",
            "Firebase": r"\bfirebase\b",
        },
        "cloud": {
            "AWS": r"\baws\b",
            "GCP": r"\bgcp|google\s+cloud\b",
            "Azure": r"\bazure\b",
            "Heroku": r"\bheroku\b",
        }
    }

    def execute(self, input_data: dict) -> ToolResult:
        """Extract skills.

        Args:
            input_data: Must contain 'resume_text' and 'repo_metadata'

        Returns:
            ToolResult with detected skills by category
        """
        resume_text = input_data.get("resume_text", "")
        repo_metadata = input_data.get("repo_metadata", {})

        try:
            skills = self._extract_skills(resume_text, repo_metadata)
            return ToolResult(success=True, data=skills)

        except Exception as e:
            logger.error("skill_extractor_error", error=str(e))
            return ToolResult(
                success=False,
                data={},
                error=str(e)
            )

    def _extract_skills(self, resume_text: str, repo_metadata: dict) -> dict:
        """Extract skills from resume and repo metadata.

        Args:
            resume_text: Resume text content
            repo_metadata: Repository metadata dict

        Returns:
            Dict with skills grouped by category
        """
        combined_text = resume_text.lower()

        # Add repo data to search text
        if isinstance(repo_metadata, dict):
            all_langs = repo_metadata.get("all_languages", [])
            frameworks = repo_metadata.get("frameworks", [])
            combined_text += " " + " ".join(all_langs).lower()
            combined_text += " " + " ".join(frameworks).lower()

        # Check for Python type annotations (evidence of Python expertise)
        if re.search(r'\bdef\s+\w+.*->\s*\w+', resume_text):
            combined_text += " python type annotations"

        detected_skills = {}

        for category, patterns in self.SKILL_PATTERNS.items():
            skills_in_category = []

            for skill_name, pattern in patterns.items():
                if re.search(pattern, combined_text):
                    skills_in_category.append(skill_name)

            detected_skills[category] = skills_in_category

        logger.info("skills_extracted",
                   languages=len(detected_skills.get("languages", [])),
                   frameworks=len(detected_skills.get("frameworks", [])),
                   tools=len(detected_skills.get("tools", [])))

        return detected_skills
