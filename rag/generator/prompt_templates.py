"""Versioned prompt templates for review generation."""

import structlog

logger = structlog.get_logger()


PROMPT_TEMPLATES = {
    "skills_feedback": {
        "v1": """Analyze the skills demonstrated in the provided portfolio context.

Portfolio Context:
{context}

GitHub Username: {github_username}
Project Count: {project_count}

Based on the portfolio evidence above, provide structured feedback on:
1. Demonstrated technical skills (with specific examples from projects)
2. Depth of expertise in key areas
3. Programming language proficiency
4. Framework and tool mastery

Format your response as JSON with these fields:
- key_skills: list of demonstrated skills with evidence
- language_proficiency: dict mapping languages to proficiency level
- framework_expertise: list of mastered frameworks
- tool_proficiency: list of tools used effectively
"""
    },
    "projects_feedback": {
        "v1": """Evaluate the quality and presentation of projects in the portfolio.

Portfolio Context:
{context}

GitHub Username: {github_username}
Project Count: {project_count}

Assess:
1. Project scope and complexity
2. Code quality indicators
3. Documentation and README quality
4. Completeness and polish

Format as JSON:
- standout_projects: list of exemplary projects
- project_quality_score: overall 0-1 score
- complexity_level: beginner/intermediate/advanced
- presentation_notes: suggestions for improvement
"""
    },
    "presentation_feedback": {
        "v1": """Evaluate the overall presentation quality of the portfolio.

Portfolio Context:
{context}

GitHub Username: {github_username}
Project Count: {project_count}

Review:
1. README quality and completeness
2. Profile information accessibility
3. Project organization
4. Visual presentation

Format as JSON:
- readme_quality: 0-1 score
- profile_completeness: percentage
- organization_score: 0-1
- presentation_suggestions: list of improvements
"""
    },
    "gaps_feedback": {
        "v1": """Identify skill gaps relative to job market demands.

Portfolio Context:
{context}

GitHub Username: {github_username}
Project Count: {project_count}

Analyze:
1. High-demand skills not demonstrated
2. Underrepresented areas
3. Market alignment
4. Growth opportunities

Format as JSON:
- missing_high_demand_skills: list with market demand info
- underrepresented_areas: areas with low portfolio coverage
- market_alignment_score: 0-1
- recommended_learning_areas: prioritized list
"""
    },
    "first_impression": {
        "v1": """Provide a 2-3 sentence overall first impression of this portfolio.

Portfolio Context:
{context}

GitHub Username: {github_username}
Project Count: {project_count}

Write a concise, professional summary capturing:
- Overall skill level and trajectory
- Most impressive aspects
- Immediate opportunities for growth

Provide only the summary text, no JSON formatting needed.
"""
    }
}


TONE_CHECK_TEMPLATE = """You are reviewing one section of automated portfolio feedback for tone.

Classify whether the feedback below is written CONSTRUCTIVELY. Constructive feedback is:
- actionable (points to a concrete next step, not just a complaint)
- specific (references the portfolio, not vague generalities)
- encouraging (respectful and motivating, even when critical)

Feedback is NON-constructive if it is discouraging, dismissive, condescending, or vague.

Feedback section to classify:
\"\"\"
{feedback}
\"\"\"

Respond with ONLY a JSON object, no prose, in this exact shape:
{{"constructive": true or false, "reason": "one short sentence explaining the verdict"}}
"""


REGENERATION_GUIDANCE = (
    "\n\nIMPORTANT: A previous draft of this section was flagged as non-constructive "
    "for the following reason: {reason}. Rewrite the feedback so it is actionable, "
    "specific, and encouraging while keeping it honest. Do not be dismissive or vague."
)


def get_tone_check_prompt(feedback: str) -> str:
    """Build the tone-classification prompt for a feedback section.

    Args:
        feedback: The generated feedback text to classify

    Returns:
        Prompt string instructing the LLM to classify tone as JSON
    """
    return TONE_CHECK_TEMPLATE.format(feedback=feedback)


def get_template(name: str, version: str = "v1") -> str:
    """Retrieve a prompt template.

    Args:
        name: Template name (skills_feedback, projects_feedback, etc.)
        version: Template version (default v1)

    Returns:
        Template string with placeholders

    Raises:
        ValueError: If template not found
    """
    if name not in PROMPT_TEMPLATES:
        available = list(PROMPT_TEMPLATES.keys())
        raise ValueError(f"Template '{name}' not found. Available: {available}")

    versions = PROMPT_TEMPLATES[name]
    if version not in versions:
        available = list(versions.keys())
        raise ValueError(f"Version '{version}' not found for '{name}'. Available: {available}")

    template = versions[version]
    logger.info("template_retrieved", name=name, version=version)
    return template
