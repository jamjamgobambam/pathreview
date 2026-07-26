"""Tests for workflow_parser.py"""

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
      - name: Run tests
        run: pytest tests/

  build-and-push:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: myapp:latest
"""


@pytest.mark.unit
class TestWorkflowParser:
    """Test suite for WorkflowParser."""

    @pytest.fixture
    def parser(self):
        """Create a WorkflowParser instance."""
        return WorkflowParser()

    def test_parse_standard_workflow(self, parser):
        """Test parsing a standard GitHub Actions workflow."""
        result = parser.parse(SAMPLE_WORKFLOW_YAML)

        assert isinstance(result, ParseResult)
        assert result.source_type == "workflow"
        assert result.metadata["source_type"] == "workflow"
        assert result.metadata["workflow_name"] == "CI"

    def test_extract_triggers(self, parser):
        """Test that triggers are extracted from the `on:` key."""
        result = parser.parse(SAMPLE_WORKFLOW_YAML)

        assert set(result.metadata["triggers"]) == {"push", "pull_request"}

    def test_extract_string_trigger(self, parser):
        """Test that a single string trigger (e.g. `on: push`) is normalized to a list."""
        workflow = "name: CI\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
        result = parser.parse(workflow)

        assert result.metadata["triggers"] == ["push"]

    def test_extract_list_trigger(self, parser):
        """Test that a list of triggers (e.g. `on: [push, pull_request]`) is preserved."""
        workflow = (
            "name: CI\non: [push, pull_request]\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
        )
        result = parser.parse(workflow)

        assert result.metadata["triggers"] == ["push", "pull_request"]

    def test_extract_jobs(self, parser):
        """Test that jobs are extracted with name, runner, and dependencies."""
        result = parser.parse(SAMPLE_WORKFLOW_YAML)
        jobs = result.metadata["jobs"]

        assert result.metadata["job_count"] == 2
        job_names = {job["name"] for job in jobs}
        assert job_names == {"test", "build-and-push"}

        build_job = next(job for job in jobs if job["name"] == "build-and-push")
        assert build_job["runs_on"] == "ubuntu-latest"
        assert build_job["needs"] == ["test"]

    def test_extract_actions_used(self, parser):
        """Test that `uses:` actions are collected across all jobs."""
        result = parser.parse(SAMPLE_WORKFLOW_YAML)

        assert "actions/checkout@v4" in result.metadata["actions_used"]
        assert "docker/build-push-action@v5" in result.metadata["actions_used"]

    def test_extract_run_commands(self, parser):
        """Test that `run:` commands are collected across all jobs."""
        result = parser.parse(SAMPLE_WORKFLOW_YAML)

        assert "pytest tests/" in result.metadata["run_commands"]

    def test_parse_workflow_with_no_jobs(self, parser):
        """Test parsing a workflow with no `jobs:` key - returns empty job list, no crash."""
        workflow = "name: Empty\non: push\n"
        result = parser.parse(workflow)

        assert result.metadata["jobs"] == []
        assert result.metadata["job_count"] == 0
        assert result.metadata["actions_used"] == []
        assert result.metadata["run_commands"] == []

    def test_parse_job_with_no_steps(self, parser):
        """Test parsing a job with no `steps:` key."""
        workflow = "name: CI\non: push\njobs:\n  noop:\n    runs-on: ubuntu-latest\n"
        result = parser.parse(workflow)

        job = result.metadata["jobs"][0]
        assert job["steps"] == []

    def test_parse_missing_workflow_name(self, parser):
        """Test that a workflow without a `name:` key falls back to a default."""
        workflow = "on: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
        result = parser.parse(workflow)

        assert result.metadata["workflow_name"] == "Unnamed workflow"

    def test_parse_bytes_input(self, parser):
        """Test parsing workflow YAML from bytes input."""
        result = parser.parse(SAMPLE_WORKFLOW_YAML.encode("utf-8"))

        assert result.metadata["workflow_name"] == "CI"

    def test_parse_invalid_content_type(self, parser):
        """Test that invalid content type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            parser.parse(12345)

        assert "Content must be a string or bytes" in str(exc_info.value)

    def test_parse_malformed_yaml_raises_value_error(self, parser):
        """Test that malformed YAML raises a clear ValueError instead of crashing."""
        malformed = "name: CI\non: [push\njobs: {broken"

        with pytest.raises(ValueError) as exc_info:
            parser.parse(malformed)

        assert "Invalid workflow YAML" in str(exc_info.value)

    def test_parse_non_mapping_yaml_raises_value_error(self, parser):
        """Test that YAML that isn't a mapping (e.g. a bare list) raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            parser.parse("- just\n- a\n- list\n")

        assert "Workflow content must be a YAML mapping" in str(exc_info.value)

    def test_text_summary_includes_jobs_and_actions(self, parser):
        """Test that the flattened text summary mentions jobs and actions used."""
        result = parser.parse(SAMPLE_WORKFLOW_YAML)

        assert "build-and-push" in result.text
        assert "docker/build-push-action@v5" in result.text
