"""Tests for workflow_parser.py

REPRODUCTION (Issue #14): As of this commit, ``ingestion/parsers/workflow_parser.py``
does not exist, so the import below fails at collection time with a
``ModuleNotFoundError``. That failure is the concrete proof that the ingestion
pipeline has no parser for ``.github/workflows/*.yml`` files and therefore cannot
detect CI/CD / DevOps skills. These tests are written to PASS once ``WorkflowParser``
is implemented per PLAN.md.

Run:  pytest tests/unit/test_workflow_parser.py -v
"""

import pytest

from ingestion.parsers.base import ParseResult
from ingestion.parsers.workflow_parser import WorkflowParser

SAMPLE_WORKFLOW_YAML = """
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Run tests
        run: pytest tests/ -v
      - name: Build image
        run: docker build -t app:latest .

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: ./scripts/deploy.sh
"""


@pytest.mark.unit
class TestWorkflowParser:
    """Test suite for WorkflowParser."""

    @pytest.fixture
    def parser(self) -> WorkflowParser:
        """Create a WorkflowParser instance."""
        return WorkflowParser()

    def test_parse_returns_parse_result(self, parser: WorkflowParser) -> None:
        """Parsing a workflow returns a ParseResult tagged as 'workflow'."""
        result = parser.parse(SAMPLE_WORKFLOW_YAML)

        assert isinstance(result, ParseResult)
        assert result.source_type == "workflow"
        assert result.metadata["source_type"] == "workflow"

    def test_detects_cicd_skills(self, parser: WorkflowParser) -> None:
        """The parser surfaces the CI/CD skills named in issue #14."""
        result = parser.parse(SAMPLE_WORKFLOW_YAML)

        # skills are threaded into metadata (exact container shape is an
        # implementation detail; assert on the human-readable text + metadata blob)
        haystack = (result.text + " " + str(result.metadata)).lower()
        assert "github actions" in haystack
        assert "docker" in haystack
        assert "pytest" in haystack
        assert "deploy" in haystack

    def test_parse_bytes_input(self, parser: WorkflowParser) -> None:
        """Workflow YAML provided as UTF-8 bytes is accepted."""
        result = parser.parse(SAMPLE_WORKFLOW_YAML.encode("utf-8"))

        assert isinstance(result, ParseResult)
        assert result.source_type == "workflow"

    def test_parse_invalid_content_type(self, parser: WorkflowParser) -> None:
        """Non-str/bytes content raises ValueError."""
        with pytest.raises(ValueError):
            parser.parse(12345)
