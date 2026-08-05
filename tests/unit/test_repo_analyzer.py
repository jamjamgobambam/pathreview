"""Tests for repo_analyzer.py"""

import json

import pytest

from ingestion.parsers.base import ParseResult
from ingestion.parsers.repo_analyzer import RepoAnalyzer


@pytest.mark.unit
class TestRepoAnalyzer:
    """Test suite for RepoAnalyzer."""

    @pytest.fixture
    def analyzer(self) -> RepoAnalyzer:
        """Create a RepoAnalyzer instance."""
        return RepoAnalyzer()

    def test_has_tests_true_when_file_structure_present(self, analyzer: RepoAnalyzer) -> None:
        """When file_structure includes a tests/ path, has_tests should be True."""
        repo_data = {
            "name": "example-repo",
            "file_structure": "README.md\ntests/test_example.py\nsrc/main.py",
        }
        result = analyzer.parse(json.dumps(repo_data))

        assert isinstance(result, ParseResult)
        assert result.metadata["has_tests"] is True

    def test_has_tests_false_when_file_structure_missing(self, analyzer: RepoAnalyzer) -> None:
        """
        Reproduces issue #50: GitHubTool never populates 'file_structure' in
        the metadata it returns, so has_tests always evaluates to False here,
        even for repositories that genuinely contain tests. This test
        documents the current (broken) behavior against real-world input
        shape, i.e. a repo_data dict with no file_structure key at all,
        matching what github_tool.py actually produces.
        """
        repo_data_missing_file_structure = {
            "name": "example-repo",
            "description": "A repo with real tests, but no file_structure key",
            "language": "Python",
        }
        result = analyzer.parse(json.dumps(repo_data_missing_file_structure))

        assert isinstance(result, ParseResult)
        assert result.metadata["has_tests"] is False
