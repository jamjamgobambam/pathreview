"""Bias detection in generated feedback."""

import re
import unicodedata

import structlog

logger = structlog.get_logger()


class BiasDetector:
    """Detect biased language in feedback via lexicon + proximity.

    Rather than matching rigid full-sentence templates, we detect when a
    *subject* (the person/background being judged) and a *dismissive*
    predicate (the negative judgment) co-occur within a small word window.
    This raises recall (catches novel phrasings) while the proximity window
    and a negation guard keep false positives low.
    """

    # Subjects being judged, keyed by the reason reported when matched.
    SUBJECTS = {
        "Dismissive language about educational background": [
            "bootcamp",
            "coding bootcamp",
            "self taught",
            "online course",
            "online class",
            "non traditional",
        ],
        "Demographic assumptions detected": [
            "young developer",
            "young programmer",
            "old developer",
            "old programmer",
            "aged developer",
            "aged programmer",
            "immigrant developer",
            "international developer",
            "foreign developer",
            "person from poor",
            "person from rich",
            "working class",
            "poor background",
            "rich background",
        ],
    }

    # Dismissive predicates. Innocuous single words (e.g. "fundamentals") are
    # deliberately excluded; only the dismissive term ("lack") qualifies.
    DISMISSIVE = [
        "cannot",
        "can not",
        "cant",
        "wont",
        "will not",
        "never",
        "insufficient",
        "inadequate",
        "inferior",
        "not equal",
        "not comparable",
        "struggle",
        "lack",
        "lacking",
        "missing",
        "not real",
        "doesnt count",
        "doesnt prepare",
        "not prepared",
        "not enough",
        "not qualified",
        "cant afford",
        "cant handle",
        "cant write",
        "cant code",
    ]

    # A dismissive term immediately preceded by one of these is negated
    # ("don't lack rigor") and should not be flagged.
    NEGATIONS = {"not", "never", "no", "isnt", "arent", "dont", "doesnt"}

    # Max word-token gap between a subject and a dismissive term.
    WINDOW = 6

    @staticmethod
    def _normalize(text: str) -> list[str]:
        """Normalize text and return word tokens.

        Handles Unicode/zero-width evasion, hyphen and apostrophe variants,
        and collapses whitespace.
        """
        text = unicodedata.normalize("NFKC", text)
        # Drop format/zero-width chars (e.g. U+200B) used to split keywords.
        text = "".join(c for c in text if unicodedata.category(c) != "Cf")
        text = text.lower().replace("-", " ")
        # Delete apostrophes so "can't" -> "cant" before other punctuation is
        # turned into whitespace (otherwise "can't" would split into "can t").
        text = text.replace("'", "").replace("’", "")
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        return text.split()

    @staticmethod
    def _word_match(word: str, token: str) -> bool:
        """Match a lexicon word to a token, tolerating a plural 's' suffix."""
        return re.fullmatch(re.escape(word) + "s?", token) is not None

    @staticmethod
    def _spans(tokens: list[str], phrases: list[str]) -> list[tuple[int, int]]:
        """Return (start, end) token-index spans where any phrase matches."""
        hits = []
        for phrase in phrases:
            words = phrase.split()
            n = len(words)
            for i in range(len(tokens) - n + 1):
                if all(BiasDetector._word_match(w, tokens[i + j]) for j, w in enumerate(words)):
                    hits.append((i, i + n - 1))
        return hits

    @staticmethod
    def detect_bias(text: str) -> tuple[bool, str]:
        """Detect biased language in feedback.

        Flags when a subject term and a dismissive term co-occur within
        WINDOW words of each other and the dismissal is not itself negated
        (i.e "bootcamp not qualified.").

        Args:
            text: Feedback text

        Returns:
            Tuple of (is_biased, reason)
        """
        tokens = BiasDetector._normalize(text)
        pred_spans = BiasDetector._spans(tokens, BiasDetector.DISMISSIVE)

        for reason, subjects in BiasDetector.SUBJECTS.items():
            for s_start, s_end in BiasDetector._spans(tokens, subjects):
                for p_start, p_end in pred_spans:
                    gap = max(s_start - p_end, p_start - s_end)
                    if gap > BiasDetector.WINDOW:
                        continue
                    # Skip negated dismissals ("...don't lack rigor...").
                    if p_start > 0 and tokens[p_start - 1] in BiasDetector.NEGATIONS:
                        continue
                    logger.warning("bias_detected", reason=reason)
                    return True, reason

        return False, ""
