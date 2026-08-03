"""Deterministic, offline review generation for benchmarking and tests."""

import structlog

from .output_parser import FeedbackSection

logger = structlog.get_logger()

# Section order mirrors ReviewGenerator.generate_full_review so the two
# generators are interchangeable from a caller's point of view.
SECTION_NAMES = [
    "skills_feedback",
    "projects_feedback",
    "presentation_feedback",
    "gaps_feedback",
    "first_impression",
]

# Openers are keyed by section so each section reads differently while staying
# a pure function of its inputs. They deliberately avoid vocabulary likely to
# appear in a portfolio (project, skills, experience) so that the faithfulness
# score reflects the quoted evidence rather than incidental boilerplate overlap.
_SECTION_OPENERS = {
    "skills_feedback": "The retrieved evidence repeatedly surfaces",
    "projects_feedback": "Recurring signals across the indexed excerpts include",
    "presentation_feedback": "The clearest self-presentation signals are",
    "gaps_feedback": "Coverage looks thinner than expected around",
    "first_impression": "A first read is dominated by",
}

_DEFAULT_OPENER = "The retrieved excerpts emphasise"

# Terms shorter than this, or present in this stop list, carry too little
# signal to be worth quoting back as evidence.
_MIN_TERM_LENGTH = 4

_TERM_STOP_WORDS = frozenset(
    {
        "about",
        "after",
        "also",
        "been",
        "both",
        "each",
        "from",
        "have",
        "into",
        "more",
        "most",
        "obtain",
        "only",
        "over",
        "same",
        "some",
        "such",
        "than",
        "that",
        "them",
        "then",
        "there",
        "these",
        "they",
        "this",
        "through",
        "used",
        "using",
        "very",
        "were",
        "what",
        "when",
        "which",
        "while",
        "with",
        "would",
        "your",
    }
)

# Number of evidence terms quoted per sentence. FaithfulnessChecker treats a
# sentence as supported when it shares at least two non-stopword tokens with the
# context, so a group of three leaves one token of slack.
_TERMS_PER_SENTENCE = 3

# Sentences per section: enough to give FaithfulnessChecker several claims to
# score without flooding its ten-claim ceiling from a single section.
_GROUPS_PER_SECTION = 3


class MockReviewGenerator:
    """Generate review feedback deterministically, without calling a model.

    The generator is the offline counterpart to
    :class:`~rag.generator.review_generator.ReviewGenerator`. It exposes the same
    ``generate_section`` / ``generate_full_review`` surface, imports no HTTP
    client, and derives every sentence from the retrieved chunks it is given, so
    the same chunks always produce byte-identical feedback.

    Feedback is grounded rather than canned on purpose: ``FaithfulnessChecker``
    scores the share of feedback sentences that overlap the retrieved context, so
    canned text would pin that metric near zero on every benchmark and make it
    useless as a regression signal. Each section quotes salient terms lifted from
    the top-ranked chunks and closes with one ungrounded recommendation, so the
    score tracks how much distinct evidence retrieval actually returned.

    Unlike ``ReviewGenerator`` this class does not append a ``Sources:`` citation
    line, because that fragment is drawn from chunk metadata rather than chunk
    text and would depress faithfulness for reasons unrelated to review quality.
    """

    def generate_section(
        self,
        section_name: str,
        context_chunks: list[dict],
        profile_data: dict,
    ) -> FeedbackSection:
        """Generate deterministic feedback for a single section.

        Args:
            section_name: Section name (skills_feedback, projects_feedback, etc.)
            context_chunks: Retrieved context chunks
            profile_data: Profile metadata

        Returns:
            FeedbackSection whose content is derived from context_chunks
        """
        terms = self._salient_terms(context_chunks)

        if not terms:
            logger.info("mock_generation_without_context", section=section_name)
            return FeedbackSection(
                section_name=section_name,
                content=(
                    f"No retrieved context was available for {section_name}, so this "
                    "section reports no evidence rather than inventing findings."
                ),
                confidence=0.0,
                suggestions=[],
            )

        rotation = SECTION_NAMES.index(section_name) if section_name in SECTION_NAMES else 0
        groups = self._term_groups(terms, rotation)
        opener = _SECTION_OPENERS.get(section_name, _DEFAULT_OPENER)
        username = str(profile_data.get("github_username", "") or "this candidate")

        sentences = [
            f"{opener} {' '.join(group)} in the material retrieved for {section_name}."
            for group in groups
        ]
        sentences.append(
            f"Reviewers should ask {username} to make the strongest of these signals "
            "visible above the fold."
        )

        return FeedbackSection(
            section_name=section_name,
            content=" ".join(sentences),
            confidence=self._confidence(len(groups)),
            suggestions=[
                f"Expand the {section_name.replace('_', ' ')} narrative around {' '.join(group)}."
                for group in groups
            ],
        )

    def generate_full_review(
        self,
        profile_data: dict,
        retrieved_chunks: list[dict],
    ) -> list[FeedbackSection]:
        """Generate deterministic feedback across every review section.

        Args:
            profile_data: Profile metadata and projects
            retrieved_chunks: Context chunks from retrieval

        Returns:
            List of FeedbackSections, one per entry in SECTION_NAMES
        """
        sections = [
            self.generate_section(section_name, retrieved_chunks, profile_data)
            for section_name in SECTION_NAMES
        ]

        logger.info(
            "mock_full_review_generated",
            section_count=len(sections),
            chunk_count=len(retrieved_chunks),
        )
        return sections

    @staticmethod
    def _confidence(group_count: int) -> float:
        """Derive a confidence score from how much evidence was available.

        Args:
            group_count: Number of grounded sentences produced

        Returns:
            Confidence between 0.0 and 0.9
        """
        return round(min(0.9, 0.5 + 0.1 * group_count), 2)

    @staticmethod
    def _salient_terms(chunks: list[dict]) -> list[str]:
        """Collect evidence terms from chunks in a stable order.

        Chunks are sorted by descending score then ascending id so that ties in
        retrieval order cannot change the output. Only tokens that are already
        alphanumeric are kept: ``FaithfulnessChecker`` compares raw whitespace
        tokens, so a term carrying attached punctuation would never match the
        context it came from.

        Args:
            chunks: Retrieved chunks with 'text', 'score' and 'id' keys

        Returns:
            Deduplicated lowercase terms, most relevant chunk first
        """
        ordered = sorted(
            chunks,
            key=lambda chunk: (-float(chunk.get("score", 0.0) or 0.0), str(chunk.get("id", ""))),
        )

        terms: dict[str, None] = {}
        for chunk in ordered:
            for raw_token in str(chunk.get("text", "")).split():
                token = raw_token.lower()
                if len(token) < _MIN_TERM_LENGTH or not token.isalnum():
                    continue
                if token in _TERM_STOP_WORDS:
                    continue
                terms[token] = None

        return list(terms)

    @staticmethod
    def _term_groups(terms: list[str], rotation: int) -> list[list[str]]:
        """Split terms into per-sentence groups, rotated per section.

        Rotating the term list by section index means each section quotes a
        different slice of the evidence, so the five sections do not collapse
        into five copies of the same sentence.

        Args:
            terms: Ordered salient terms
            rotation: Section index used to rotate the term list

        Returns:
            Up to _GROUPS_PER_SECTION groups of terms
        """
        if not terms:
            return []

        offset = (rotation * _TERMS_PER_SENTENCE) % len(terms)
        rotated = terms[offset:] + terms[:offset]

        groups: list[list[str]] = []
        for start in range(0, len(rotated), _TERMS_PER_SENTENCE):
            if len(groups) == _GROUPS_PER_SECTION:
                break
            groups.append(rotated[start : start + _TERMS_PER_SENTENCE])

        return groups
