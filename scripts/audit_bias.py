"""Offline bias audit over a sample of stored reviews.

Runs the ``safety.bias_detector.BiasDetector`` over a labeled sample set and reports
false-positive / false-negative rates overall and by demographic signal, so maintainers
have reproducible evidence of the detector's real-world behavior instead of guesswork.

Usage::

    # Score the detector against the labeled fixture set (no database needed)
    python scripts/audit_bias.py

    # Also scan up to 100 real stored reviews for the detector's flag rate
    python scripts/audit_bias.py --scan-db --sample-size 100

The ground-truth accuracy numbers come from the labeled sample file, because stored
reviews are unlabeled — the ``--scan-db`` pass reports only how often the detector fires
on real data, which is still useful for spotting drift. See ``PLAN.md`` for the rationale.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from core.logging import configure_logging, get_logger
from safety.bias_audit import (
    AuditReport,
    LabeledSample,
    audit_samples,
    extract_review_text,
    format_report_text,
    load_labeled_samples,
)
from safety.bias_detector import BiasDetector

logger = get_logger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SAMPLES = REPO_ROOT / "tests" / "fixtures" / "bias_audit_samples.json"
DEFAULT_OUTPUT = REPO_ROOT / "bias_audit_report.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the audit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--samples",
        type=Path,
        default=DEFAULT_SAMPLES,
        help=f"Labeled sample JSON file (default: {DEFAULT_SAMPLES}).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Where to write the JSON report (default: {DEFAULT_OUTPUT}).",
    )
    parser.add_argument(
        "--scan-db",
        action="store_true",
        help="Additionally scan stored reviews for the detector's live flag rate.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=100,
        help="Max number of stored reviews to scan when --scan-db is set (default: 100).",
    )
    return parser.parse_args(argv)


def log_sample_results(report: AuditReport) -> None:
    """Emit per-sample detail so misfires are visible in the logs."""
    for result in report.results:
        if result.outcome in ("fp", "fn"):
            logger.warning(
                "bias_audit_misfire",
                outcome=result.outcome,
                signal=result.signal,
                review_id=result.review_id,
                reason=result.reason,
                text_preview=result.text_preview,
            )
        else:
            logger.info(
                "bias_audit_sample",
                outcome=result.outcome,
                signal=result.signal,
                review_id=result.review_id,
            )


async def scan_stored_reviews(sample_size: int) -> dict[str, int] | None:
    """Run the detector over stored reviews and count how often it fires.

    Stored reviews are unlabeled, so this reports only a flag rate — not accuracy.
    Returns ``None`` when the database cannot be reached, so the audit still succeeds
    on machines without a running Postgres.

    Args:
        sample_size: Maximum number of most-recent reviews to scan.

    Returns:
        A dict with ``scanned`` and ``flagged`` counts, or ``None`` if the DB is unavailable.
    """
    try:
        from sqlalchemy import select

        from core.database import AsyncSessionLocal
        from core.models.review import Review
    except Exception as exc:  # pragma: no cover - import/config guard
        logger.warning("bias_audit_db_unavailable", error=str(exc))
        return None

    try:
        async with AsyncSessionLocal() as session:
            stmt = select(Review).order_by(Review.created_at.desc()).limit(sample_size)
            reviews = (await session.execute(stmt)).scalars().all()
    except Exception as exc:
        logger.warning("bias_audit_db_query_failed", error=str(exc))
        return None

    scanned = 0
    flagged = 0
    for review in reviews:
        text = extract_review_text(review.sections)
        if not text.strip():
            continue
        scanned += 1
        is_biased, reason = BiasDetector.detect_bias(text)
        if is_biased:
            flagged += 1
            logger.warning(
                "bias_audit_stored_review_flagged",
                review_id=review.id,
                reason=reason,
            )

    logger.info("bias_audit_db_scan_complete", scanned=scanned, flagged=flagged)
    return {"scanned": scanned, "flagged": flagged}


def run_audit(args: argparse.Namespace) -> int:
    """Execute the audit and write the report. Returns a process exit code."""
    configure_logging()

    try:
        samples: list[LabeledSample] = load_labeled_samples(args.samples)
    except (OSError, ValueError) as exc:
        logger.error("bias_audit_samples_failed", error=str(exc), path=str(args.samples))
        print(f"Could not load labeled samples: {exc}")
        return 1

    if not samples:
        logger.error("bias_audit_no_samples", path=str(args.samples))
        print("No labeled samples found; nothing to audit.")
        return 1

    report = audit_samples(samples)
    log_sample_results(report)

    report_dict = report.to_dict()
    if args.scan_db:
        db_scan = asyncio.run(scan_stored_reviews(args.sample_size))
        report_dict["stored_review_scan"] = db_scan

    args.output.write_text(json.dumps(report_dict, indent=2), encoding="utf-8")

    print(format_report_text(report))
    if args.scan_db:
        scan = report_dict.get("stored_review_scan")
        print("")
        if scan is None:
            print("Stored-review scan: skipped (database unavailable).")
        else:
            print(f"Stored-review scan: {scan['flagged']}/{scan['scanned']} reviews flagged.")
    print(f"\nJSON report written to {args.output}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point for the bias audit script."""
    return run_audit(parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
