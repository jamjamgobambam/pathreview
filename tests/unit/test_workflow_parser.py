"""Tests for workflow_parser.py"""

import pytest

from ingestion.parsers.base import ParseResult
from ingestion.parsers.workflow_parser import WorkflowParser


@pytest.mark.unit
class TestWorkflowParser:
    """Test suite for WorkflowParser."""

    @pytest.fixture
    def parser(self):
        """Create a WorkflowParser instance."""
        return WorkflowParser()

    def test_parse_standard_workflow(self, parser, sample_workflow_yaml):
        """Test parsing a standard multi-job workflow."""
        result = parser.parse(sample_workflow_yaml)

        assert isinstance(result, ParseResult)
        assert result.source_type == "workflow"
        assert result.metadata["source_type"] == "workflow"
        assert "CI" in result.text
        assert result.metadata["job_count"] == 2

    def test_parse_extracts_trigger_events(self, parser, sample_workflow_yaml):
        """Test that trigger events are extracted despite the YAML 'on' gotcha."""
        result = parser.parse(sample_workflow_yaml)

        assert "push" in result.metadata["trigger_events"]
        assert "pull_request" in result.metadata["trigger_events"]

    def test_parse_extracts_job_names(self, parser, sample_workflow_yaml):
        """Test that job names appear in the parsed text."""
        result = parser.parse(sample_workflow_yaml)

        assert "test" in result.text
        assert "deploy" in result.text

    def test_parse_extracts_actions_used(self, parser, sample_workflow_yaml):
        """Test that 'uses:' action references are extracted."""
        result = parser.parse(sample_workflow_yaml)

        assert "actions/checkout@v4" in result.metadata["actions_used"]
        assert "actions/setup-python@v5" in result.metadata["actions_used"]
        assert "docker/build-push-action@v5" in result.metadata["actions_used"]

    def test_parse_extracts_run_commands(self, parser, sample_workflow_yaml):
        """Test that 'run:' commands are extracted into the text."""
        result = parser.parse(sample_workflow_yaml)

        assert "pytest" in result.text
        assert "./deploy.sh production" in result.text

    def test_parse_single_job_workflow(self, parser):
        """Test parsing a workflow with a single job and string trigger."""
        workflow = """
        name: Lint
        on: push
        jobs:
          lint:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
              - run: ruff check .
        """
        result = parser.parse(workflow)

        assert result.metadata["job_count"] == 1
        assert result.metadata["trigger_events"] == ["push"]

    def test_parse_list_style_triggers(self, parser):
        """Test parsing a workflow with 'on:' as a list rather than a mapping."""
        workflow = """
        name: Multi-trigger
        on: [push, pull_request]
        jobs:
          build:
            runs-on: ubuntu-latest
            steps:
              - run: echo build
        """
        result = parser.parse(workflow)

        assert result.metadata["trigger_events"] == ["push", "pull_request"]

    def test_parse_malformed_yaml_raises_value_error(self, parser):
        """Test that malformed YAML raises ValueError instead of crashing."""
        malformed = """
        name: Broken
        on: [push
        jobs:
        """
        with pytest.raises(ValueError):
            parser.parse(malformed)

    def test_parse_missing_jobs_key(self, parser):
        """Test a workflow with no 'jobs' key parses without crashing."""
        workflow = """
        name: No Jobs Yet
        on: push
        """
        result = parser.parse(workflow)

        assert result.metadata["job_count"] == 0
        assert result.metadata["actions_used"] == []

    def test_parse_job_with_no_steps(self, parser):
        """Test a job missing a 'steps' key does not crash the parser."""
        workflow = """
        name: Reusable
        on: push
        jobs:
          call-shared:
            uses: org/repo/.github/workflows/shared.yml@main
        """
        result = parser.parse(workflow)

        assert result.metadata["job_count"] == 1
        assert result.metadata["actions_used"] == []

    def test_parse_step_with_neither_uses_nor_run(self, parser):
        """Test a step missing both 'uses' and 'run' does not crash the parser."""
        workflow = """
        name: Weird Step
        on: push
        jobs:
          build:
            runs-on: ubuntu-latest
            steps:
              - name: Just a label
        """
        result = parser.parse(workflow)

        assert result.metadata["job_count"] == 1
        assert result.metadata["actions_used"] == []

    def test_parse_empty_yaml(self, parser):
        """Test parsing empty content returns an empty-but-valid result."""
        result = parser.parse("")

        assert isinstance(result, ParseResult)
        assert result.metadata["job_count"] == 0
        assert result.metadata["trigger_events"] == []
        assert result.source_type == "workflow"

    def test_parse_non_mapping_yaml_raises_value_error(self, parser):
        """Test that a top-level YAML list (not a mapping) raises ValueError."""
        with pytest.raises(ValueError):
            parser.parse("- just\n- a\n- list\n")

    def test_parse_bytes_input(self, parser):
        """Test parsing workflow content from bytes."""
        workflow_bytes = b"name: CI\non: push\njobs:\n  build:\n    steps:\n      - run: echo hi\n"
        result = parser.parse(workflow_bytes)

        assert isinstance(result, ParseResult)
        assert "CI" in result.text

    def test_parse_invalid_content_type(self, parser):
        """Test that an invalid content type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            parser.parse(12345)

        assert "Content must be a string or bytes" in str(exc_info.value)

    def test_metadata_structure(self, parser, sample_workflow_yaml):
        """Test that metadata has the required structure."""
        result = parser.parse(sample_workflow_yaml)

        assert "source_type" in result.metadata
        assert "job_count" in result.metadata
        assert "trigger_events" in result.metadata
        assert "actions_used" in result.metadata
        assert result.metadata["source_type"] == "workflow"
