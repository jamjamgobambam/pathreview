"""Check if generated feedback is supported by retrieved context."""

import re
from collections.abc import Mapping, Sequence

import structlog

logger = structlog.get_logger()


def _word_set(words: str) -> frozenset[str]:
    """Build an immutable word set from a compact space-delimited string."""
    return frozenset(words.split())


_STOP_WORDS = _word_set("a an and are be been but for in is of or that the to was were")
_ROLE_SUBJECTS = _word_set(
    "candidate candidates developer developers engineer engineers he i it she they we you"
)
_REPORTING_VERBS = _word_set("has have know knows show shows")

# Normalize Unicode apostrophe and in-word hyphen variants to their ASCII forms.
_TOKEN_TRANSLATION = str.maketrans(
    {
        "\u02bc": "'",
        "\u2010": "-",
        "\u2011": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\uff07": "'",
    }
)
# Preserve common technical identifiers and apostrophized words while trimming punctuation.
_WORD_RE = re.compile(r"\.?[^\W_]+(?:[-._&/'][^\W_]+|[+#]+)*")
# Split punctuation and adjacent reporter-led sentences without breaking dotted names.
# Keep the reporter alternation in sync with _REPORTING_VERBS.
_CLAIM_BOUNDARY_RE = re.compile(r"[!?]+|\.(?=\s|$)|\.(?=(?:Has|Have|Know|Knows|Show|Shows)\s)")


class FaithfulnessChecker:
    """Score lexical grounding of feedback claims against retrieved context."""

    def check(self, feedback: str, context_chunks: Sequence[Mapping[str, object]]) -> float:
        """Return mean lexical support for extracted feedback claims.

        Args:
            feedback: Generated feedback text.
            context_chunks: Retrieved context dictionaries.

        Returns:
            Mean per-claim evidence in the inclusive range 0.0 to 1.0. Claims
            meeting their support threshold contribute 1.0; other multi-term
            claims contribute their matched-term proportion. Ordinary one-term
            claims contribute 0.0. Empty inputs return 0.0, while feedback with
            no extractable claim returns the neutral score 0.5.
        """
        if not feedback or not context_chunks:
            logger.info(
                "faithfulness_empty_input",
                has_feedback=bool(feedback),
                has_chunks=bool(context_chunks),
            )
            return 0.0

        claims = self._extract_claims(feedback)
        if not claims:
            logger.info("faithfulness_no_claims_extracted")
            return 0.5

        valid_text: list[str] = []
        skipped_chunks = 0
        for chunk in context_chunks:
            chunk_text = chunk.get("text")
            if isinstance(chunk_text, str):
                valid_text.append(chunk_text)
            else:
                skipped_chunks += 1

        if skipped_chunks:
            logger.warning(
                "faithfulness_context_chunks_skipped",
                skipped_count=skipped_chunks,
                total_count=len(context_chunks),
            )

        context_terms = self._context_terms(" ".join(valid_text))
        scores: list[float] = []
        supported_count = 0
        for claim in claims:
            required, reporter_led = self._claim_terms(claim)
            score, supported = self._score_terms(required, context_terms, allow_single=reporter_led)
            scores.append(score)
            supported_count += int(supported)

        result = sum(scores) / len(scores)
        logger.info(
            "faithfulness_checked",
            claims_count=len(claims),
            supported_count=supported_count,
            score=result,
        )
        return result

    @classmethod
    def _extract_claims(cls, text: str) -> list[str]:
        """Extract at most ten conventional, scoreable sentences."""
        claims: list[str] = []
        for fragment in _CLAIM_BOUNDARY_RE.split(text):
            claim = fragment.strip()
            if not claim:
                continue
            terms, reporter_led = cls._claim_terms(claim)
            if len(claim) > 10 or (reporter_led and terms):
                claims.append(claim)
            if len(claims) == 10:
                break
        return claims

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Return case-folded words and common technical identifiers."""
        return _WORD_RE.findall(text.translate(_TOKEN_TRANSLATION).casefold())

    @classmethod
    def _context_terms(cls, context: str) -> set[str]:
        """Return content terms after removing sentence-boundary punctuation."""
        return set(cls._tokenize(_CLAIM_BOUNDARY_RE.sub(" ", context))) - _STOP_WORDS

    @classmethod
    def _claim_terms(cls, claim: str) -> tuple[set[str], bool]:
        """Return content terms and whether a leading reporter was removed."""
        terms = [token for token in cls._tokenize(claim) if token not in _STOP_WORDS]
        if len(terms) > 1 and terms[0] in _ROLE_SUBJECTS and terms[1] in _REPORTING_VERBS:
            terms = terms[1:]

        reporter_led = bool(terms and terms[0] in _REPORTING_VERBS)
        if reporter_led:
            terms = terms[1:]
        return set(terms), reporter_led

    @staticmethod
    def _score_terms(
        required: set[str], context: set[str], *, allow_single: bool = False
    ) -> tuple[float, bool]:
        """Return partial evidence and whether the applicable threshold is met."""
        if not required:
            return 0.0, False
        if len(required) == 1 and not allow_single:
            return 0.0, False
        overlap_count = len(required & context)
        minimum_overlap = 1 if allow_single and len(required) == 1 else 2
        supported = overlap_count >= minimum_overlap
        score = 1.0 if supported else overlap_count / len(required)
        return score, supported

    @classmethod
    def _is_supported(cls, claim: str, context: str) -> bool:
        """Return whether a claim meets its lexical-overlap threshold."""
        required, reporter_led = cls._claim_terms(claim)
        context_terms = cls._context_terms(context)
        _, supported = cls._score_terms(required, context_terms, allow_single=reporter_led)
        return supported
