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

    def test_empty_content_returns_result_with_no_skills(self, parser: WorkflowParser) -> None:
        """An empty file parses to a ParseResult with no detected skills."""
        result = parser.parse("")

        assert isinstance(result, ParseResult)
        assert result.source_type == "workflow"
        assert result.metadata["skills"] == ""
        assert result.metadata["job_count"] == 0

    def test_whitespace_only_content(self, parser: WorkflowParser) -> None:
        """Whitespace-only content is handled like an empty document."""
        result = parser.parse("   \n   \n")

        assert isinstance(result, ParseResult)
        assert result.metadata["skills"] == ""

    def test_valid_yaml_but_not_a_workflow(self, parser: WorkflowParser) -> None:
        """Valid YAML without on:/jobs: is not flagged as a GitHub Actions workflow."""
        result = parser.parse("name: not-a-workflow\nfoo:\n  bar: baz\n")

        assert "GitHub Actions" not in result.metadata["skills"]
        assert result.metadata["job_count"] == 0

    def test_malformed_yaml_raises_value_error(self, parser: WorkflowParser) -> None:
        """Malformed YAML raises ValueError, consistent with the other parsers."""
        with pytest.raises(ValueError):
            parser.parse("on: [push, pull_request\njobs: :::")

    def test_on_key_boolean_gotcha(self, parser: WorkflowParser) -> None:
        """Triggers are read even though PyYAML resolves the `on:` key to True."""
        yaml_text = (
            "on:\n"
            "  push:\n"
            "  pull_request:\n"
            "jobs:\n"
            "  a:\n"
            "    runs-on: ubuntu-latest\n"
        )
        result = parser.parse(yaml_text)

        assert "push" in result.metadata["triggers"]
        assert "pull_request" in result.metadata["triggers"]
        assert "GitHub Actions" in result.metadata["skills"]

    def test_triggers_but_zero_jobs(self, parser: WorkflowParser) -> None:
        """A workflow with triggers but no jobs is still GitHub Actions, 0 jobs."""
        result = parser.parse("on: [push]\n")

        assert result.metadata["job_count"] == 0
        assert "GitHub Actions" in result.metadata["skills"]

    def test_matrix_build_parses(self, parser: WorkflowParser) -> None:
        """Matrix builds (strategy.matrix) parse and the job/steps are detected."""
        yaml_text = (
            "on: [push]\n"
            "jobs:\n"
            "  test:\n"
            "    runs-on: ubuntu-latest\n"
            "    strategy:\n"
            "      matrix:\n"
            "        python: ['3.10', '3.11']\n"
            "    steps:\n"
            "      - run: pytest\n"
        )
        result = parser.parse(yaml_text)

        assert result.metadata["job_count"] == 1
        assert result.metadata["runs_pytest"] is True

    def test_reusable_workflow_uses_at_job_level(self, parser: WorkflowParser) -> None:
        """A job-level `uses:` (reusable workflow) is captured in actions_used."""
        yaml_text = (
            "on: [push]\n"
            "jobs:\n"
            "  call:\n"
            "    uses: owner/repo/.github/workflows/reusable.yml@main\n"
        )
        result = parser.parse(yaml_text)

        assert "owner/repo/.github/workflows/reusable.yml@main" in result.metadata["actions_used"]

    def test_metadata_values_are_chromadb_scalars(self, parser: WorkflowParser) -> None:
        """Every metadata value must be scalar (str/int/float/bool) for ChromaDB."""
        result = parser.parse(SAMPLE_WORKFLOW_YAML)

        scalar_types = (str, int, float, bool)
        for key, value in result.metadata.items():
            assert isinstance(value, scalar_types), f"{key} is not scalar"

    def test_reuses_skill_extractor(self, parser: WorkflowParser) -> None:
        """The parser threads SkillExtractor output into extracted_skills."""
        result = parser.parse(SAMPLE_WORKFLOW_YAML)

        assert "extracted_skills" in result.metadata
        assert isinstance(result.metadata["extracted_skills"], str)

    def test_skill_flags_reflect_sample(self, parser: WorkflowParser) -> None:
        """has_docker / runs_pytest / has_deployment reflect the sample workflow."""
        result = parser.parse(SAMPLE_WORKFLOW_YAML)

        assert result.metadata["has_docker"] is True
        assert result.metadata["runs_pytest"] is True
        assert result.metadata["has_deployment"] is True
