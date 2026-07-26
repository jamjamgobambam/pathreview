import yaml

from .base import BaseParser, ParseResult


class WorkflowParser(BaseParser):
    """Parser for GitHub Actions workflow files (.github/workflows/*.yml)."""

    def parse(self, content: str | bytes) -> ParseResult:
        """
        Parse a GitHub Actions workflow from YAML content.

        Args:
            content: Workflow YAML string or bytes

        Returns:
            ParseResult with structured workflow data and a text summary

        Raises:
            ValueError: If content is not a valid string/bytes, or not valid
                workflow YAML
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        elif not isinstance(content, str):
            raise ValueError("Content must be a string or bytes")

        try:
            workflow = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid workflow YAML: {e}") from e

        if not isinstance(workflow, dict):
            raise ValueError("Workflow content must be a YAML mapping")

        name = workflow.get("name") or "Unnamed workflow"
        triggers = self._extract_triggers(workflow)
        jobs = self._extract_jobs(workflow)
        actions_used = sorted(
            {step["uses"] for job in jobs for step in job["steps"] if step["uses"]}
        )
        run_commands = [step["run"] for job in jobs for step in job["steps"] if step["run"]]

        metadata = {
            "source_type": "workflow",
            "workflow_name": name,
            "triggers": triggers,
            "jobs": jobs,
            "actions_used": actions_used,
            "run_commands": run_commands,
            "job_count": len(jobs),
        }

        return ParseResult(
            text=self._build_summary(name, triggers, jobs),
            metadata=metadata,
            source_type="workflow",
        )

    def _extract_triggers(self, workflow: dict) -> list[str]:
        """Normalize the `on:` key into a flat list of trigger names.

        PyYAML's default (1.1) resolver parses the bare `on` key as the
        boolean `True` rather than the string "on", so both are checked here.
        """
        on = workflow.get("on", workflow.get(True))
        if isinstance(on, str):
            return [on]
        if isinstance(on, list):
            return [str(trigger) for trigger in on]
        if isinstance(on, dict):
            return list(on.keys())
        return []

    def _extract_jobs(self, workflow: dict) -> list[dict]:
        """Extract job name, runner, dependencies, and steps for each job."""
        jobs_data = workflow.get("jobs") or {}
        jobs = []
        for job_name, job_def in jobs_data.items():
            if not isinstance(job_def, dict):
                continue

            needs = job_def.get("needs") or []
            if isinstance(needs, str):
                needs = [needs]

            jobs.append(
                {
                    "name": job_name,
                    "runs_on": job_def.get("runs-on"),
                    "needs": needs,
                    "steps": self._extract_steps(job_def.get("steps") or []),
                }
            )
        return jobs

    def _extract_steps(self, steps_data: list) -> list[dict]:
        """Extract the `uses:` action and `run:` command from each step."""
        steps = []
        for step in steps_data:
            if not isinstance(step, dict):
                continue
            steps.append(
                {
                    "name": step.get("name"),
                    "uses": step.get("uses"),
                    "run": step.get("run"),
                }
            )
        return steps

    def _build_summary(self, name: str, triggers: list[str], jobs: list[dict]) -> str:
        """Build a flattened text summary of the workflow for embedding."""
        lines = [
            f"Workflow: {name}",
            f"Triggers: {', '.join(triggers) if triggers else 'none'}",
        ]
        for job in jobs:
            lines.append(f"Job: {job['name']} (runs-on: {job['runs_on'] or 'unknown'})")
            if job["needs"]:
                lines.append(f"  Needs: {', '.join(job['needs'])}")
            for step in job["steps"]:
                if step["uses"]:
                    lines.append(f"  Uses: {step['uses']}")
                if step["run"]:
                    lines.append(f"  Run: {step['run']}")
        return "\n".join(lines)
