"""Tests for the offline bias audit workflow."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from core.models.review import Review
from scripts.audit_bias import (
    AuditResult,
    evaluate_report,
    extract_review_text,
    load_report,
    write_report,
)

pytestmark = pytest.mark.unit


def _result(review_id: str, predicted_biased: bool) -> AuditResult:
    return {
        "review_id": review_id,
        "review_text": "Review feedback",
        "predicted_biased": predicted_biased,
        "reason": "",
        "expected_biased": None,
        "demographic_signal": None,
    }


def test_extract_review_text_combines_content_and_suggestions() -> None:
    review = Review(
        id="review-1",
        profile_id="profile-1",
        status="complete",
        sections=[
            {
                "section_name": "Technical Skills",
                "content": "Clear feedback",
                "suggestions": ["Add tests", "Document behavior"],
            }
        ],
    )

    assert extract_review_text(review) == "Clear feedback\nAdd tests\nDocument behavior"


def test_labeled_report_produces_evaluated_metrics() -> None:
    with TemporaryDirectory() as temp_dir:
        report_path = Path(temp_dir) / "bias_audit_report.json"
        evaluated_path = Path(temp_dir) / "bias_audit_evaluated.json"
        write_report(
            3,
            [_result("review-1", True), _result("review-2", False), _result("review-3", False)],
            report_path,
        )

        report = json.loads(report_path.read_text(encoding="utf-8"))
        labels = [
            (False, "education_background"),
            (True, "age"),
            (False, "none"),
        ]
        for result, (expected_biased, signal) in zip(report["results"], labels, strict=True):
            result["expected_biased"] = expected_biased
            result["demographic_signal"] = signal
        report_path.write_text(json.dumps(report), encoding="utf-8")

        evaluate_report(report_path, evaluated_path)
        metrics = json.loads(evaluated_path.read_text(encoding="utf-8"))["metrics"]

        assert metrics["false_positive_rate_by_demographic_signal"] == {
            "education_background": 1.0,
            "age": None,
            "none": 0.0,
        }
        assert metrics["false_negative_rate_by_demographic_signal"] == {
            "education_background": None,
            "age": 1.0,
            "none": None,
        }

    assert not report_path.exists()
    assert not evaluated_path.exists()


def test_load_report_rejects_unknown_demographic_signal() -> None:
    with TemporaryDirectory() as temp_dir:
        report_path = Path(temp_dir) / "bias_audit_report.json"
        write_report(1, [_result("review-1", False)], report_path)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["results"][0]["expected_biased"] = False
        report["results"][0]["demographic_signal"] = "Age"
        report_path.write_text(json.dumps(report), encoding="utf-8")

        with pytest.raises(ValueError, match="must be one of"):
            load_report(report_path)
