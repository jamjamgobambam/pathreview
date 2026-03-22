"""Evaluation suite for RAG system."""

from dataclasses import dataclass
import structlog

from .relevance_scorer import RelevanceScorer
from .faithfulness_checker import FaithfulnessChecker

logger = structlog.get_logger()


@dataclass
class EvalResult:
    """Result of evaluation."""
    relevance_score: float
    faithfulness_score: float
    overall_score: float


class EvalSuite:
    """Run evaluation on retrieval and generation."""

    def __init__(self):
        """Initialize evaluation suite."""
        self.relevance_scorer = RelevanceScorer()
        self.faithfulness_checker = FaithfulnessChecker()

    def run(self, query: str, chunks: list[dict], feedback: str) -> EvalResult:
        """Run full evaluation.

        Args:
            query: Query text
            chunks: Retrieved chunks
            feedback: Generated feedback

        Returns:
            EvalResult with all scores
        """
        # Score relevance of retrieval
        relevance = self.relevance_scorer.score(query, chunks)

        # Score faithfulness of feedback to chunks
        faithfulness = self.faithfulness_checker.check(feedback, chunks)

        # Overall score (average)
        overall = (relevance + faithfulness) / 2

        result = EvalResult(
            relevance_score=relevance,
            faithfulness_score=faithfulness,
            overall_score=overall
        )

        logger.info("eval_suite_complete", relevance=relevance,
                   faithfulness=faithfulness, overall=overall)

        return result
