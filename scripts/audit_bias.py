"""Run an offline bias audit over stored portfolio reviews."""

import argparse
import asyncio
import json
from collections.abc import Sequence
from pathlib import Path
from typing import TypedDict, cast

from sqlalchemy import func, select

from core.database import AsyncSessionLocal
from core.logging import configure_logging, get_logger
from core.models.review import Review
from safety.bias_detector import BiasDetector

SAMPLE_SIZE = 100
VALID_DEMOGRAPHIC_SIGNALS = frozenset(
    {
        "age",
        "education_background",
        "socioeconomic_background",
        "immigration_status",
        "none",
    }
)
REPORT_PATH = Path(__file__).resolve().parents[1] / "bias_audit_report.json"
EVALUATED_REPORT_PATH = Path(__file__).resolve().parents[1] / "bias_audit_evaluated.json"
logger = get_logger(__name__)


class AuditResult(TypedDict):
    """One review's bias detection result."""

    review_id: str
    review_text: str
    predicted_biased: bool
    reason: str
    expected_biased: bool | None
    demographic_signal: str | None


class AuditMetrics(TypedDict):
    """Metric fields that require human-reviewed ground-truth labels."""

    status: str
    reason: str
    false_positive_rate_by_demographic_signal: dict[str, float | None]
    false_negative_rate_by_demographic_signal: dict[str, float | None]


class AuditReport(TypedDict):
    """Serialized output from one audit run."""

    sampled_count: int
    checked_count: int
    skipped_count: int
    detected_bias_count: int
    metrics: AuditMetrics
    results: list[AuditResult]


def extract_review_text(review: Review) -> str:
    """Combine the review's written feedback into one auditable text value."""
    if not isinstance(review.sections, list):
        return ""

    text_parts: list[str] = []
    for section in review.sections:
        if not isinstance(section, dict):
            continue

        content = section.get("content")
        if isinstance(content, str) and content.strip():
            text_parts.append(content.strip())

        suggestions = section.get("suggestions")
        if isinstance(suggestions, list):
            text_parts.extend(
                suggestion.strip()
                for suggestion in suggestions
                if isinstance(suggestion, str) and suggestion.strip()
            )

    return "\n".join(text_parts)


def audit_reviews(reviews: Sequence[Review]) -> list[AuditResult]:
    """Run the existing bias detector once for each nonempty review."""
    results: list[AuditResult] = []

    for review in reviews:
        review_text = extract_review_text(review)
        if not review_text:
            logger.info("bias_audit_review_skipped", review_id=str(review.id))
            continue

        predicted_biased, reason = BiasDetector.detect_bias(review_text)
        logger.info(
            "bias_audit_review_checked",
            review_id=str(review.id),
            predicted_biased=predicted_biased,
            reason=reason or None,
        )
        results.append(
            {
                "review_id": str(review.id),
                "review_text": review_text,
                "predicted_biased": predicted_biased,
                "reason": reason,
                "expected_biased": None,
                "demographic_signal": None,
            }
        )

    return results


def write_report(
    sampled_count: int,
    results: list[AuditResult],
    output_path: Path = REPORT_PATH,
) -> Path:
    """Write the audit results and current metric availability to JSON."""
    report: AuditReport = {
        "sampled_count": sampled_count,
        "checked_count": len(results),
        "skipped_count": sampled_count - len(results),
        "detected_bias_count": sum(result["predicted_biased"] for result in results),
        "metrics": {
            "status": "unavailable",
            "reason": (
                "Ground-truth annotations are required to calculate false "
                "positive and false negative rates by demographic signal."
            ),
            "false_positive_rate_by_demographic_signal": {},
            "false_negative_rate_by_demographic_signal": {},
        },
        "results": results,
    }
    output_path.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    logger.info("bias_audit_report_written", path=str(output_path))
    return output_path


def load_report(input_path: Path) -> AuditReport:
    """Load and validate an editable audit report."""
    data = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        raise ValueError("Audit report must contain a results list.")

    for entry in data["results"]:
        if not isinstance(entry, dict):
            raise ValueError("Each audit result must be a JSON object.")

        review_id = entry.get("review_id")
        if not isinstance(review_id, str):
            raise ValueError("Each audit result must contain a review_id.")
        if not isinstance(entry.get("predicted_biased"), bool):
            raise ValueError(f"Review {review_id} must contain a Boolean predicted_biased value.")

        expected_biased = entry.get("expected_biased")
        demographic_signal = entry.get("demographic_signal")
        if expected_biased is not None and not isinstance(expected_biased, bool):
            raise ValueError(f"Review {review_id} expected_biased must be true, false, or null.")
        if demographic_signal is not None and not isinstance(demographic_signal, str):
            raise ValueError(f"Review {review_id} demographic_signal must be text or null.")
        if (expected_biased is None) != (demographic_signal is None):
            raise ValueError(
                f"Review {review_id} must set both expected_biased and "
                "demographic_signal, or leave both null."
            )
        if isinstance(demographic_signal, str) and not demographic_signal.strip():
            raise ValueError(f"Review {review_id} demographic_signal cannot be blank.")
        if isinstance(demographic_signal, str):
            signal = demographic_signal.strip()
            if signal not in VALID_DEMOGRAPHIC_SIGNALS:
                valid_signals = ", ".join(sorted(VALID_DEMOGRAPHIC_SIGNALS))
                raise ValueError(
                    f"Review {review_id} demographic_signal must be one of: {valid_signals}."
                )
            entry["demographic_signal"] = signal

    return cast("AuditReport", data)


def calculate_metrics(results: Sequence[AuditResult]) -> AuditMetrics:
    """Calculate error rates for each human-labeled demographic signal."""
    labeled_by_signal: dict[str, list[AuditResult]] = {}
    for result in results:
        expected_biased = result["expected_biased"]
        demographic_signal = result["demographic_signal"]
        if expected_biased is None or demographic_signal is None:
            continue

        signal = demographic_signal.strip()
        labeled_by_signal.setdefault(signal, []).append(result)

    if not labeled_by_signal:
        return {
            "status": "unavailable",
            "reason": (
                "No complete human labels were found. Set expected_biased and "
                "demographic_signal in the audit report."
            ),
            "false_positive_rate_by_demographic_signal": {},
            "false_negative_rate_by_demographic_signal": {},
        }

    false_positive_rates: dict[str, float | None] = {}
    false_negative_rates: dict[str, float | None] = {}
    for signal, signal_results in labeled_by_signal.items():
        actual_negative_count = sum(not result["expected_biased"] for result in signal_results)
        actual_positive_count = sum(bool(result["expected_biased"]) for result in signal_results)
        false_positive_count = sum(
            result["predicted_biased"] and not result["expected_biased"]
            for result in signal_results
        )
        false_negative_count = sum(
            not result["predicted_biased"] and bool(result["expected_biased"])
            for result in signal_results
        )

        false_positive_rates[signal] = (
            false_positive_count / actual_negative_count if actual_negative_count else None
        )
        false_negative_rates[signal] = (
            false_negative_count / actual_positive_count if actual_positive_count else None
        )

    return {
        "status": "available",
        "reason": (
            "A rate is null when its demographic signal has no examples for "
            "the required denominator."
        ),
        "false_positive_rate_by_demographic_signal": false_positive_rates,
        "false_negative_rate_by_demographic_signal": false_negative_rates,
    }


def evaluate_report(
    input_path: Path,
    output_path: Path = EVALUATED_REPORT_PATH,
) -> Path:
    """Calculate metrics from an edited report and write the evaluated report."""
    report = load_report(input_path)
    report["metrics"] = calculate_metrics(report["results"])
    output_path.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    logger.info(
        "bias_audit_evaluation_written",
        input_path=str(input_path),
        output_path=str(output_path),
    )
    return output_path


async def load_reviews() -> list[Review]:
    """Load a random sample of completed reviews with stored sections.

    Returns:
        Up to 100 eligible reviews.
    """
    statement = (
        select(Review)
        .where(Review.status == "complete", Review.sections.is_not(None))
        .order_by(func.random())
        .limit(SAMPLE_SIZE)
    )

    async with AsyncSessionLocal() as session:
        result = await session.execute(statement)
        return list(result.scalars().all())


async def run_audit() -> list[AuditResult]:
    """Load eligible reviews, audit them, and log a summary."""
    logger.info("bias_audit_started", sample_limit=SAMPLE_SIZE)
    reviews = await load_reviews()
    results = audit_reviews(reviews)
    write_report(len(reviews), results)

    logger.info(
        "bias_audit_completed",
        sampled_count=len(reviews),
        checked_count=len(results),
        skipped_count=len(reviews) - len(results),
        detected_bias_count=sum(result["predicted_biased"] for result in results),
    )
    return results


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse audit generation or evaluation arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--evaluate",
        type=Path,
        metavar="REPORT_PATH",
        help="Evaluate human labels in an existing bias audit report.",
    )
    return parser.parse_args(argv)


def main() -> None:
    """Run a new audit or evaluate an edited audit report."""
    configure_logging()
    args = parse_args()
    if args.evaluate:
        evaluate_report(args.evaluate)
        return

    asyncio.run(run_audit())


if __name__ == "__main__":
    main()
