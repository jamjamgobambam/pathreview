"""Score how actionable generated feedback is."""

import re
import structlog

logger = structlog.get_logger()

# Imperative / next-step cues that indicate concrete recommendations
_ACTION_VERBS = {
    "add",
    "include",
    "consider",
    "replace",
    "remove",
    "rewrite",
    "quantify",
    "highlight",
    "expand",
    "clarify",
    "document",
    "link",
    "update",
    "improve",
    "demonstrate",
    "show",
    "provide",
    "specify",
}

_SUGGESTION_MARKERS = {
    "should",
    "could",
    "recommend",
    "try",
    "next",
    "instead",
    "specifically",
}


class ActionabilityScorer:
    """Score whether feedback gives concrete, actionable next steps."""

    def score(self, feedback: str) -> float:
        """Score actionability of feedback text.

        Args:
            feedback: Generated feedback text (may include suggestion lines)

        Returns:
            Actionability score 0.0-1.0
        """
        if not feedback or not feedback.strip():
            logger.info("actionability_empty_feedback")
            return 0.0

        sentences = self._split_sentences(feedback)
        if not sentences:
            return 0.0

        actionable = 0
        for sentence in sentences:
            if self._is_actionable(sentence):
                actionable += 1

        # Bonus for explicit suggestion-style lines (bullets / numbered)
        bullet_lines = [
            line for line in feedback.splitlines()
            if re.match(r"^\s*([-*•]|\d+[.)])\s+", line)
        ]
        bullet_bonus = min(len(bullet_lines) * 0.05, 0.2)

        ratio = actionable / len(sentences)
        score = min(ratio + bullet_bonus, 1.0)

        logger.info(
            "actionability_scored",
            sentences=len(sentences),
            actionable=actionable,
            bullet_lines=len(bullet_lines),
            score=score,
        )
        return score

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split feedback into sentence-like units."""
        parts = re.split(r"[.!?]+|\n+", text)
        return [p.strip() for p in parts if p.strip() and len(p.strip()) > 8]

    @staticmethod
    def _is_actionable(sentence: str) -> bool:
        """Return True if a sentence looks like a concrete recommendation."""
        tokens = set(re.findall(r"[a-zA-Z]+", sentence.lower()))
        if tokens & _ACTION_VERBS:
            return True
        if tokens & _SUGGESTION_MARKERS and len(tokens) >= 4:
            return True
        # Numbered / imperative-looking short recommendations
        if re.match(r"^[-*•]?\s*\d+[.)]", sentence.strip()):
            return True
        return False
