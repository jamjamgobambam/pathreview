"""Unit tests for WorkflowParser."""

from __future__ import annotations

import pytest

from ingestion.parsers.workflow_parser import WorkflowParser, _is_workflow_file


@pytest.mark.unit
class TestIsWorkflowFile:
    """Tests for the _is_workflow_file helper."""

    def test_standard_yml_path(self) -> None:
        assert _is_workflow_file(".github/workflows/ci.yml") is True

    def test_standard_yaml_extension(self) -> None:
        assert _is_workflow_file(".github/workflows/release.yaml") is True

    def test_nested_path(self) -> None:
        assert _is_workflow_file("repo/.github/workflows/deploy.yml") is True

    def test_non_workflow_yml(self) -> None:
        assert _is_workflow_file("docker-compose.yml") is False

    def test_non_workflow_in_other_dir(self) -> None:
        assert _is_workflow_file(".github/ISSUE_TEMPLATE/bug.yml") is False

    def test_none_filename(self) -> None:
        assert _is_workflow_file(None) is False


@pytest.mark.unit
class TestWorkflowParser:
    """Tests for WorkflowParser.parse()."""

    @pytest.fixture
    def parser(self) -> WorkflowParser:
        return WorkflowParser()

    # ------------------------------------------------------------------
    # Happy-path: canonical CI workflow
    # ------------------------------------------------------------------

    def test_always_detects_github_actions(self, parser: WorkflowParser) -> None:
        """Any workflow file should produce a GitHub Actions skill."""
        content = "name: CI\non: [push]\njobs:\n  build:\n    runs-on: ubuntu-latest\n"
        result = parser.parse(content, filename=".github/workflows/ci.yml")
        names = [s.name for s in result]
        assert "GitHub Actions" in names

    def test_github_actions_confidence_high(self, parser: WorkflowParser) -> None:
        content = "name: CI\non: [push]\n"
        result = parser.parse(content, filename=".github/workflows/ci.yml")
        gh = next(s for s in result if s.name == "GitHub Actions")
        assert gh.confidence >= 0.90

    def test_detects_pytest_from_run_step(self, parser: WorkflowParser) -> None:
        content = (
            "name: CI\n"
            "on: [push]\n"
            "jobs:\n"
            "  test:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "    - uses: actions/checkout@v4\n"
            "    - run: pytest tests/ -v\n"
        )
        result = parser.parse(content, filename=".github/workflows/ci.yml")
        names = [s.name for s in result]
        assert "pytest" in names

    def test_detects_docker_from_run_step(self, parser: WorkflowParser) -> None:
        content = (
            "name: Build\n"
            "on: [push]\n"
            "jobs:\n"
            "  build:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "    - run: docker build -t myapp .\n"
        )
        result = parser.parse(content, filename=".github/workflows/build.yml")
        names = [s.name for s in result]
        assert "Docker" in names

    def test_detects_setup_python_action(self, parser: WorkflowParser) -> None:
        content = (
            "name: CI\n"
            "on: [push]\n"
            "jobs:\n"
            "  test:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "    - uses: actions/setup-python@v5\n"
            "      with:\n"
            "        python-version: '3.11'\n"
        )
        result = parser.parse(content, filename=".github/workflows/ci.yml")
        names = [s.name for s in result]
        assert "Python" in names

    def test_detects_docker_build_push_action(self, parser: WorkflowParser) -> None:
        content = (
            "name: Publish\n"
            "on: [push]\n"
            "jobs:\n"
            "  publish:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "    - uses: docker/build-push-action@v5\n"
        )
        result = parser.parse(content, filename=".github/workflows/publish.yml")
        names = [s.name for s in result]
        assert "Docker" in names

    def test_detects_aws_credentials_action(self, parser: WorkflowParser) -> None:
        content = (
            "name: Deploy\n"
            "on: [push]\n"
            "jobs:\n"
            "  deploy:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "    - uses: aws-actions/configure-aws-credentials@v4\n"
        )
        result = parser.parse(content, filename=".github/workflows/deploy.yml")
        names = [s.name for s in result]
        assert "AWS" in names

    def test_detects_block_scalar_run(self, parser: WorkflowParser) -> None:
        """Block-style run steps (run: |) should also be parsed."""
        content = (
            "name: CI\n"
            "on: [push]\n"
            "jobs:\n"
            "  test:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "    - name: Run suite\n"
            "      run: |\n"
            "        pip install -e .[dev]\n"
            "        pytest tests/unit -v\n"
        )
        result = parser.parse(content, filename=".github/workflows/ci.yml")
        names = [s.name for s in result]
        assert "pytest" in names
        assert "Python" in names

    def test_multiple_skills_detected(self, parser: WorkflowParser) -> None:
        """A complex workflow can surface several skills at once."""
        content = (
            "name: Full\n"
            "on: [push]\n"
            "jobs:\n"
            "  build:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "    - uses: actions/checkout@v4\n"
            "    - uses: actions/setup-python@v5\n"
            "    - uses: docker/build-push-action@v5\n"
            "    - run: pytest\n"
            "    - run: kubectl apply -f manifests/\n"
        )
        result = parser.parse(content, filename=".github/workflows/full.yml")
        names = {s.name for s in result}
        assert "GitHub Actions" in names
        assert "Python" in names
        assert "Docker" in names
        assert "pytest" in names
        assert "Kubernetes" in names

    def test_results_sorted_by_confidence(self, parser: WorkflowParser) -> None:
        content = (
            "name: CI\n"
            "on: [push]\n"
            "jobs:\n"
            "  test:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "    - uses: actions/checkout@v4\n"
            "    - run: pytest\n"
        )
        result = parser.parse(content, filename=".github/workflows/ci.yml")
        confidences = [s.confidence for s in result]
        assert confidences == sorted(confidences, reverse=True)

    def test_skill_detection_has_evidence(self, parser: WorkflowParser) -> None:
        content = (
            "name: CI\non: [push]\n"
            "jobs:\n  test:\n    runs-on: ubuntu-latest\n"
            "    steps:\n    - uses: actions/checkout@v4\n"
        )
        result = parser.parse(content, filename=".github/workflows/ci.yml")
        for skill in result:
            assert isinstance(skill.evidence, list)
            assert len(skill.evidence) > 0

    def test_confidence_scores_bounded(self, parser: WorkflowParser) -> None:
        content = (
            "name: CI\non: [push]\n"
            "jobs:\n  test:\n    runs-on: ubuntu-latest\n"
            "    steps:\n    - uses: actions/checkout@v4\n"
            "    - run: pytest\n"
        )
        result = parser.parse(content, filename=".github/workflows/ci.yml")
        for skill in result:
            assert 0.0 <= skill.confidence <= 1.0

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_empty_content_returns_empty_list(self, parser: WorkflowParser) -> None:
        result = parser.parse("", filename=".github/workflows/ci.yml")
        assert result == []

    def test_whitespace_only_returns_empty_list(self, parser: WorkflowParser) -> None:
        result = parser.parse("   \n  \t  ", filename=".github/workflows/ci.yml")
        assert result == []

    def test_non_workflow_filename_returns_empty(self, parser: WorkflowParser) -> None:
        """A .yml file outside .github/workflows/ should not be parsed."""
        content = "name: CI\non: [push]\n"
        result = parser.parse(content, filename="docker-compose.yml")
        assert result == []

    def test_no_filename_parses_content(self, parser: WorkflowParser) -> None:
        """When no filename is provided the parser should still work."""
        content = (
            "name: CI\non: [push]\n" "jobs:\n  test:\n    steps:\n    - uses: actions/checkout@v4\n"
        )
        result = parser.parse(content)
        assert len(result) > 0

    def test_unknown_actions_are_ignored(self, parser: WorkflowParser) -> None:
        """Unrecognised ``uses:`` values should not crash."""
        content = (
            "name: CI\n"
            "on: [push]\n"
            "jobs:\n"
            "  test:\n"
            "    steps:\n"
            "    - uses: some-unknown-org/some-action@v1\n"
        )
        result = parser.parse(content, filename=".github/workflows/ci.yml")
        # Only GitHub Actions base signal should be present.
        assert all(s.name == "GitHub Actions" for s in result)

    def test_invalid_content_type_raises(self, parser: WorkflowParser) -> None:
        with pytest.raises(ValueError):
            parser.parse(b"binary content")  # type: ignore[arg-type]

    def test_duplicate_uses_merges_evidence(self, parser: WorkflowParser) -> None:
        """Repeated checkout actions should not produce duplicate skill entries."""
        content = (
            "name: CI\n"
            "on: [push]\n"
            "jobs:\n"
            "  a:\n    steps:\n    - uses: actions/checkout@v4\n"
            "  b:\n    steps:\n    - uses: actions/checkout@v4\n"
        )
        result = parser.parse(content, filename=".github/workflows/ci.yml")
        gh_entries = [s for s in result if s.name == "GitHub Actions"]
        assert len(gh_entries) == 1
