"""Tests for workflow_parser.py"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ingestion.parsers.base import ParseResult
from ingestion.parsers.workflow_parser import WorkflowParser


@pytest.mark.unit
class TestWorkflowParser:
    """Test suite for WorkflowParser.

    Following the test_batch_processor.py pattern:
    - @pytest.mark.unit class decorator
    - @pytest.fixture for setup
    - Mock filesystem I/O (Path.glob, Path.read_text, yaml.safe_load)
      so tests run without real .yml files on disk
    """

    @pytest.fixture
    def parser(self):
        """Create a WorkflowParser instance."""
        return WorkflowParser()

    @pytest.fixture
    def sample_workflow_dict(self):
        """Return a dict matching yaml.safe_load output for a GitHub Actions workflow."""
        return {
            "name": "CI/CD Pipeline",
            "on": {"push": {"branches": ["main"]}},
            "jobs": {
                "test": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"uses": "actions/checkout@v4"},
                        {"name": "Run pytest", "run": "pytest tests/ -v"},
                        {"uses": "docker/build-push-action@v5", "with": {"push": True}},
                    ],
                },
                "deploy": {
                    "runs-on": "ubuntu-latest",
                    "needs": "test",
                    "steps": [
                        {"uses": "actions/checkout@v4"},
                        {"name": "Deploy to production", "run": "kubectl apply -f k8s/"},
                    ],
                },
            },
        }

    def test_parse_finds_workflow_files(self, parser, sample_workflow_dict):
        """Test that parser discovers .github/workflows/*.yml files."""
        mock_path = MagicMock(spec=Path)
        mock_workflow_file = MagicMock(spec=Path)
        mock_workflow_file.name = "ci.yml"
        mock_workflow_file.read_text.return_value = "mock yaml content"

        # Mock Path.glob to return our fake workflow file
        mock_path.glob.return_value = [mock_workflow_file]

        with patch("pathlib.Path.glob", return_value=[mock_workflow_file]):
            with patch("yaml.safe_load", return_value=sample_workflow_dict):
                result = parser.parse("/fake/repo")

        assert isinstance(result, ParseResult)
        assert result.source_type == "workflow"
        # The parsed text should contain action references and job names
        assert "actions/checkout" in result.text
        assert "pytest" in result.text.lower()
        assert "docker" in result.text.lower()

    def test_parse_no_workflows_directory(self, parser):
        """Test graceful handling when .github/workflows/ does not exist."""
        mock_path = MagicMock(spec=Path)
        mock_path.glob.return_value = []  # No files found

        with patch("pathlib.Path.glob", return_value=[]):
            result = parser.parse("/fake/repo")

        assert isinstance(result, ParseResult)
        assert result.text == ""
        assert result.metadata.get("file_count") == 0
        assert result.source_type == "workflow"

    def test_parse_multiple_workflows(self, parser, sample_workflow_dict):
        """Test parsing multiple workflow files."""
        mock_file1 = MagicMock(spec=Path)
        mock_file1.name = "ci.yml"
        mock_file1.read_text.return_value = "ci yaml"

        mock_file2 = MagicMock(spec=Path)
        mock_file2.name = "deploy.yml"
        mock_file2.read_text.return_value = "deploy yaml"

        with patch("pathlib.Path.glob", return_value=[mock_file1, mock_file2]):
            with patch("yaml.safe_load", side_effect=[sample_workflow_dict, sample_workflow_dict]):
                result = parser.parse("/fake/repo")

        assert result.metadata.get("file_count") == 2
        workflow_names = result.metadata.get("workflow_names", [])
        assert "ci.yml" in workflow_names
        assert "deploy.yml" in workflow_names

    def test_parse_malformed_yaml_logs_warning(self, parser, caplog):
        """Test that malformed YAML is skipped with a warning, not a crash."""
        mock_file = MagicMock(spec=Path)
        mock_file.name = "broken.yml"
        mock_file.read_text.return_value = "invalid: yaml: ["

        with patch("pathlib.Path.glob", return_value=[mock_file]):
            with patch("yaml.safe_load", side_effect=Exception("YAML parse error")):
                result = parser.parse("/fake/repo")

        assert isinstance(result, ParseResult)
        # Should log a warning about the bad file
        assert "broken.yml" in caplog.text or "yaml" in caplog.text.lower()

    def test_parse_empty_workflow_file(self, parser):
        """Test that empty workflow files are counted but contribute no text."""
        mock_file = MagicMock(spec=Path)
        mock_file.name = "empty.yml"
        mock_file.read_text.return_value = ""

        with patch("pathlib.Path.glob", return_value=[mock_file]):
            with patch("yaml.safe_load", return_value={}):
                result = parser.parse("/fake/repo")

        assert result.metadata.get("file_count") == 1
        # Empty workflow produces no extractable text
        assert "empty.yml" not in result.text

    def test_extracted_text_contains_action_references(self, parser, sample_workflow_dict):
        """Test that the parsed text includes uses: references for skill detection."""
        mock_file = MagicMock(spec=Path)
        mock_file.name = "ci.yml"
        mock_file.read_text.return_value = "mock content"

        with patch("pathlib.Path.glob", return_value=[mock_file]):
            with patch("yaml.safe_load", return_value=sample_workflow_dict):
                result = parser.parse("/fake/repo")

        # These strings must appear so SkillExtractor can match against them
        assert "actions/checkout" in result.text
        assert "docker/build-push-action" in result.text
        assert "ubuntu-latest" in result.text

    def test_parse_preserves_metadata(self, parser, sample_workflow_dict):
        """Test that metadata includes workflow names and file count."""
        mock_file = MagicMock(spec=Path)
        mock_file.name = "ci.yml"
        mock_file.read_text.return_value = "content"

        with patch("pathlib.Path.glob", return_value=[mock_file]):
            with patch("yaml.safe_load", return_value=sample_workflow_dict):
                result = parser.parse("/fake/repo")

        assert result.metadata["source_type"] == "workflow"
        assert result.metadata["file_count"] == 1
        assert "ci.yml" in result.metadata["workflow_names"]
