"""
scripts/audit_bias.py — PathReview

Offline bias audit script: samples up to 100 stored reviews from the database,
runs each through BiasDetector, and produces a report showing flag rates by
demographic signal type.

Issue #72: https://github.com/ascherj/pathreview/issues/72

Usage:
    python scripts/audit_bias.py
    python scripts/audit_bias.py --limit 50
    python scripts/audit_bias.py --output scripts/audit_report.json

The script requires a running database (docker compose up -d) and a valid
DATABASE_URL in .env.
"""

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import structlog
from sqlalchemy import func, select

# Add project root to path so imports work when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import AsyncSessionLocal  # noqa: E402
from core.logging import configure_logging  # noqa: E402
from core.models.review import Review  # noqa: E402
from safety.bias_detector import BiasDetector  # noqa: E402

logger = structlog.get_logger()

# Synthetic test fixtures to verify the detector is working.
# Excluded from flag rate calculations.
SYNTHETIC_FIXTURES: list[dict] = [
    {
        "id": "SYNTHETIC-001",
        "text": "bootcamp training is inadequate for professional development",
        "expected_biased": True,
        "label": "dismissive_education",
    },
    {
        "id": "SYNTHETIC-002",
        "text": "immigrant developers can't communicate effectively in code reviews",
        "expected_biased": True,
        "label": "demographic_assumption",
    },
    {
        "id": "SYNTHETIC-003",
        "text": "Your Python skills are strong and your projects show solid fundamentals.",
        "expected_biased": False,
        "label": "clean_feedback",
    },
]


def extract_text_from_review(review: Review) -> str:
    """
    Extract a single text blob from a review's sections field.

    Args:
        review: Review model instance with sections JSON.

    Returns:
        Concatenated text from all section content and suggestions.
        Empty string if sections is None or malformed.
    """
    if not review.sections:
        return ""

    parts: list[str] = []
    try:
        for section in review.sections:
            if not isinstance(section, dict):
                continue
            content = section.get("content", "")
            if content and isinstance(content, str):
                parts.append(content)
            suggestions = section.get("suggestions", [])
            if isinstance(suggestions, list):
                for s in suggestions:
                    if s and isinstance(s, str):
                        parts.append(s)
    except (TypeError, AttributeError) as exc:
        logger.warning("review_text_extraction_failed", error=str(exc))
        return ""

    return " ".join(parts)


def run_synthetic_validation() -> dict:
    """
    Run BiasDetector against synthetic fixtures to verify it is working.

    Returns:
        Dict with validation results and pass/fail status.
    """
    results = []
    all_passed = True

    for fixture in SYNTHETIC_FIXTURES:
        text = fixture["text"]
        assert isinstance(text, str)
        is_biased, reason = BiasDetector.detect_bias(text)
        passed = is_biased == fixture["expected_biased"]
        if not passed:
            all_passed = False

        result = {
            "fixture_id": fixture["id"],
            "label": fixture["label"],
            "expected_biased": fixture["expected_biased"],
            "actual_biased": is_biased,
            "reason": reason,
            "passed": passed,
        }
        results.append(result)

        logger.info(
            "synthetic_fixture_result",
            fixture_id=fixture["id"],
            expected=fixture["expected_biased"],
            actual=is_biased,
            passed=passed,
        )

    return {"all_passed": all_passed, "fixtures": results}


async def sample_reviews(limit: int = 100) -> list[Review]:
    """
    Sample up to `limit` completed reviews from the database.

    Args:
        limit: Maximum number of reviews to sample.

    Returns:
        List of Review instances with status='complete'.
    """
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Review).where(Review.status == "complete").order_by(func.random()).limit(limit)
        )
        result = await session.execute(stmt)
        reviews = result.scalars().all()
        logger.info("reviews_sampled", count=len(reviews), limit=limit)
        return list(reviews)


def audit_reviews(reviews: list[Review]) -> list[dict]:
    """
    Run BiasDetector on each review and return per-review results.

    Args:
        reviews: List of Review instances to audit.

    Returns:
        List of audit result dicts.
    """
    results: list[dict] = []

    for review in reviews:
        text = extract_text_from_review(review)

        if not text.strip():
            logger.warning(
                "review_skipped_empty_text",
                review_id=str(review.id),
            )
            results.append(
                {
                    "review_id": str(review.id),
                    "skipped": True,
                    "skip_reason": "empty_text",
                    "is_biased": None,
                    "reason": None,
                    "signal_category": None,
                }
            )
            continue

        try:
            is_biased, reason = BiasDetector.detect_bias(text)
        except Exception as exc:
            logger.error(
                "bias_detection_error",
                review_id=str(review.id),
                error=str(exc),
            )
            results.append(
                {
                    "review_id": str(review.id),
                    "skipped": True,
                    "skip_reason": "detection_error",
                    "is_biased": None,
                    "reason": None,
                    "signal_category": None,
                }
            )
            continue

        # Categorize the signal type based on the reason string
        signal_category = None
        if is_biased:
            if "educational" in reason.lower() or "dismissive" in reason.lower():
                signal_category = "dismissive_education"
            elif "demographic" in reason.lower():
                signal_category = "demographic_assumption"
            else:
                signal_category = "other"

        logger.info(
            "review_audited",
            review_id=str(review.id),
            is_biased=is_biased,
            signal_category=signal_category,
        )

        results.append(
            {
                "review_id": str(review.id),
                "skipped": False,
                "skip_reason": None,
                "is_biased": is_biased,
                "reason": reason,
                "signal_category": signal_category,
            }
        )

    return results


def compute_report(audit_results: list[dict], synthetic_validation: dict) -> dict:
    """
    Compute summary statistics from audit results.

    Note on false positive / negative rates: without ground-truth labels on
    stored reviews, we cannot compute true false positive / negative rates.
    This report shows flag rates as a proxy for auditing detector behavior.

    Args:
        audit_results: Per-review audit results from audit_reviews().
        synthetic_validation: Validation results from run_synthetic_validation().

    Returns:
        Summary report dict.
    """
    evaluated = [r for r in audit_results if not r["skipped"]]
    skipped = [r for r in audit_results if r["skipped"]]
    flagged = [r for r in evaluated if r["is_biased"]]

    dismissive = [r for r in flagged if r["signal_category"] == "dismissive_education"]
    demographic = [r for r in flagged if r["signal_category"] == "demographic_assumption"]
    other = [r for r in flagged if r["signal_category"] == "other"]

    total_evaluated = len(evaluated)
    total_flagged = len(flagged)
    flag_rate = total_flagged / total_evaluated if total_evaluated > 0 else 0.0

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "sample_size": len(audit_results),
        "evaluated": total_evaluated,
        "skipped": len(skipped),
        "total_flagged": total_flagged,
        "flag_rate": round(flag_rate, 4),
        "by_signal": {
            "dismissive_education": {
                "count": len(dismissive),
                "rate": (
                    round(len(dismissive) / total_evaluated, 4) if total_evaluated > 0 else 0.0
                ),
            },
            "demographic_assumption": {
                "count": len(demographic),
                "rate": (
                    round(len(demographic) / total_evaluated, 4) if total_evaluated > 0 else 0.0
                ),
            },
            "other": {
                "count": len(other),
                "rate": (round(len(other) / total_evaluated, 4) if total_evaluated > 0 else 0.0),
            },
        },
        "note": (
            "Flag rates are computed without ground-truth labels. "
            "True false positive/negative rates require human-labeled data."
        ),
        "synthetic_validation": synthetic_validation,
        "flagged_reviews": [
            {
                "review_id": r["review_id"],
                "signal_category": r["signal_category"],
                "reason": r["reason"],
            }
            for r in flagged
        ],
    }


def print_report(report: dict) -> None:
    """Print a human-readable summary of the audit report."""
    print("\n" + "=" * 60)
    print("BIAS AUDIT REPORT — PathReview")
    print("=" * 60)
    print(f"Generated at : {report['generated_at']}")
    print(f"Sample size  : {report['sample_size']} reviews")
    print(f"Evaluated    : {report['evaluated']} (skipped: {report['skipped']})")
    print()
    print(f"Total flagged: {report['total_flagged']} ({report['flag_rate']:.1%} flag rate)")
    print()
    print("By signal type:")
    for signal, stats in report["by_signal"].items():
        print(f"  {signal:<30} {stats['count']:>4} flagged  ({stats['rate']:.1%})")
    print()
    val = report["synthetic_validation"]
    status = "PASS" if val["all_passed"] else "FAIL"
    print(f"Synthetic validation: {status}")
    for fixture in val["fixtures"]:
        icon = "PASS" if fixture["passed"] else "FAIL"
        print(f"  [{icon}] {fixture['fixture_id']} ({fixture['label']})")
    print()
    print(report["note"])
    print("=" * 60)


async def main(limit: int = 100, output: str | None = None) -> None:
    """
    Main entry point for the bias audit script.

    Args:
        limit: Maximum number of reviews to sample.
        output: Optional path to write JSON report.
    """
    configure_logging()
    logger.info("bias_audit_started", limit=limit)

    # Step 1: Validate detector works with synthetic fixtures
    logger.info("running_synthetic_validation")
    synthetic_validation = run_synthetic_validation()
    if not synthetic_validation["all_passed"]:
        logger.warning(
            "synthetic_validation_failed",
            detail=(
                "Some fixtures did not match expected results. "
                "Detector patterns may be too narrow."
            ),
        )

    # Step 2: Sample reviews from DB
    reviews = await sample_reviews(limit=limit)

    if not reviews:
        logger.warning("no_reviews_found", detail="No completed reviews in database.")
        print("\nNo completed reviews found in the database.")
        print("Run 'make reset-db' to seed sample data, then try again.")
        return

    # Step 3: Run bias detector on each review
    logger.info("auditing_reviews", count=len(reviews))
    audit_results = audit_reviews(reviews)

    # Step 4: Compute report
    report = compute_report(audit_results, synthetic_validation)

    # Step 5: Print report
    print_report(report)

    # Step 6: Optionally write JSON report
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info("report_written", path=str(output_path))
        print(f"\nJSON report written to: {output_path}")

    logger.info(
        "bias_audit_completed",
        flagged=report["total_flagged"],
        total=report["evaluated"],
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run bias audit on stored PathReview reviews.")
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of reviews to sample (default: 100)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to write JSON report (optional)",
    )
    args = parser.parse_args()
    asyncio.run(main(limit=args.limit, output=args.output))
