"""Tests for safety/bias_audit.py"""

from pathlib import Path

import pytest

from safety.bias_audit import (
    ConfusionMatrix,
    LabeledSample,
    audit_samples,
    extract_review_text,
    format_report_text,
    load_labeled_samples,
)

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "bias_audit_samples.json"


def _predict_by_keyword(text: str) -> tuple[bool, str]:
    """Fake predictor: flags text containing 'biased' so scoring is deterministic."""
    if "biased" in text.lower():
        return True, "contains keyword"
    return False, ""


@pytest.mark.unit
class TestExtractReviewText:
    """Tests for flattening a review's sections JSON into auditable text."""

    def test_extracts_content_and_suggestions(self) -> None:
        """Content and suggestion strings are joined together."""
        sections = [
            {"content": "Strong Python skills.", "suggestions": ["Add a README", "Add tests"]},
            {"content": "Clear positioning.", "suggestions": []},
        ]

        text = extract_review_text(sections)

        assert "Strong Python skills." in text
        assert "Add a README" in text
        assert "Add tests" in text
        assert "Clear positioning." in text

    def test_none_sections_returns_empty_string(self) -> None:
        """A failed review with sections=None yields an empty string, not an error."""
        assert extract_review_text(None) == ""

    def test_string_sections_returns_empty_string(self) -> None:
        """A string is not a list of sections and must not be iterated char by char."""
        assert extract_review_text("not a list") == ""

    def test_malformed_sections_are_skipped(self) -> None:
        """Non-dict entries and missing/blank fields are skipped gracefully."""
        sections = [
            "junk",
            {"content": "   "},
            {"suggestions": ["Keep this", 42, None]},
            {"content": "Real content"},
        ]

        text = extract_review_text(sections)

        assert "Real content" in text
        assert "Keep this" in text
        assert "junk" not in text
        assert "42" not in text

    def test_empty_list_returns_empty_string(self) -> None:
        """An empty sections list yields an empty string."""
        assert extract_review_text([]) == ""


@pytest.mark.unit
class TestConfusionMatrix:
    """Tests for confusion-matrix tallying and derived rates."""

    def test_record_classifies_all_four_outcomes(self) -> None:
        """Each (expected, predicted) combination lands in the right bucket."""
        matrix = ConfusionMatrix()
        matrix.record(expected_biased=True, predicted_biased=True)  # TP
        matrix.record(expected_biased=True, predicted_biased=False)  # FN
        matrix.record(expected_biased=False, predicted_biased=True)  # FP
        matrix.record(expected_biased=False, predicted_biased=False)  # TN

        assert matrix.true_positive == 1
        assert matrix.false_negative == 1
        assert matrix.false_positive == 1
        assert matrix.true_negative == 1
        assert matrix.total == 4

    def test_rates_are_computed_correctly(self) -> None:
        """Precision, recall, and FP/FN rates match hand-computed values."""
        matrix = ConfusionMatrix(
            true_positive=3, false_positive=1, true_negative=4, false_negative=2
        )

        assert matrix.precision == pytest.approx(3 / 4)
        assert matrix.recall == pytest.approx(3 / 5)
        assert matrix.false_positive_rate == pytest.approx(1 / 5)
        assert matrix.false_negative_rate == pytest.approx(2 / 5)

    def test_denominators_match_their_rates(self) -> None:
        """The exposed denominators are the ones the reported rates divide by."""
        matrix = ConfusionMatrix(
            true_positive=3, false_positive=1, true_negative=4, false_negative=2
        )

        assert matrix.flagged == 4  # precision denominator
        assert matrix.labeled_biased == 5  # recall and FN-rate denominator
        assert matrix.labeled_neutral == 5  # FP-rate denominator

    def test_rates_are_none_when_undefined(self) -> None:
        """Rates with a zero denominator return None instead of dividing by zero."""
        empty = ConfusionMatrix()

        assert empty.precision is None
        assert empty.recall is None
        assert empty.false_positive_rate is None
        assert empty.false_negative_rate is None


@pytest.mark.unit
class TestAuditSamples:
    """Tests for scoring labeled samples into an audit report."""

    def test_counts_and_per_signal_breakdown(self) -> None:
        """Overall and per-signal matrices reflect the fake predictor's decisions."""
        samples = [
            LabeledSample("this is biased text", expected_biased=True, signal="education"),
            LabeledSample("neutral education text", expected_biased=False, signal="education"),
            LabeledSample("this is biased too", expected_biased=True, signal="age"),
            LabeledSample("a missed biased phrase", expected_biased=True, signal="age"),
        ]

        report = audit_samples(samples, predictor=_predict_by_keyword)

        assert report.overall.true_positive == 3
        assert report.overall.true_negative == 1
        assert report.overall.false_negative == 0
        assert report.by_signal["education"].total == 2
        assert report.by_signal["age"].total == 2

    def test_false_negative_is_recorded(self) -> None:
        """A biased sample the predictor misses is counted as a false negative."""
        samples = [LabeledSample("subtle prejudice here", expected_biased=True, signal="origin")]

        report = audit_samples(samples, predictor=_predict_by_keyword)

        assert report.overall.false_negative == 1
        assert report.results[0].outcome == "fn"

    def test_empty_text_samples_are_skipped(self) -> None:
        """Blank samples are counted as skipped and excluded from the matrix."""
        samples = [
            LabeledSample("", expected_biased=False, signal="none"),
            LabeledSample("   ", expected_biased=True, signal="none"),
            LabeledSample("this is biased", expected_biased=True, signal="none"),
        ]

        report = audit_samples(samples, predictor=_predict_by_keyword)

        assert report.skipped_empty == 2
        assert report.overall.total == 1

    def test_report_to_dict_is_json_shaped(self) -> None:
        """to_dict exposes the fields the JSON report and detail rows need."""
        samples = [LabeledSample("this is biased", expected_biased=True, signal="education")]

        report_dict = audit_samples(samples, predictor=_predict_by_keyword).to_dict()

        assert report_dict["sample_count"] == 1
        assert report_dict["overall"]["counts"]["true_positive"] == 1
        assert "education" in report_dict["by_signal"]
        assert report_dict["results"][0]["outcome"] == "tp"


@pytest.mark.unit
class TestLoadLabeledSamples:
    """Tests for loading labeled samples from JSON."""

    def test_loads_bundled_fixture(self) -> None:
        """The shipped fixture parses and includes both biased and neutral samples."""
        samples = load_labeled_samples(FIXTURE_PATH)

        assert len(samples) > 0
        assert any(s.expected_biased for s in samples)
        assert any(not s.expected_biased for s in samples)
        assert any(s.signal == "education" for s in samples)

    def test_missing_required_field_raises(self, tmp_path: Path) -> None:
        """A sample missing expected_biased is rejected with a clear error."""
        bad = tmp_path / "bad.json"
        bad.write_text('[{"text": "no label here"}]', encoding="utf-8")

        with pytest.raises(ValueError, match="expected_biased"):
            load_labeled_samples(bad)

    def test_non_list_top_level_raises(self, tmp_path: Path) -> None:
        """A JSON object at the top level is rejected."""
        bad = tmp_path / "bad.json"
        bad.write_text('{"text": "x", "expected_biased": true}', encoding="utf-8")

        with pytest.raises(ValueError, match="list"):
            load_labeled_samples(bad)


@pytest.mark.unit
class TestFormatReportText:
    """Tests for the human-readable report rendering."""

    def test_includes_overall_and_signal_sections(self) -> None:
        """The rendered report names the overall block and each signal breakdown."""
        samples = [
            LabeledSample("this is biased", expected_biased=True, signal="education"),
            LabeledSample("neutral text", expected_biased=False, signal="none"),
        ]

        rendered = format_report_text(audit_samples(samples, predictor=_predict_by_keyword))

        assert "Bias audit report" in rendered
        assert "Overall" in rendered
        assert "[education]" in rendered
        assert "false_negative_rate" in rendered

    def test_rates_are_reported_with_their_counts(self) -> None:
        """Every rate carries its (numerator/denominator) so small samples are obvious."""
        samples = [
            LabeledSample("this is biased", expected_biased=True, signal="origin"),
            LabeledSample("a missed slight", expected_biased=True, signal="origin"),
        ]

        rendered = format_report_text(audit_samples(samples, predictor=_predict_by_keyword))

        # 1 of 2 biased samples missed — the percentage alone would imply more data.
        assert "false_negative_rate=50.0% (1/2)" in rendered
        assert "recall=50.0% (1/2)" in rendered

    def test_undefined_rates_still_show_counts(self) -> None:
        """A rate with a zero denominator renders as n/a with its 0/0 counts."""
        samples = [LabeledSample("neutral text", expected_biased=False, signal="none")]

        rendered = format_report_text(audit_samples(samples, predictor=_predict_by_keyword))

        # Nothing was labeled biased, so the FN rate is undefined rather than 0%.
        assert "false_negative_rate=n/a (0/0)" in rendered
        assert "false_positive_rate=0.0% (0/1)" in rendered
