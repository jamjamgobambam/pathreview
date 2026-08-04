"""Tests for repo_analyzer.py"""

import pytest

from agent.tools.repo_analyzer import RepoAnalyzer


@pytest.mark.unit
class TestRepoAnalyzer:
    """Test suite for RepoAnalyzer."""

    @pytest.fixture
    def analyzer(self) -> RepoAnalyzer:
        """Create a RepoAnalyzer instance."""
        return RepoAnalyzer()

    @pytest.mark.parametrize(
        "files",
        [
            ["tests/test_app.py"],
            ["test/test_app.py"],
            ["src/app/pytest.ini"],
            ["src/test_api.py"],
            ["src/module/tests/test_service.py"],
            ["src\\module\\tests\\test_service.py"],
        ],
    )
    def test_detects_test_signals(self, analyzer: RepoAnalyzer, files: list[str]) -> None:
        """Test common test-path signals set has_tests to True."""
        result = analyzer.execute({"files": files})

        assert result.success is True
        assert result.data["has_tests"] is True

    @pytest.mark.parametrize(
        "files",
        [
            ["src/app.py", "README.md", "docs/guide.md"],
            ["src/latest_data.py", "contest/results.csv"],
            ["src/module/unit.py", "scripts/deploy.sh"],
            [],
        ],
    )
    def test_does_not_false_positive(self, analyzer: RepoAnalyzer, files: list[str]) -> None:
        """Test unrelated file names do not trigger has_tests."""
        result = analyzer.execute({"files": files})

        assert result.success is True
        assert result.data["has_tests"] is False

    def test_missing_files_key_defaults_false(self, analyzer: RepoAnalyzer) -> None:
        """Test missing files key returns False rather than error."""
        result = analyzer.execute({})

        assert result.success is True
        assert result.data["has_tests"] is False
