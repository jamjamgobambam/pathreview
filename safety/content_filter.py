"""Content filter for generated feedback."""

import json
import re

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
                filtered_text = re.sub(pattern, "[CONTENT REMOVED]", filtered_text, flags=re.IGNORECASE)

        return filtered_text, was_filtered


class ToneClassifier:
    """Classify whether generated feedback is written constructively.

    Unlike ``ContentFilter`` (which uses regex to catch genuinely harmful
    phrases), this uses an LLM to judge *tone*: feedback that is dismissive,
    discouraging, or vague passes the harmful-content filter but should still
    be rejected and regenerated.

    The LLM client is injected so the classifier stays testable and reuses the
    same provider/config as the generator (see ``rag.generator``).
    """

    def __init__(self, client, model: str):
        """Initialize the tone classifier.

        Args:
            client: An OpenAI-compatible client with ``chat.completions.create``
            model: Model identifier to use for classification
        """
        self.client = client
        self.model = model

    def classify(self, text: str) -> tuple[bool, str]:
        """Classify whether a feedback section is constructive.

        Args:
            text: Feedback section content to classify

        Returns:
            Tuple of (is_constructive, reason). Fails open: if the text is
            empty or the classification call/parse fails, returns
            ``(True, <reason>)`` so tone-checking never blocks delivery.
        """
        # Local import avoids a circular import (rag imports safety indirectly)
        from rag.generator.prompt_templates import get_tone_check_prompt

        if not text or not text.strip():
            return True, "empty feedback, nothing to classify"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a strict feedback-tone reviewer."},
                    {"role": "user", "content": get_tone_check_prompt(text)},
                ],
                temperature=0.0,
                max_tokens=200,
            )
            raw = response.choices[0].message.content or ""
            verdict = self._parse_verdict(raw)
            if verdict is None:
                logger.warning("tone_classification_unparseable", raw_snippet=raw[:120])
                return True, "tone verdict unparseable, defaulting to constructive"

            is_constructive, reason = verdict
            logger.info("tone_classified", constructive=is_constructive, reason=reason)
            return is_constructive, reason

        except Exception as exc:  # fail open — never block delivery on a tone-check error
            logger.error("tone_classification_failed", error=str(exc))
            return True, "tone check unavailable, defaulting to constructive"

    @staticmethod
    def _parse_verdict(raw: str) -> tuple[bool, str] | None:
        """Extract the (constructive, reason) verdict from an LLM response.

        Args:
            raw: Raw LLM response text (expected to contain a JSON object)

        Returns:
            Parsed (is_constructive, reason) tuple, or None if not parseable.
        """
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
        if "constructive" not in data:
            return None
        return bool(data["constructive"]), str(data.get("reason", ""))
