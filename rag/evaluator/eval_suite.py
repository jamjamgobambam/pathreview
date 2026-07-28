"""Evaluation suite for RAG system."""

from dataclasses import dataclass
import structlog

from .relevance_scorer import RelevanceScorer
from .faithfulness_checker import FaithfulnessChecker
from .actionability_scorer import ActionabilityScorer

logger = structlog.get_logger()


@dataclass
class EvalResult:
    """Result of evaluation."""
    relevance_score: float
    faithfulness_score: float
    actionability_score: float
    overall_score: float


class EvalSuite:
    """Run evaluation on retrieval and generation."""

    def __init__(self):
        """Initialize evaluation suite."""
        self.relevance_scorer = RelevanceScorer()
        self.faithfulness_checker = FaithfulnessChecker()
        self.actionability_scorer = ActionabilityScorer()

    def run(self, query: str, chunks: list[dict], feedback: str) -> EvalResult:
        """Run full evaluation.

        Args:
            query: Query text
            chunks: Retrieved chunks
            feedback: Generated feedback

        Returns:
            EvalResult with all scores
        """
        relevance = self.relevance_scorer.score(query, chunks)
        faithfulness = self.faithfulness_checker.check(feedback, chunks)
        actionability = self.actionability_scorer.score(feedback)

        overall = (relevance + faithfulness + actionability) / 3

        result = EvalResult(
            relevance_score=relevance,
            faithfulness_score=faithfulness,
            actionability_score=actionability,
            overall_score=overall,
        )

        logger.info(
            "eval_suite_complete",
            relevance=relevance,
            faithfulness=faithfulness,
            actionability=actionability,
            overall=overall,
        )

        return result
