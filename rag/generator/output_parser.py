"""Parse LLM output into structured feedback."""

from dataclasses import dataclass
import json
import re
import structlog

logger = structlog.get_logger()


@dataclass
class FeedbackSection:
    """Structured feedback section."""
    section_name: str
    content: str
    confidence: float
    suggestions: list[str]


def parse_review_output(raw: str) -> list[FeedbackSection]:
    """Parse LLM output into structured feedback sections.

    Args:
        raw: Raw LLM output string

    Returns:
        List of FeedbackSection objects
    """
    sections = []

    # Try JSON in code fence first
    json_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", raw, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
        try:
            data = json.loads(json_str)
            return _parse_json_output(data)
        except json.JSONDecodeError:
            logger.warning("json_parsing_failed_in_fence", json_snippet=json_str[:100])

    # Try raw JSON
    try:
        data = json.loads(raw)
        return _parse_json_output(data)
    except json.JSONDecodeError:
        logger.warning("raw_json_parsing_failed")

    # Fallback to plain text parsing
    return _parse_plaintext_output(raw)


def _parse_json_output(data: dict) -> list[FeedbackSection]:
    """Parse structured JSON output.

    Args:
        data: Parsed JSON dict

    Returns:
        List of FeedbackSection objects
    """
    sections = []

    # Handle both single-level and nested structures
    for key, value in data.items():
        if isinstance(value, dict):
            section = FeedbackSection(
                section_name=key,
                content=json.dumps(value),
                confidence=0.9,
                suggestions=value.get("suggestions", [])
                    if isinstance(value.get("suggestions"), list) else []
            )
        else:
            section = FeedbackSection(
                section_name=key,
                content=str(value),
                confidence=0.85,
                suggestions=[]
            )
        sections.append(section)

    logger.info("json_output_parsed", section_count=len(sections))
    return sections


def _parse_plaintext_output(raw: str) -> list[FeedbackSection]:
    """Parse plain text output into sections.

    Args:
        raw: Raw text string

    Returns:
        List of FeedbackSection objects (single section from raw text)
    """
    # Treat entire text as a single feedback section
    section = FeedbackSection(
        section_name="general_feedback",
        content=raw,
        confidence=0.7,
        suggestions=[]
    )

    logger.info("plaintext_output_parsed", content_length=len(raw))
    return [section]
