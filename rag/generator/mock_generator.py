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
# context, so quoting three leaves one token of slack — and a chunk too thin to
# supply two is reported as an unsupported claim, which is the honest outcome.
_TERMS_PER_SENTENCE = 3

# Chunks cited per section: enough to give FaithfulnessChecker several claims to
# score without flooding its ten-claim ceiling from a single section.
_CHUNKS_PER_SECTION = 3


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
    useless as a regression signal.

    Each sentence is grounded in **one** chunk rather than in a pooled term list.
    That matters: pooling terms saturates the metric — every portfolio with a
    handful of chunks yields the same ratio of supported sentences, and a metric
    that is constant detects nothing. Grounding per chunk means a thin chunk
    yields a thin sentence, so the score tracks the quality of what retrieval
    actually returned. Each section closes with one recommendation that is not
    drawn from the context, keeping the score off the 1.0 ceiling.

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
        rotation = SECTION_NAMES.index(section_name) if section_name in SECTION_NAMES else 0
        evidence = self._section_evidence(context_chunks, rotation)

        if not evidence:
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

        opener = _SECTION_OPENERS.get(section_name, _DEFAULT_OPENER)
        username = str(profile_data.get("github_username", "") or "this candidate")

        sentences = [
            f"{opener} {' '.join(terms)} in the material retrieved for {section_name}."
            for terms in evidence
        ]
        sentences.append(
            f"Reviewers should ask {username} to make the strongest of these signals "
            "visible above the fold."
        )

        return FeedbackSection(
            section_name=section_name,
            content=" ".join(sentences),
            confidence=self._confidence(evidence),
            suggestions=[
                f"Expand the {section_name.replace('_', ' ')} narrative around {' '.join(terms)}."
                for terms in evidence
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
    def _confidence(evidence: list[list[str]]) -> float:
        """Derive a confidence score from how much evidence was quoted.

        Counting terms rather than sentences means a section grounded in one thin
        chunk reports lower confidence than one grounded in a dense chunk, which
        is the distinction a reader of the report cares about.

        Args:
            evidence: Per-sentence term lists

        Returns:
            Confidence between 0.0 and 0.9
        """
        term_count = sum(len(terms) for terms in evidence)
        return round(min(0.9, 0.5 + 0.05 * term_count), 2)

    @classmethod
    def _section_evidence(cls, chunks: list[dict], rotation: int) -> list[list[str]]:
        """Pick the evidence each sentence of one section will quote.

        One entry per sentence, each drawn from a single chunk. Sections start at
        different offsets into the ranked chunk list so the five sections do not
        collapse into five restatements of the top chunk. Chunks that yield no
        usable term produce no sentence at all, rather than a sentence with a
        hole in it.

        Args:
            chunks: Retrieved chunks
            rotation: Section index, used as the starting offset

        Returns:
            Up to _CHUNKS_PER_SECTION term lists, one per sentence
        """
        ranked = cls._rank_chunks(chunks)
        if not ranked:
            return []

        start = rotation % len(ranked)
        evidence = []
        for step in range(min(_CHUNKS_PER_SECTION, len(ranked))):
            chunk = ranked[(start + step) % len(ranked)]
            terms = cls._chunk_terms(chunk)[:_TERMS_PER_SENTENCE]
            if terms:
                evidence.append(terms)

        return evidence

    @staticmethod
    def _rank_chunks(chunks: list[dict]) -> list[dict]:
        """Order chunks by descending score, breaking ties on id.

        Sorting on a total order means the caller's iteration order — which
        HybridRetriever does not guarantee for equal scores — cannot change the
        generated text.

        Args:
            chunks: Retrieved chunks with 'score' and 'id' keys

        Returns:
            Chunks in stable ranked order
        """
        return sorted(
            chunks,
            key=lambda chunk: (-float(chunk.get("score", 0.0) or 0.0), str(chunk.get("id", ""))),
        )

    @staticmethod
    def _chunk_terms(chunk: dict) -> list[str]:
        """Extract quotable evidence terms from one chunk.

        Only tokens that are already alphanumeric survive: ``FaithfulnessChecker``
        compares raw whitespace tokens, so a term carrying attached punctuation
        ("python," from "Python, FastAPI") would never match the context it came
        from and would silently look unsupported.

        Args:
            chunk: A retrieved chunk

        Returns:
            Deduplicated lowercase terms in document order
        """
        terms: dict[str, None] = {}
        for raw_token in str(chunk.get("text", "")).split():
            token = raw_token.lower()
            if len(token) < _MIN_TERM_LENGTH or not token.isalnum():
                continue
            if token in _TERM_STOP_WORDS:
                continue
            terms[token] = None

        return list(terms)
