"""Parse LLM output into structured feedback."""

import json
import re
from dataclasses import dataclass

import structlog

logger = structlog.get_logger()

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)\n```", re.DOTALL)


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
    # Try JSON in code fence first
    json_match = _JSON_FENCE_RE.search(raw)
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


def parse_section_output(raw: str, section_name: str) -> FeedbackSection:
    """Parse one section's LLM output, preserving its full structure.

    Unlike parse_review_output, which fans a response out into one section per
    top-level JSON key (so callers keeping only the first section drop the
    rest), this returns a single section named after the requested section
    with the entire structured payload preserved in its content. That intact
    structure is what downstream consolidation operates on (issue #28).

    Args:
        raw: Raw LLM output string
        section_name: Name of the section this output was generated for

    Returns:
        FeedbackSection named section_name; content is the full JSON payload
        as a string, or the raw text when the output is not a JSON object
    """
    data = _extract_json_dict(raw)
    if data is None:
        logger.info("section_output_plaintext", section_name=section_name)
        return FeedbackSection(
            section_name=section_name, content=raw, confidence=0.7, suggestions=[]
        )

    # Unwrap a redundant single top-level key matching the section name
    payload: dict = data
    if set(payload.keys()) == {section_name} and isinstance(payload[section_name], dict):
        payload = payload[section_name]

    suggestions = payload.get("suggestions", [])
    if not isinstance(suggestions, list):
        suggestions = []

    logger.info("section_output_parsed", section_name=section_name)
    return FeedbackSection(
        section_name=section_name,
        content=json.dumps(payload),
        confidence=0.9,
        suggestions=suggestions,
    )


def _extract_json_dict(raw: str) -> dict | None:
    """Extract a JSON object from raw LLM output.

    Args:
        raw: Raw LLM output string, possibly wrapping JSON in a code fence

    Returns:
        Parsed dict, or None if no JSON object could be extracted
    """
    json_match = _JSON_FENCE_RE.search(raw)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            logger.warning("json_parsing_failed_in_fence", json_snippet=json_match.group(1)[:100])

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


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
                suggestions=(
                    value.get("suggestions", [])
                    if isinstance(value.get("suggestions"), list)
                    else []
                ),
            )
        else:
            section = FeedbackSection(
                section_name=key, content=str(value), confidence=0.85, suggestions=[]
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
        section_name="general_feedback", content=raw, confidence=0.7, suggestions=[]
    )

    logger.info("plaintext_output_parsed", content_length=len(raw))
    return [section]
