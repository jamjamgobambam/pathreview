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
""",
        "v2": """Analyze the skills demonstrated in the provided portfolio context.

The portfolio contains {project_count} project(s):
{project_inventory}

The context below is grouped by project. Each project's evidence appears
under its own '=== Project: <id> ===' header.

Portfolio Context:
{context}

GitHub Username: {github_username}

Based on the portfolio evidence above, provide structured feedback on:
1. Demonstrated technical skills (with specific examples from projects)
2. Depth of expertise in key areas
3. Programming language proficiency
4. Framework and tool mastery

IMPORTANT — consolidate observations across projects: when the same skill is
demonstrated in more than one project, emit exactly ONE key_skills entry for
that skill and list every project that demonstrates it in that entry's
"projects" field. Do not repeat a near-identical observation once per project.

Format your response as JSON with these fields:
- key_skills: list of objects, each with fields "skill" (short skill name),
  "evidence" (specific example from the portfolio), and "projects" (list of
  ids of every project demonstrating this skill)
- language_proficiency: dict mapping languages to proficiency level
- framework_expertise: list of mastered frameworks
- tool_proficiency: list of tools used effectively
""",
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
    },
}


# Preferred version per template; templates not listed here use v1.
CURRENT_TEMPLATE_VERSIONS = {
    "skills_feedback": "v2",
}


def get_current_version(name: str) -> str:
    """Return the preferred version for a template.

    Args:
        name: Template name (skills_feedback, projects_feedback, etc.)

    Returns:
        Version string to use for this template (defaults to v1)
    """
    return CURRENT_TEMPLATE_VERSIONS.get(name, "v1")


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
