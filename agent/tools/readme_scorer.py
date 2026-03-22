"""README quality scorer tool."""

import re
import structlog
from .base import BaseTool, ToolResult

logger = structlog.get_logger()


class ReadmeScorer(BaseTool):
    """Score README quality."""

    name = "readme_scorer"
    description = "Score README file quality"

    def execute(self, input_data: dict) -> ToolResult:
        """Score README quality.

        Args:
            input_data: Must contain 'readme_content' or 'github_username'/'repo_name'

        Returns:
            ToolResult with README quality scores
        """
        readme_content = input_data.get("readme_content", "")

        if not readme_content:
            logger.warning("readme_scorer_empty_content")
            return ToolResult(
                success=True,
                data={
                    "has_readme": False,
                    "word_count": 0,
                    "word_count_category": "minimal",
                    "has_installation_section": False,
                    "has_usage_section": False,
                    "has_badges": False,
                    "has_demo_link": False,
                    "has_tech_stack_section": False,
                    "overall_score": 0.0
                }
            )

        try:
            scores = self._score_readme(readme_content)
            return ToolResult(success=True, data=scores)

        except Exception as e:
            logger.error("readme_scorer_error", error=str(e))
            return ToolResult(
                success=False,
                data={},
                error=str(e)
            )

    @staticmethod
    def _score_readme(content: str) -> dict:
        """Score README content.

        Args:
            content: README file content

        Returns:
            Dict with quality scores
        """
        has_readme = bool(content.strip())
        word_count = len(content.split())

        # Categorize word count
        if word_count < 100:
            word_count_category = "minimal"
        elif word_count < 500:
            word_count_category = "adequate"
        else:
            word_count_category = "comprehensive"

        # Check for sections (case-insensitive)
        content_lower = content.lower()
        has_installation = bool(
            re.search(r'(install|setup|getting\s+started)', content_lower)
        )
        has_usage = bool(
            re.search(r'(usage|how\s+to\s+use|quickstart|example)', content_lower)
        )

        # Check for badges ([![...](...)]), common format
        has_badges = bool(re.search(r'\!\[.*?\]\(.*?\)', content))

        # Check for demo/live links
        has_demo = bool(
            re.search(r'(demo|live\s+demo|try\s+it|see\s+it|live\s+link)', content_lower)
        )

        # Check for tech stack section
        has_tech_stack = bool(
            re.search(r'(tech\s+stack|technologies|built\s+with|technology|stack)', content_lower)
        )

        # Calculate overall score (0-1)
        score_components = [
            has_readme,
            has_installation,
            has_usage,
            has_badges,
            has_demo,
            has_tech_stack,
            min(word_count / 500, 1.0)  # Bonus for comprehensive content
        ]
        overall_score = sum(score_components) / len(score_components)

        logger.info("readme_scored", word_count=word_count,
                   category=word_count_category, score=overall_score)

        return {
            "has_readme": has_readme,
            "word_count": word_count,
            "word_count_category": word_count_category,
            "has_installation_section": has_installation,
            "has_usage_section": has_usage,
            "has_badges": has_badges,
            "has_demo_link": has_demo,
            "has_tech_stack_section": has_tech_stack,
            "overall_score": overall_score
        }
