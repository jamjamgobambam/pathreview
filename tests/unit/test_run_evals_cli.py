"""Tests for scripts/run_evals.py"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_evals.py"


def _load_cli():
    """Import scripts/run_evals.py as a module.

    scripts/ is excluded from the installed distribution, so the CLI is loaded
    from its path rather than imported as a package.

    Returns:
        The loaded module
    """
    spec = importlib.util.spec_from_file_location("run_evals_cli", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def cli():
    """Load the run_evals CLI module once for the suite."""
    return _load_cli()


@pytest.fixture
def fixtures_dir(tmp_path):
    """Create a directory holding one valid benchmark fixture."""
    directory = tmp_path / "sample_profiles"
    directory.mkdir()
    payload = {
        "portfolio_id": "cli01",
        "description": "Fixture used by the CLI tests",
        "profile": {"github_username": "testuser", "projects": []},
        "documents": [
            {
                "source_id": "readme_cli01",
                "source_type": "readme",
                "text": (
                    "# Ledger Service\nA small ledger.\n\n"
                    "## Overview\nA python service exposing rest apis built with fastapi.\n\n"
                    "## Storage\nEntries persist in postgresql with alembic migrations.\n\n"
                    "## Testing\nCovered by pytest cases in continuous integration.\n\n"
                    "## Deployment\nShips as a docker image promoted through staging."
                ),
            }
        ],
        "queries": ["python fastapi rest apis"],
    }
    (directory / "cli01.json").write_text(json.dumps(payload), encoding="utf-8")
    return directory


@pytest.mark.unit
class TestRunEvalsCLI:
    """Test suite for the eval runner command line entry point."""

    def test_successful_run_exits_zero(self, cli, fixtures_dir, tmp_path):
        """Test a completed run exits 0."""
        output = tmp_path / "eval_results.json"

        exit_code = cli.main(["--fixtures-dir", str(fixtures_dir), "--output", str(output)])

        assert exit_code == 0

    def test_successful_run_creates_eval_results_json(self, cli, fixtures_dir, tmp_path):
        """Test the report file the CI workflow reads is actually written."""
        output = tmp_path / "eval_results.json"

        cli.main(["--fixtures-dir", str(fixtures_dir), "--output", str(output)])

        assert output.exists()
        payload = json.loads(output.read_text())
        assert payload["portfolio_count"] == 1
        assert payload["llm_provider"]

    def test_missing_fixtures_directory_exits_non_zero(self, cli, tmp_path, capsys):
        """Test a missing benchmark set fails loudly instead of reporting success."""
        exit_code = cli.main(
            [
                "--fixtures-dir",
                str(tmp_path / "does_not_exist"),
                "--output",
                str(tmp_path / "eval_results.json"),
            ]
        )

        assert exit_code == 1
        assert "Evaluation failed" in capsys.readouterr().err

    def test_missing_fixtures_directory_writes_no_report(self, cli, tmp_path):
        """Test a failed run leaves no report claiming zero quality."""
        output = tmp_path / "eval_results.json"

        cli.main(["--fixtures-dir", str(tmp_path / "does_not_exist"), "--output", str(output)])

        assert not output.exists()

    def test_malformed_fixture_exits_non_zero(self, cli, fixtures_dir, tmp_path, capsys):
        """Test invalid JSON in the benchmark set is reported by filename."""
        (fixtures_dir / "broken.json").write_text("{not json", encoding="utf-8")

        exit_code = cli.main(
            [
                "--fixtures-dir",
                str(fixtures_dir),
                "--output",
                str(tmp_path / "eval_results.json"),
            ]
        )

        assert exit_code == 1
        assert "broken.json" in capsys.readouterr().err

    def test_unusable_provider_exits_non_zero_without_traceback(
        self, cli, fixtures_dir, tmp_path, capsys, monkeypatch
    ):
        """Test a bad LLM_PROVIDER reports an actionable message rather than a traceback."""
        monkeypatch.setattr("core.config.settings.llm_provider", "not-a-provider")

        exit_code = cli.main(
            [
                "--fixtures-dir",
                str(fixtures_dir),
                "--output",
                str(tmp_path / "eval_results.json"),
            ]
        )

        assert exit_code == 1
        assert "Evaluation failed" in capsys.readouterr().err

    def test_missing_output_directory_is_created(self, cli, fixtures_dir, tmp_path):
        """Test an output path under a directory that does not exist yet still succeeds."""
        output = tmp_path / "reports" / "nested" / "eval_results.json"

        exit_code = cli.main(["--fixtures-dir", str(fixtures_dir), "--output", str(output)])

        assert exit_code == 0
        assert output.exists()

    def test_unwritable_output_exits_non_zero_without_claiming_success(
        self, cli, fixtures_dir, tmp_path, capsys
    ):
        """Test a write failure is reported as a failure, not as a completed evaluation."""
        blocked = tmp_path / "eval_results.json"
        blocked.mkdir()

        exit_code = cli.main(["--fixtures-dir", str(fixtures_dir), "--output", str(blocked)])

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "could not be written" in captured.err
        assert "Results written to" not in captured.out

    def test_repeated_runs_write_identical_bytes(self, cli, fixtures_dir, tmp_path):
        """Test running the CLI twice produces the same file byte for byte."""
        first = tmp_path / "first.json"
        second = tmp_path / "second.json"

        cli.main(["--fixtures-dir", str(fixtures_dir), "--output", str(first)])
        cli.main(["--fixtures-dir", str(fixtures_dir), "--output", str(second)])

        assert first.read_bytes() == second.read_bytes()

    def test_summary_reports_where_results_were_written(self, cli, fixtures_dir, tmp_path, capsys):
        """Test the success message names the file that was actually written."""
        output = tmp_path / "eval_results.json"

        cli.main(["--fixtures-dir", str(fixtures_dir), "--output", str(output)])

        assert f"Results written to {output}" in capsys.readouterr().out

    def test_defaults_match_the_ci_contract(self, cli):
        """Test bare `python scripts/run_evals.py` uses the paths CI expects."""
        args = cli.build_parser().parse_args([])

        assert args.output == Path("eval_results.json")
        assert args.fixtures_dir == Path("tests/fixtures/sample_profiles")
