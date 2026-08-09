"""Tests for scripts/audit_bias.py"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.audit_bias import (
    audit_reviews,
    compute_report,
    extract_text_from_review,
    run_synthetic_validation,
)


def make_review(review_id: str, sections: list | None) -> MagicMock:
    """Helper to create a mock Review with the given sections."""
    review = MagicMock()
    review.id = review_id
    review.sections = sections
    return review


@pytest.mark.unit
class TestExtractTextFromReview:
    """Tests for extract_text_from_review()."""

    def test_returns_empty_string_for_none_sections(self) -> None:
        review = make_review("r1", None)
        assert extract_text_from_review(review) == ""

    def test_returns_empty_string_for_empty_sections(self) -> None:
        review = make_review("r1", [])
        assert extract_text_from_review(review) == ""

    def test_extracts_content_from_sections(self) -> None:
        review = make_review(
            "r1",
            [
                {
                    "section_name": "Skills",
                    "content": "Strong Python skills.",
                    "suggestions": [],
                }
            ],
        )
        result = extract_text_from_review(review)
        assert "Strong Python skills." in result

    def test_extracts_suggestions_from_sections(self) -> None:
        review = make_review(
            "r1",
            [
                {
                    "section_name": "Skills",
                    "content": "Good skills.",
                    "suggestions": ["Add more projects.", "Learn Kubernetes."],
                }
            ],
        )
        result = extract_text_from_review(review)
        assert "Add more projects." in result
        assert "Learn Kubernetes." in result

    def test_handles_missing_content_key(self) -> None:
        review = make_review("r1", [{"section_name": "Skills", "suggestions": []}])
        result = extract_text_from_review(review)
        assert result == ""

    def test_handles_none_content_value(self) -> None:
        review = make_review(
            "r1",
            [{"section_name": "Skills", "content": None, "suggestions": []}],
        )
        result = extract_text_from_review(review)
        assert result == ""

    def test_handles_multiple_sections(self) -> None:
        review = make_review(
            "r1",
            [
                {"section_name": "Skills", "content": "Python expert.", "suggestions": []},
                {"section_name": "Projects", "content": "Good projects.", "suggestions": []},
            ],
        )
        result = extract_text_from_review(review)
        assert "Python expert." in result
        assert "Good projects." in result

    def test_handles_malformed_section(self) -> None:
        """Non-dict section entries are skipped without crashing."""
        review = make_review("r1", ["not a dict", None, 42])
        result = extract_text_from_review(review)
        assert result == ""


@pytest.mark.unit
class TestRunSyntheticValidation:
    """Tests for run_synthetic_validation()."""

    def test_returns_dict_with_all_passed_and_fixtures(self) -> None:
        result = run_synthetic_validation()
        assert "all_passed" in result
        assert "fixtures" in result
        assert isinstance(result["fixtures"], list)

    def test_fixtures_have_required_fields(self) -> None:
        result = run_synthetic_validation()
        for fixture in result["fixtures"]:
            assert "fixture_id" in fixture
            assert "passed" in fixture
            assert "actual_biased" in fixture
            assert "expected_biased" in fixture

    def test_synthetic_001_is_detected_as_biased(self) -> None:
        result = run_synthetic_validation()
        fixture_001 = next(f for f in result["fixtures"] if f["fixture_id"] == "SYNTHETIC-001")
        assert fixture_001["actual_biased"] is True

    def test_synthetic_002_is_detected_as_biased(self) -> None:
        result = run_synthetic_validation()
        fixture_002 = next(f for f in result["fixtures"] if f["fixture_id"] == "SYNTHETIC-002")
        assert fixture_002["actual_biased"] is True

    def test_synthetic_003_is_not_flagged(self) -> None:
        result = run_synthetic_validation()
        fixture_003 = next(f for f in result["fixtures"] if f["fixture_id"] == "SYNTHETIC-003")
        assert fixture_003["actual_biased"] is False


@pytest.mark.unit
class TestAuditReviews:
    """Tests for audit_reviews()."""

    def test_clean_review_not_flagged(self) -> None:
        review = make_review(
            "r1",
            [
                {
                    "section_name": "Skills",
                    "content": "Strong Python and JavaScript skills demonstrated.",
                    "suggestions": ["Add more open source contributions."],
                }
            ],
        )
        results = audit_reviews([review])
        assert len(results) == 1
        assert results[0]["is_biased"] is False

    def test_biased_review_flagged(self) -> None:
        review = make_review(
            "r1",
            [
                {
                    "section_name": "Skills",
                    "content": "bootcamp training is inadequate for professional development",
                    "suggestions": [],
                }
            ],
        )
        results = audit_reviews([review])
        assert len(results) == 1
        assert results[0]["is_biased"] is True
        assert results[0]["signal_category"] == "dismissive_education"

    def test_demographic_bias_flagged_with_correct_category(self) -> None:
        review = make_review(
            "r1",
            [
                {
                    "section_name": "Skills",
                    "content": (
                        "immigrant developers can't communicate effectively in code reviews"
                    ),
                    "suggestions": [],
                }
            ],
        )
        results = audit_reviews([review])
        assert results[0]["signal_category"] == "demographic_assumption"

    def test_review_with_none_sections_skipped(self) -> None:
        review = make_review("r1", None)
        results = audit_reviews([review])
        assert results[0]["skipped"] is True
        assert results[0]["skip_reason"] == "empty_text"

    def test_review_with_empty_sections_skipped(self) -> None:
        review = make_review("r1", [])
        results = audit_reviews([review])
        assert results[0]["skipped"] is True

    def test_multiple_reviews_processed(self) -> None:
        reviews = [
            make_review(
                "r1",
                [
                    {
                        "section_name": "Skills",
                        "content": "Great Python skills.",
                        "suggestions": [],
                    }
                ],
            ),
            make_review(
                "r2",
                [
                    {
                        "section_name": "Skills",
                        "content": ("bootcamp training is inadequate for professional development"),
                        "suggestions": [],
                    }
                ],
            ),
        ]
        results = audit_reviews(reviews)
        assert len(results) == 2
        assert results[0]["is_biased"] is False
        assert results[1]["is_biased"] is True

    def test_result_has_required_fields(self) -> None:
        review = make_review(
            "r1",
            [{"section_name": "Skills", "content": "Good work.", "suggestions": []}],
        )
        results = audit_reviews([review])
        result = results[0]
        assert "review_id" in result
        assert "skipped" in result
        assert "is_biased" in result
        assert "reason" in result
        assert "signal_category" in result


@pytest.mark.unit
class TestComputeReport:
    """Tests for compute_report()."""

    def _make_synthetic_validation(self, all_passed: bool = True) -> dict:
        return {
            "all_passed": all_passed,
            "fixtures": [
                {
                    "fixture_id": "SYNTHETIC-001",
                    "label": "dismissive_education",
                    "expected_biased": True,
                    "actual_biased": True,
                    "reason": "Dismissive language about educational background",
                    "passed": all_passed,
                }
            ],
        }

    def test_report_has_required_fields(self) -> None:
        results: list[dict] = [
            {
                "skipped": False,
                "is_biased": False,
                "signal_category": None,
                "review_id": "r1",
                "reason": "",
            }
        ]
        report = compute_report(results, self._make_synthetic_validation())
        for field in [
            "generated_at",
            "sample_size",
            "evaluated",
            "skipped",
            "total_flagged",
            "flag_rate",
            "by_signal",
            "note",
            "synthetic_validation",
        ]:
            assert field in report

    def test_zero_flagged_when_all_clean(self) -> None:
        results: list[dict] = [
            {
                "skipped": False,
                "is_biased": False,
                "signal_category": None,
                "review_id": "r1",
                "reason": "",
            },
            {
                "skipped": False,
                "is_biased": False,
                "signal_category": None,
                "review_id": "r2",
                "reason": "",
            },
        ]
        report = compute_report(results, self._make_synthetic_validation())
        assert report["total_flagged"] == 0
        assert report["flag_rate"] == 0.0

    def test_flag_rate_calculated_correctly(self) -> None:
        results: list[dict] = [
            {
                "skipped": False,
                "is_biased": True,
                "signal_category": "dismissive_education",
                "review_id": "r1",
                "reason": "Dismissive",
            },
            {
                "skipped": False,
                "is_biased": False,
                "signal_category": None,
                "review_id": "r2",
                "reason": "",
            },
            {
                "skipped": False,
                "is_biased": False,
                "signal_category": None,
                "review_id": "r3",
                "reason": "",
            },
            {
                "skipped": False,
                "is_biased": False,
                "signal_category": None,
                "review_id": "r4",
                "reason": "",
            },
        ]
        report = compute_report(results, self._make_synthetic_validation())
        assert report["total_flagged"] == 1
        assert report["flag_rate"] == 0.25

    def test_skipped_excluded_from_evaluated_count(self) -> None:
        results: list[dict] = [
            {
                "skipped": True,
                "skip_reason": "empty_text",
                "is_biased": None,
                "signal_category": None,
                "review_id": "r1",
                "reason": None,
            },
            {
                "skipped": False,
                "is_biased": False,
                "signal_category": None,
                "review_id": "r2",
                "reason": "",
            },
        ]
        report = compute_report(results, self._make_synthetic_validation())
        assert report["evaluated"] == 1
        assert report["skipped"] == 1

    def test_signal_breakdown_correct(self) -> None:
        results: list[dict] = [
            {
                "skipped": False,
                "is_biased": True,
                "signal_category": "dismissive_education",
                "review_id": "r1",
                "reason": "Dismissive",
            },
            {
                "skipped": False,
                "is_biased": True,
                "signal_category": "demographic_assumption",
                "review_id": "r2",
                "reason": "Demographic",
            },
            {
                "skipped": False,
                "is_biased": False,
                "signal_category": None,
                "review_id": "r3",
                "reason": "",
            },
        ]
        report = compute_report(results, self._make_synthetic_validation())
        assert report["by_signal"]["dismissive_education"]["count"] == 1
        assert report["by_signal"]["demographic_assumption"]["count"] == 1

    def test_empty_results_returns_zero_flag_rate(self) -> None:
        results: list[dict] = []
        report = compute_report(results, self._make_synthetic_validation())
        assert report["flag_rate"] == 0.0
        assert report["total_flagged"] == 0

    def test_flagged_reviews_included_in_report(self) -> None:
        results: list[dict] = [
            {
                "skipped": False,
                "is_biased": True,
                "signal_category": "dismissive_education",
                "review_id": "r1",
                "reason": "Dismissive language about educational background",
            },
            {
                "skipped": False,
                "is_biased": False,
                "signal_category": None,
                "review_id": "r2",
                "reason": "",
            },
        ]
        report = compute_report(results, self._make_synthetic_validation())
        assert len(report["flagged_reviews"]) == 1
        assert report["flagged_reviews"][0]["review_id"] == "r1"
