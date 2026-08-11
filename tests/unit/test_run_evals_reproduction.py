"""Tests that the offline eval runner (issue #40 / B-20) produces a quality report."""

from pathlib import Path

import pytest

from rag.evaluator.eval_suite import EvalResult
from scripts import run_evals


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "sample_profiles"


@pytest.mark.unit
class TestOfflineEvalRunner:
    """Verify the standalone eval runner writes a scored JSON report."""

    def test_run_evals_writes_eval_results_json(self, tmp_path):
        """Runner creates eval_results.json with summary and portfolio scores."""
        output = tmp_path / "eval_results.json"
        exit_code = run_evals.main(
            ["--fixtures-dir", str(FIXTURES_DIR), "--output", str(output)]
        )
        assert exit_code == 0
        assert output.exists()

        import json

        report = json.loads(output.read_text(encoding="utf-8"))
        assert "summary" in report
        assert "portfolios" in report
        assert report["summary"]["portfolio_count"] == 3
        assert "avg_actionability_score" in report["summary"]
        for portfolio in report["portfolios"]:
            assert "relevance_score" in portfolio
            assert "faithfulness_score" in portfolio
            assert "actionability_score" in portfolio
            assert "overall_score" in portfolio

    def test_benchmark_fixtures_directory_exists(self):
        """Curated benchmark portfolios are available for the runner."""
        assert FIXTURES_DIR.is_dir()
        assert list(FIXTURES_DIR.glob("*.json"))

    def test_eval_result_includes_actionability_score(self):
        """EvalResult includes actionability alongside relevance and faithfulness."""
        assert "actionability_score" in EvalResult.__dataclass_fields__
