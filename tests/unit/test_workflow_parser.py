import pytest

from ingestion.parsers.base import ParseResult
from ingestion.parsers.workflow_parser import WorkflowParser


@pytest.mark.unit
class TestWorkflowParser:
    """Unit tests for WorkflowParser."""

    @pytest.fixture
    def parser(self) -> WorkflowParser:
        """Fixture to provide a WorkflowParser instance."""
        return WorkflowParser()

    def test_parse_returns_parse_result(self, parser: WorkflowParser) -> None:
        """Test that parse returns a ParseResult instance."""
        workflow_yaml = """
name: Test
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo test
"""
        result = parser.parse(workflow_yaml)
        assert isinstance(result, ParseResult)

    def test_parse_valid_workflow_yaml(self, parser: WorkflowParser) -> None:
        """Test parsing a valid GitHub Actions workflow."""
        workflow_yaml = """
name: CI Pipeline
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/
"""
        result = parser.parse(workflow_yaml)

        assert result.source_type == "workflow"
        assert result.metadata["workflow_name"] == "CI Pipeline"
        assert result.metadata["job_count"] == 1
        assert result.metadata["step_count"] == 4
        assert "push" in result.metadata["trigger_events"]
        assert "pull_request" in result.metadata["trigger_events"]
        assert "Checkout" in result.metadata["step_names"]
        assert "Workflow: CI Pipeline" in result.text
        assert "uses: actions/checkout@v3" in result.text
        assert "run: pip install" in result.text
        assert "run: pytest" in result.text

    def test_source_type_is_workflow(self, parser: WorkflowParser) -> None:
        """Test that source_type is set to 'workflow'."""
        workflow_yaml = """
name: Test
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo test
"""
        result = parser.parse(workflow_yaml)
        assert result.source_type == "workflow"
        assert result.metadata["source_type"] == "workflow"

    def test_workflow_name_extracted(self, parser: WorkflowParser) -> None:
        """Test that workflow name is correctly extracted."""
        workflow_yaml = """
name: My Workflow
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo test
"""
        result = parser.parse(workflow_yaml)
        assert result.metadata["workflow_name"] == "My Workflow"

    def test_parse_extracts_skills(self, parser: WorkflowParser) -> None:
        """Test that skills are extracted and stored in metadata."""
        workflow_yaml = """
name: Docker Build
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: docker/build-push-action@v4
      - run: terraform plan
"""
        result = parser.parse(workflow_yaml)

        assert "detected_skills" in result.metadata
        assert "ci_tools" in result.metadata

        # Check for expected tools
        detected_skill_names = [s.lower() for s in result.metadata["detected_skills"]]
        assert "docker" in detected_skill_names
        assert "terraform" in detected_skill_names

    def test_trigger_events_extracted(self, parser: WorkflowParser) -> None:
        """Test that trigger events are correctly extracted."""
        workflow_yaml = """
name: Multi-Trigger
on: [push, pull_request, schedule]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo test
"""
        result = parser.parse(workflow_yaml)
        assert "push" in result.metadata["trigger_events"]
        assert "pull_request" in result.metadata["trigger_events"]
        assert "schedule" in result.metadata["trigger_events"]

    def test_job_and_step_counts(self, parser: WorkflowParser) -> None:
        """Test that job and step counts are accurate."""
        workflow_yaml = """
name: Multi-Job
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: pytest tests/
      - run: coverage report
  build:
    runs-on: ubuntu-latest
    steps:
      - run: docker build .
"""
        result = parser.parse(workflow_yaml)
        assert result.metadata["job_count"] == 2
        assert result.metadata["step_count"] == 3

    def test_parse_multiple_jobs(self, parser: WorkflowParser) -> None:
        """Test parsing workflow with multiple jobs."""
        workflow_yaml = """
name: Multi-Job Workflow
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: pytest tests/
  deploy:
    runs-on: ubuntu-latest
    steps:
      - run: kubectl deploy
      - run: ansible-playbook site.yml
"""
        result = parser.parse(workflow_yaml)

        assert "Job: test" in result.text
        assert "Job: deploy" in result.text
        assert "run: pytest" in result.text
        assert "run: kubectl" in result.text
        assert "run: ansible-playbook" in result.text

    def test_parse_workflow_with_both_uses_and_run(self, parser: WorkflowParser) -> None:
        """Test workflow with both 'uses' and 'run' commands."""
        workflow_yaml = """
name: Mixed Steps
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: docker/login-action@v2
      - run: docker build -t myapp:latest .
      - uses: docker/build-push-action@v4
      - run: docker push myapp:latest
"""
        result = parser.parse(workflow_yaml)

        detected_skill_names = [s.lower() for s in result.metadata["detected_skills"]]
        ci_tools_lower = [t.lower() for t in result.metadata["ci_tools"]]
        assert "docker" in detected_skill_names
        assert "docker" in ci_tools_lower

    def test_github_actions_always_detected_when_uses_present(self, parser: WorkflowParser) -> None:
        """Test that GitHub Actions is detected when uses: actions/* is present."""
        workflow_yaml = """
name: GA Test
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
"""
        result = parser.parse(workflow_yaml)
        assert "GitHub Actions" in result.metadata["detected_skills"]

    def test_cicd_detected_when_triggers_present(self, parser: WorkflowParser) -> None:
        """Test that CI/CD is detected when workflow has triggers."""
        workflow_yaml = """
name: CI Test
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo test
"""
        result = parser.parse(workflow_yaml)
        assert "CI/CD" in result.metadata["detected_skills"]

    def test_parse_malformed_yaml_raises_error(self, parser: WorkflowParser) -> None:
        """Test that malformed YAML raises ValueError."""
        malformed_yaml = """
name: Bad YAML
jobs: [unclosed bracket
"""
        with pytest.raises(ValueError, match="Invalid workflow YAML"):
            parser.parse(malformed_yaml)

    def test_parse_missing_jobs_key(self, parser: WorkflowParser) -> None:
        """Test workflow without 'jobs' key (valid but empty)."""
        workflow_yaml = """
name: No Jobs
on: push
"""
        result = parser.parse(workflow_yaml)

        assert result.source_type == "workflow"
        assert "Workflow: No Jobs" in result.text
        assert result.metadata["workflow_name"] == "No Jobs"

    def test_parse_empty_jobs(self, parser: WorkflowParser) -> None:
        """Test workflow with empty jobs dict."""
        workflow_yaml = """
name: Empty Jobs
on: push
jobs: {}
"""
        result = parser.parse(workflow_yaml)

        assert result.source_type == "workflow"
        assert "Workflow: Empty Jobs" in result.text

    def test_empty_workflow_no_crash(self, parser: WorkflowParser) -> None:
        """Test that empty workflows don't crash and metadata is sensible."""
        workflow_yaml = """
on: push
jobs: {}
"""
        result = parser.parse(workflow_yaml)
        assert result.metadata["job_count"] == 0
        assert result.metadata["step_count"] == 0
        # No steps means no tool-specific skills
        tools_to_check = ["docker", "pytest", "kubernetes"]
        tool_skills = [
            s.lower() for s in result.metadata["detected_skills"] if s.lower() in tools_to_check
        ]
        assert len(tool_skills) == 0

    def test_empty_workflow_name_fallback(self, parser: WorkflowParser) -> None:
        """Test that missing workflow name uses fallback."""
        workflow_yaml = """
on: push
jobs: {}
"""
        result = parser.parse(workflow_yaml)
        # Should have a fallback name, not None or empty string
        assert result.metadata["workflow_name"] in ["unnamed", "unknown"]

    def test_parse_workflow_bytes_input(self, parser: WorkflowParser) -> None:
        """Test parsing workflow from bytes."""
        workflow_yaml = b"""
name: Byte Input
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: pytest
"""
        result = parser.parse(workflow_yaml)

        assert result.source_type == "workflow"
        assert "Workflow: Byte Input" in result.text

    def test_text_contains_skills(self, parser: WorkflowParser) -> None:
        """Test that detected skills appear in the result text."""
        workflow_yaml = """
name: Text Test
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: docker/build-push-action@v4
      - run: pytest tests/
"""
        result = parser.parse(workflow_yaml)
        # Skills should be mentioned in the assembled text
        assert "docker" in result.text.lower() or "Docker" in result.text
        assert "pytest" in result.text.lower() or "Pytest" in result.text

    def test_text_contains_workflow_name(self, parser: WorkflowParser) -> None:
        """Test that workflow name appears in the result text."""
        workflow_yaml = """
name: Named Workflow
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo test
"""
        result = parser.parse(workflow_yaml)
        assert "Named Workflow" in result.text

    def test_aws_action_infers_aws_and_github_actions(self, parser: WorkflowParser) -> None:
        """Test that AWS actions infer both AWS and GitHub Actions skills."""
        workflow_yaml = """
name: Deploy AWS
on: push
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: aws-actions/configure-aws-credentials@v2
      - run: aws s3 sync . s3://bucket
"""
        result = parser.parse(workflow_yaml)
        skills = result.metadata["detected_skills"]
        assert "AWS" in skills
        assert "GitHub Actions" in skills

    def test_parse_realistic_ci_cd_workflow(self, parser: WorkflowParser) -> None:
        """Test parsing a realistic CI/CD workflow with multiple tools."""
        workflow_yaml = """
name: Full CI/CD Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: |
          pip install -r requirements.txt
          pytest tests/ --cov=src/
      - uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: docker/setup-buildx-action@v2
      - uses: docker/build-push-action@v4
        with:
          context: .
          push: true

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: azure/setup-kubectl@v3
      - run: |
          kubectl set image deployment/app app=app:latest
          kubectl rollout status deployment/app
      - run: |
          terraform init
          terraform apply -auto-approve
      - run: |
          ansible-playbook site.yml
"""
        result = parser.parse(workflow_yaml)

        # Verify structure
        assert result.source_type == "workflow"
        assert result.metadata["workflow_name"] == "Full CI/CD Pipeline"

        # Verify jobs are extracted
        assert "Job: test" in result.text
        assert "Job: build" in result.text
        assert "Job: deploy" in result.text

        # Verify skills are detected
        detected_skill_names = [s.lower() for s in result.metadata["detected_skills"]]
        assert "python" in detected_skill_names
        assert "docker" in detected_skill_names
        assert "kubernetes" in detected_skill_names
        assert "terraform" in detected_skill_names
        assert "ansible" in detected_skill_names

        # Verify CI tools are in metadata
        ci_tools_lower = [t.lower() for t in result.metadata["ci_tools"]]
        assert "docker" in ci_tools_lower
        assert "kubernetes" in ci_tools_lower

    def test_metadata_structure(self, parser: WorkflowParser) -> None:
        """Test that metadata has the required structure."""
        workflow_yaml = """
name: Test Metadata
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Test step
        run: echo test
"""
        result = parser.parse(workflow_yaml)

        # Check metadata keys
        assert "source_type" in result.metadata
        assert "workflow_name" in result.metadata
        assert "trigger_events" in result.metadata
        assert "job_count" in result.metadata
        assert "step_count" in result.metadata
        assert "step_names" in result.metadata
        assert "detected_skills" in result.metadata
        assert "ci_tools" in result.metadata
        assert "has_deploy_step" in result.metadata

        # Check values
        assert result.metadata["source_type"] == "workflow"
        assert result.metadata["workflow_name"] == "Test Metadata"
        assert isinstance(result.metadata["trigger_events"], list)
        assert isinstance(result.metadata["job_count"], int)
        assert isinstance(result.metadata["step_count"], int)
        assert isinstance(result.metadata["step_names"], list)
        assert isinstance(result.metadata["detected_skills"], list)
        assert isinstance(result.metadata["ci_tools"], list)
        assert isinstance(result.metadata["has_deploy_step"], bool)

    def test_parse_workflow_with_special_characters_in_steps(self, parser: WorkflowParser) -> None:
        """Test workflow with special characters in step commands."""
        workflow_yaml = r"""
name: Special Chars
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "Testing with quotes and $VARS"
          grep -r "pattern" tests/ || true
"""
        result = parser.parse(workflow_yaml)

        assert result.source_type == "workflow"
        assert "run:" in result.text

    def test_deploy_workflow_detection_by_event(self, parser: WorkflowParser) -> None:
        """Test detection of deployment workflow by trigger event."""
        workflow_yaml = """
name: Deploy
on: release
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - run: kubectl deploy
"""
        result = parser.parse(workflow_yaml)

        assert result.metadata["has_deploy_step"] is True
        assert "release" in result.metadata["trigger_events"]

    def test_has_deploy_step_false_for_non_deploy(self, parser: WorkflowParser) -> None:
        """Test that non-deploy workflows have has_deploy_step=False."""
        workflow_yaml = """
name: CI Pipeline
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: pytest
"""
        result = parser.parse(workflow_yaml)
        assert result.metadata["has_deploy_step"] is False

    def test_deploy_workflow_detection_by_branch(self, parser: WorkflowParser) -> None:
        """Test detection of deployment workflow by target branch."""
        workflow_yaml = """
name: Deploy to Prod
on:
  push:
    branches: [main, production]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - run: terraform apply
"""
        result = parser.parse(workflow_yaml)

        assert result.metadata["has_deploy_step"] is True
        assert "push" in result.metadata["trigger_events"]

    def test_kubernetes_detected_from_kubectl(self, parser: WorkflowParser) -> None:
        """Test that Kubernetes is detected when kubectl is used."""
        workflow_yaml = """
name: K8s Deploy
on: release
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: azure/setup-kubectl@v3
      - run: kubectl apply -f k8s/
"""
        result = parser.parse(workflow_yaml)
        assert "Kubernetes" in result.metadata["detected_skills"]

    def test_step_names_extraction(self, parser: WorkflowParser) -> None:
        """Test that step names are extracted."""
        workflow_yaml = """
name: Named Steps
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      - name: Run unit tests
        run: pytest tests/
      - name: Generate coverage report
        run: coverage report
"""
        result = parser.parse(workflow_yaml)

        assert "Checkout code" in result.metadata["step_names"]
        assert "Run unit tests" in result.metadata["step_names"]
        assert "Generate coverage report" in result.metadata["step_names"]
        assert result.metadata["step_count"] == 3

    def test_trigger_events_extraction(self, parser: WorkflowParser) -> None:
        """Test extraction of trigger events."""
        workflow_yaml = """
name: Multi-Trigger
on: [push, pull_request, schedule]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo test
"""
        result = parser.parse(workflow_yaml)

        assert "push" in result.metadata["trigger_events"]
        assert "pull_request" in result.metadata["trigger_events"]
        assert "schedule" in result.metadata["trigger_events"]
        assert "Triggers:" in result.text
