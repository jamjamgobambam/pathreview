"""Tone classification for generated feedback."""

import re
from dataclasses import dataclass

import structlog

logger = structlog.get_logger()

TONE_CLASSIFICATION_PROMPT = (
    "You are evaluating whether a piece of career feedback is constructive.\n"
    "\n"
    "Constructive feedback is:\n"
    "- Specific and evidence-based (references actual work or skills)\n"
    "- Actionable (gives the developer something concrete to improve)\n"
    "- Encouraging (acknowledges strengths, frames gaps as opportunities)\n"
    "\n"
    "Negative feedback is:\n"
    "- Vague or generic (could apply to anyone)\n"
    "- Discouraging (focuses on failure without a path forward)\n"
    "- Dismissive (writes off the developer's abilities or potential)\n"
    "\n"
    'Feedback to evaluate:\n"""\n{feedback}\n"""\n'
    "\n"
    "Respond with exactly one word: CONSTRUCTIVE or NEGATIVE.\n"
    "Then on a new line, explain your reasoning in one sentence."
)


@dataclass
class ToneResult:
    """Result of a tone classification check."""

    is_constructive: bool
    reason: str
    section_name: str


class ToneChecker:
    """Classify feedback tone using an LLM-as-judge pattern.

    Uses a secondary LLM call to verify that generated feedback is
    constructive (actionable, specific, encouraging) rather than negative
    (vague, discouraging, dismissive). Sections that fail are flagged for
    regeneration.
    """

    def __init__(self, llm_client: object | None = None) -> None:
        """Initialize ToneChecker.

        Args:
            llm_client: OpenAI-compatible client. When None, falls back to
                        a heuristic regex check so unit tests run without
                        a live API key.
        """
        self.llm_client = llm_client

    def check(self, section_name: str, feedback_text: str) -> ToneResult:
        """Classify whether feedback is constructive or negative.

        Args:
            section_name: Name of the feedback section being checked.
            feedback_text: The generated feedback text to evaluate.

        Returns:
            ToneResult with classification and reason.
        """
        if self.llm_client is not None:
            return self._llm_check(section_name, feedback_text)
        return self._heuristic_check(section_name, feedback_text)

    def _llm_check(self, section_name: str, feedback_text: str) -> ToneResult:
        """Use LLM-as-judge to classify tone.

        Args:
            section_name: Name of the feedback section.
            feedback_text: The generated feedback text.

        Returns:
            ToneResult from LLM classification.
        """
        prompt = TONE_CLASSIFICATION_PROMPT.format(feedback=feedback_text)

        try:
            response = self.llm_client.chat.completions.create(  # type: ignore[union-attr]
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=100,
            )
            raw = response.choices[0].message.content.strip()
            lines = raw.splitlines()
            verdict = lines[0].strip().upper()
            reason = lines[1].strip() if len(lines) > 1 else ""
            is_constructive = verdict == "CONSTRUCTIVE"

            logger.info(
                "tone_check_complete",
                section=section_name,
                is_constructive=is_constructive,
                reason=reason,
            )
            return ToneResult(
                is_constructive=is_constructive,
                reason=reason,
                section_name=section_name,
            )

        except Exception as e:
            logger.error("tone_check_failed", section=section_name, error=str(e))
            # Fail open: assume constructive so a transient API error doesn't
            # block the entire review pipeline.
            return ToneResult(
                is_constructive=True,
                reason="Tone check unavailable; defaulting to pass.",
                section_name=section_name,
            )

    def _heuristic_check(self, section_name: str, feedback_text: str) -> ToneResult:
        """Regex-based fallback when no LLM client is configured.

        Flags feedback that contains dismissive or vague patterns without
        any actionable language.

        Args:
            section_name: Name of the feedback section.
            feedback_text: The generated feedback text.

        Returns:
            ToneResult from heuristic classification.
        """
        negative_patterns = [
            r"\b(terrible|awful|horrible|bad)\b",
            r"\b(you (can't|cannot|will never|won't))\b",
            r"\b(failure|failed|hopeless|pointless)\b",
            r"\bnot good enough\b",
        ]

        actionable_signals = [
            r"\b(consider|try|improve|add|refactor|update|learn|explore)\b",
            r"\b(would benefit|could strengthen|recommend)\b",
            r"\b(next step|action item|suggestion)\b",
        ]

        text_lower = feedback_text.lower()

        for pattern in negative_patterns:
            if re.search(pattern, text_lower):
                reason = f"Dismissive language detected (matched: {pattern})"
                logger.warning("tone_check_negative", section=section_name, reason=reason)
                return ToneResult(is_constructive=False, reason=reason, section_name=section_name)

        has_actionable = any(re.search(p, text_lower) for p in actionable_signals)
        if not has_actionable and len(feedback_text.split()) < 20:
            reason = "Feedback is too vague and lacks actionable language."
            logger.warning("tone_check_vague", section=section_name, reason=reason)
            return ToneResult(is_constructive=False, reason=reason, section_name=section_name)

        return ToneResult(
            is_constructive=True,
            reason="No negative patterns detected.",
            section_name=section_name,
        )
