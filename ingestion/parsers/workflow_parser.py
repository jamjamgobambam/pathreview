import structlog
import yaml  # type: ignore

from .base import BaseParser, ParseResult
from .skill_extractor import SkillExtractor

logger = structlog.get_logger()

_DEPLOY_TRIGGERS = {"release", "workflow_dispatch"}
_DEPLOY_BRANCHES = {"main", "master", "production", "prod"}


class WorkflowParser(BaseParser):
    """Parser for GitHub Actions workflow files."""

    def parse(self, content: str | bytes) -> ParseResult:
        """
        Parse GitHub Actions workflow YAML and extract skills.

        Args:
            content: Workflow YAML content (string or bytes)

        Returns:
            ParseResult with extracted text, metadata, and detected skills

        Raises:
            ValueError: If YAML is malformed or missing required structure
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")

        try:
            workflow = yaml.safe_load(content) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid workflow YAML: {str(e)}") from e

        if not isinstance(workflow, dict):
            workflow = {}

        # Extract workflow metadata
        workflow_name = workflow.get("name", "unnamed") or "unnamed"

        # Extract trigger events
        trigger_events = self._extract_triggers(workflow)

        # Extract jobs and steps
        jobs = workflow.get("jobs") or {}
        if not isinstance(jobs, dict):
            jobs = {}

        job_count = len(jobs)
        step_count = 0
        step_names = []
        text_parts = [f"Workflow: {workflow_name}"]

        if trigger_events:
            text_parts.append(f"Triggers: {', '.join(trigger_events)}")

        for job_name, job in jobs.items():
            if not isinstance(job, dict):
                continue

            text_parts.append(f"Job: {job_name}")

            steps = job.get("steps") or []
            if not isinstance(steps, list):
                continue

            for step in steps:
                if not isinstance(step, dict):
                    continue

                step_count += 1

                # Extract step name
                step_name = step.get("name")
                if step_name:
                    step_names.append(str(step_name))

                try:
                    # Extract 'uses' actions
                    if "uses" in step:
                        uses_action = step["uses"]
                        text_parts.append(f"uses: {uses_action}")

                    # Extract 'run' commands
                    if "run" in step:
                        run_command = step["run"]
                        text_parts.append(f"run: {run_command}")
                except Exception:
                    logger.warning("Failed to parse workflow step", job=job_name)

        # Detect if this is a deployment workflow
        has_deploy_step = self._is_deploy_workflow(trigger_events, workflow)

        summary_text = "\n".join(text_parts)

        # Extract skills from the assembled workflow text
        skill_extractor = SkillExtractor()
        detected_skills = skill_extractor.extract_skills(summary_text, filename="workflow.yml")

        # Extract skill names and always infer GitHub Actions and CI/CD
        # The existence of a workflow file proves the developer has these skills
        all_skill_names = [s.name for s in detected_skills]

        if "GitHub Actions" not in all_skill_names:
            all_skill_names.append("GitHub Actions")

        if "CI/CD" not in all_skill_names:
            all_skill_names.append("CI/CD")

        # Build metadata
        ci_tools = [s.name for s in detected_skills if s.category == "Tool"]

        metadata = {
            "source_type": "workflow",
            "workflow_name": workflow_name,
            "trigger_events": trigger_events,
            "job_count": job_count,
            "step_count": step_count,
            "step_names": step_names,
            "detected_skills": all_skill_names,
            "ci_tools": ci_tools,
            "has_deploy_step": has_deploy_step,
        }

        logger.info(
            "Workflow parsed successfully",
            workflow_name=workflow_name,
            job_count=job_count,
            step_count=step_count,
            trigger_events=trigger_events,
            detected_skills=all_skill_names,
        )

        return ParseResult(
            text=summary_text,
            metadata=metadata,
            source_type="workflow",
        )

    def _extract_triggers(self, workflow: dict) -> list[str]:
        """Extract trigger events from workflow.

        Args:
            workflow: Parsed workflow dictionary

        Returns:
            List of trigger event names (e.g., ['push', 'pull_request'])
        """
        on = workflow.get("on") or workflow.get(True)  # YAML parses `on:` as True
        if not on:
            return []
        if isinstance(on, str):
            return [on]
        if isinstance(on, list):
            return [str(t) for t in on]
        if isinstance(on, dict):
            return sorted(on.keys())
        return []

    def _is_deploy_workflow(self, trigger_events: list[str], workflow: dict) -> bool:
        """Detect if workflow is a deployment workflow.

        Args:
            trigger_events: List of trigger event names from the workflow
            workflow: Parsed workflow dictionary

        Returns:
            True if workflow is a deployment workflow, False otherwise
        """
        # Check if triggered by deployment events
        for event in trigger_events:
            if event in _DEPLOY_TRIGGERS:
                return True

        # Check if it deploys to main/production branch
        on = workflow.get("on") or workflow.get(True)
        if isinstance(on, dict):
            push = on.get("push") or {}
            if isinstance(push, dict):
                branches = push.get("branches") or []
                for branch in branches:
                    if str(branch).lower() in _DEPLOY_BRANCHES:
                        return True
        return False
