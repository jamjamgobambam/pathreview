"""Offline bias audit over stored reviews.

This module measures how the :class:`~safety.bias_detector.BiasDetector` behaves on
real review text. It is deliberately free of database and I/O concerns so the scoring
logic can be unit tested without a running Postgres; the command-line entry point that
samples the live database lives in ``scripts/audit_bias.py``.

The audit compares the detector's predictions against a labeled sample set and reports
false-positive / false-negative rates overall and broken down by demographic signal
(for example ``education``, ``age``, or ``origin``).
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from safety.bias_detector import BiasDetector

# A predictor takes review text and returns ``(is_biased, reason)`` — the same shape as
# ``BiasDetector.detect_bias``, so the detector can be swapped for a fake in tests.
Predictor = Callable[[str], tuple[bool, str]]

# Signal used when a labeled sample does not name a demographic signal.
UNSPECIFIED_SIGNAL = "unspecified"


@dataclass(frozen=True)
class LabeledSample:
    """A single labeled review snippet used as ground truth for the audit.

    Attributes:
        text: The review text to run through the detector.
        expected_biased: Whether a human labeled this text as biased.
        signal: The demographic signal this sample exercises (e.g. ``"education"``,
            ``"age"``, ``"origin"``, or ``"none"`` for clearly-neutral text).
        review_id: Optional identifier for tracing a sample back to its source.
    """

    text: str
    expected_biased: bool
    signal: str = UNSPECIFIED_SIGNAL
    review_id: str | None = None


@dataclass
class ConfusionMatrix:
    """Counts of detector outcomes against ground-truth labels."""

    true_positive: int = 0
    false_positive: int = 0
    true_negative: int = 0
    false_negative: int = 0

    @property
    def total(self) -> int:
        """Return the number of samples counted."""
        return self.true_positive + self.false_positive + self.true_negative + self.false_negative

    @property
    def flagged(self) -> int:
        """Number of samples the detector flagged — the denominator of precision."""
        return self.true_positive + self.false_positive

    @property
    def labeled_biased(self) -> int:
        """Number of samples labeled biased — the denominator of recall and the FN rate."""
        return self.true_positive + self.false_negative

    @property
    def labeled_neutral(self) -> int:
        """Number of samples labeled neutral — the denominator of the FP rate."""
        return self.false_positive + self.true_negative

    @property
    def precision(self) -> float | None:
        """Fraction of flagged samples that were truly biased, or ``None`` if nothing flagged."""
        return self.true_positive / self.flagged if self.flagged else None

    @property
    def recall(self) -> float | None:
        """Fraction of biased samples that were flagged, or ``None`` if none were biased."""
        return self.true_positive / self.labeled_biased if self.labeled_biased else None

    @property
    def false_positive_rate(self) -> float | None:
        """FP / (FP + TN) — how often neutral text is wrongly flagged."""
        return self.false_positive / self.labeled_neutral if self.labeled_neutral else None

    @property
    def false_negative_rate(self) -> float | None:
        """FN / (FN + TP) — how often biased text is missed."""
        return self.false_negative / self.labeled_biased if self.labeled_biased else None

    def record(self, expected_biased: bool, predicted_biased: bool) -> None:
        """Tally a single prediction against its label."""
        if expected_biased and predicted_biased:
            self.true_positive += 1
        elif expected_biased and not predicted_biased:
            self.false_negative += 1
        elif not expected_biased and predicted_biased:
            self.false_positive += 1
        else:
            self.true_negative += 1

    def to_dict(self) -> dict[str, Any]:
        """Serialize counts and derived rates to a JSON-friendly dict."""
        return {
            "counts": {
                "true_positive": self.true_positive,
                "false_positive": self.false_positive,
                "true_negative": self.true_negative,
                "false_negative": self.false_negative,
                "total": self.total,
            },
            "precision": self.precision,
            "recall": self.recall,
            "false_positive_rate": self.false_positive_rate,
            "false_negative_rate": self.false_negative_rate,
        }


@dataclass
class SampleResult:
    """The detector's outcome for one labeled sample, kept for spot-checking."""

    review_id: str | None
    signal: str
    expected_biased: bool
    predicted_biased: bool
    reason: str
    text_preview: str

    @property
    def outcome(self) -> str:
        """Return a short label: ``tp``, ``fp``, ``tn``, or ``fn``."""
        if self.expected_biased and self.predicted_biased:
            return "tp"
        if self.expected_biased and not self.predicted_biased:
            return "fn"
        if not self.expected_biased and self.predicted_biased:
            return "fp"
        return "tn"

    def to_dict(self) -> dict[str, Any]:
        """Serialize this result to a JSON-friendly dict."""
        return {
            "review_id": self.review_id,
            "signal": self.signal,
            "expected_biased": self.expected_biased,
            "predicted_biased": self.predicted_biased,
            "outcome": self.outcome,
            "reason": self.reason,
            "text_preview": self.text_preview,
        }


@dataclass
class AuditReport:
    """Aggregate audit results: overall and per-signal confusion matrices plus detail."""

    overall: ConfusionMatrix
    by_signal: dict[str, ConfusionMatrix]
    results: list[SampleResult] = field(default_factory=list)
    skipped_empty: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize the full report to a JSON-friendly dict."""
        return {
            "sample_count": self.overall.total,
            "skipped_empty": self.skipped_empty,
            "overall": self.overall.to_dict(),
            "by_signal": {
                signal: matrix.to_dict() for signal, matrix in sorted(self.by_signal.items())
            },
            "results": [result.to_dict() for result in self.results],
        }


def extract_review_text(sections: Any) -> str:
    """Flatten a review's ``sections`` JSON into a single auditable string.

    A review's ``sections`` field is a list of section dicts, each optionally carrying
    ``content`` text and a ``suggestions`` list. This joins all of that text so the
    detector sees everything a candidate would read.

    Args:
        sections: The ``sections`` value from a review. May be ``None`` (e.g. a failed
            review) or malformed; those yield an empty string rather than raising.

    Returns:
        The concatenated review text, or an empty string when nothing is extractable.
    """
    if not isinstance(sections, Sequence) or isinstance(sections, str | bytes):
        return ""

    parts: list[str] = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        content = section.get("content")
        if isinstance(content, str) and content.strip():
            parts.append(content.strip())
        suggestions = section.get("suggestions")
        if isinstance(suggestions, list):
            parts.extend(s.strip() for s in suggestions if isinstance(s, str) and s.strip())

    return "\n".join(parts)


def audit_samples(
    samples: Iterable[LabeledSample],
    predictor: Predictor | None = None,
    *,
    preview_chars: int = 100,
) -> AuditReport:
    """Run the detector over labeled samples and build a confusion-matrix report.

    Args:
        samples: The labeled samples to score.
        predictor: A ``(text) -> (is_biased, reason)`` callable. Defaults to
            :meth:`safety.bias_detector.BiasDetector.detect_bias`.
        preview_chars: How many characters of each sample to keep in the detail output.

    Returns:
        An :class:`AuditReport` with overall and per-signal matrices and per-sample detail.
        Samples whose text is empty or whitespace-only are skipped and counted separately.
    """
    predict = predictor or BiasDetector.detect_bias

    overall = ConfusionMatrix()
    by_signal: dict[str, ConfusionMatrix] = defaultdict(ConfusionMatrix)
    results: list[SampleResult] = []
    skipped_empty = 0

    for sample in samples:
        if not sample.text or not sample.text.strip():
            skipped_empty += 1
            continue

        predicted_biased, reason = predict(sample.text)
        signal = sample.signal or UNSPECIFIED_SIGNAL

        overall.record(sample.expected_biased, predicted_biased)
        by_signal[signal].record(sample.expected_biased, predicted_biased)
        results.append(
            SampleResult(
                review_id=sample.review_id,
                signal=signal,
                expected_biased=sample.expected_biased,
                predicted_biased=predicted_biased,
                reason=reason,
                text_preview=sample.text[:preview_chars],
            )
        )

    return AuditReport(
        overall=overall,
        by_signal=dict(by_signal),
        results=results,
        skipped_empty=skipped_empty,
    )


def load_labeled_samples(path: str | Path) -> list[LabeledSample]:
    """Load labeled samples from a JSON file.

    The file must contain a list of objects with ``text`` and ``expected_biased`` keys
    and optional ``signal`` and ``review_id`` keys.

    Args:
        path: Path to the labeled-sample JSON file.

    Returns:
        The parsed labeled samples.

    Raises:
        ValueError: If the file's top level is not a list, or an entry is missing a
            required field.
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"Expected a JSON list of samples, got {type(raw).__name__}")

    samples: list[LabeledSample] = []
    for index, entry in enumerate(raw):
        if not isinstance(entry, dict) or "text" not in entry or "expected_biased" not in entry:
            raise ValueError(f"Sample at index {index} is missing 'text' or 'expected_biased'")
        samples.append(
            LabeledSample(
                text=str(entry["text"]),
                expected_biased=bool(entry["expected_biased"]),
                signal=str(entry.get("signal", UNSPECIFIED_SIGNAL)),
                review_id=entry.get("review_id"),
            )
        )
    return samples


def _format_rate(value: float | None, numerator: int, denominator: int) -> str:
    """Render a rate as a percentage followed by the counts behind it.

    The counts matter as much as the percentage here: a sample set this small can
    produce a headline like ``50.0%`` off two samples, and a maintainer tuning
    thresholds needs to see that it is ``1/2`` and not read false precision into it.

    Args:
        value: The rate, or ``None`` when its denominator is zero.
        numerator: The count on top of the rate.
        denominator: The count underneath it.

    Returns:
        A string like ``"50.0% (1/2)"``, or ``"n/a (0/0)"`` when the rate is undefined.
    """
    if value is None:
        return f"n/a ({numerator}/{denominator})"
    return f"{value * 100:.1f}% ({numerator}/{denominator})"


def format_report_text(report: AuditReport) -> str:
    """Render a human-readable summary of an audit report.

    Args:
        report: The report to format.

    Returns:
        A multi-line string suitable for printing to a console.
    """
    lines = ["Bias audit report", "=" * 60]
    lines.append(f"Samples scored : {report.overall.total}")
    lines.append(f"Skipped (empty): {report.skipped_empty}")
    lines.append("")

    def _matrix_lines(title: str, matrix: ConfusionMatrix) -> list[str]:
        precision = _format_rate(matrix.precision, matrix.true_positive, matrix.flagged)
        recall = _format_rate(matrix.recall, matrix.true_positive, matrix.labeled_biased)
        fp_rate = _format_rate(
            matrix.false_positive_rate, matrix.false_positive, matrix.labeled_neutral
        )
        fn_rate = _format_rate(
            matrix.false_negative_rate, matrix.false_negative, matrix.labeled_biased
        )
        return [
            title,
            f"  TP={matrix.true_positive} FP={matrix.false_positive} "
            f"TN={matrix.true_negative} FN={matrix.false_negative}",
            f"  precision={precision} recall={recall}",
            f"  false_positive_rate={fp_rate} false_negative_rate={fn_rate}",
        ]

    lines.extend(_matrix_lines("Overall", report.overall))
    lines.append("")
    lines.append("By demographic signal")
    lines.append("-" * 60)
    if report.by_signal:
        for signal, matrix in sorted(report.by_signal.items()):
            lines.extend(_matrix_lines(f"[{signal}] (n={matrix.total})", matrix))
    else:
        lines.append("  (no samples)")

    return "\n".join(lines)
