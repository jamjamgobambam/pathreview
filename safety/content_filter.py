"""Content filter for generated feedback."""

import re
from dataclasses import dataclass
from typing import Any

import structlog

logger = structlog.get_logger()


class ContentFilter:
    """Filter genuinely harmful content from generated feedback."""

    # Specific harmful patterns (not broad keyword matching)
    HARMFUL_PATTERNS = [
        r"(?:kill|harm|hurt)\s+(?:yourself|yourself|themself|themselves)",
        r"(?:suicide|self-harm|cut\s+yourself)",
        r"(?:hate|despise)\s+(?:themself|themselves|yourself)",
        r"(?:worthless|useless|trash|garbage)\s+(?:person|human)",
        r"(?:illegal|unlawful)\s+(?:activity|action|conduct)",
        r"(?:child|minor)\s+(?:abuse|exploitation|trafficking)",
    ]

    @staticmethod
    def filter(text: str) -> tuple[str, bool]:
        """Filter harmful content from text.

        Args:
            text: Text to filter

        Returns:
            Tuple of (filtered_text, was_filtered)
        """
        was_filtered = False
        filtered_text = text

        for pattern in ContentFilter.HARMFUL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning("harmful_content_detected", pattern=pattern)
                was_filtered = True
                # Replace harmful phrases with neutral text
                filtered_text = re.sub(
                    pattern, "[CONTENT REMOVED]", filtered_text, flags=re.IGNORECASE
                )

        return filtered_text, was_filtered


@dataclass
class ToneCheckResult:
    """Result of a tone classification check."""

    is_constructive: bool
    raw_response: str


class ToneChecker:
    """Classify generated feedback as constructive or negative using an LLM."""

    MAX_RETRIES = 2

    SYSTEM_PROMPT = (
        "You are a strict but fair classifier. Given a piece of portfolio review "
        "feedback, decide if it is CONSTRUCTIVE (actionable, specific, and "
        "encouraging, even if it contains criticism) or NEGATIVE (discouraging, "
        "vague, dismissive, or overly harsh with no actionable guidance). "
        "Respond with exactly one word: CONSTRUCTIVE or NEGATIVE."
    )

    def __init__(self, client: Any, model: str):
        """Initialize the tone checker.

        Args:
            client: An OpenAI-compatible chat client (reused from ReviewGenerator)
            model: Model name to use for classification
        """
        self.client = client
        self.model = model

    def check(self, text: str) -> ToneCheckResult:
        """Classify a piece of feedback text as constructive or not.

        Args:
            text: Feedback content to classify

        Returns:
            ToneCheckResult with the verdict and raw model response
        """
        if not text or not text.strip():
            # Nothing to classify - don't reject on empty content
            return ToneCheckResult(is_constructive=True, raw_response="")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0.0,
            max_tokens=5,
        )
        raw_response = response.choices[0].message.content.strip().upper()
        is_ok = raw_response.startswith("CONSTRUCTIVE")

        if not is_ok:
            logger.warning("feedback_tone_check_failed", verdict=raw_response)

        return ToneCheckResult(is_constructive=is_ok, raw_response=raw_response)
