import yaml

from .base import BaseParser, ParseResult


class WorkflowParser(BaseParser):
    """Parser for GitHub Actions workflow YAML files (.github/workflows/*.yml)."""

    def parse(self, content: str | bytes) -> ParseResult:
        """
        Parse a GitHub Actions workflow from YAML content.

        Args:
            content: Workflow YAML string or bytes

        Returns:
            ParseResult with extracted text and metadata

        Raises:
            ValueError: If content is not a valid string/bytes, or the YAML
                is malformed or does not define a top-level mapping.
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        elif not isinstance(content, str):
            raise ValueError("Content must be a string or bytes")

        try:
            workflow = yaml.safe_load(content)
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid workflow YAML: {exc}") from exc

        if workflow is None:
            workflow = {}
        if not isinstance(workflow, dict):
            raise ValueError("Workflow YAML must define a mapping at the top level")

        # PyYAML's YAML 1.1 resolver treats the unquoted `on:` key as the
        # boolean True, so the trigger config can land under either key.
        trigger_events = self._extract_triggers(workflow.get("on", workflow.get(True)))

        jobs = workflow.get("jobs")
        jobs = jobs if isinstance(jobs, dict) else {}
        job_names = [str(name) for name in jobs]
        actions_used, run_commands = self._extract_steps(jobs)

        text = self._build_text(
            name=workflow.get("name"),
            trigger_events=trigger_events,
            job_names=job_names,
            actions_used=actions_used,
            run_commands=run_commands,
        )

        metadata = {
            "source_type": "workflow",
            "job_count": len(job_names),
            "trigger_events": trigger_events,
            "actions_used": actions_used,
        }

        return ParseResult(text=text, metadata=metadata, source_type="workflow")

    def _extract_triggers(self, on_value: object) -> list[str]:
        """Normalize the `on:` trigger config into a list of event names."""
        if isinstance(on_value, str):
            return [on_value]
        if isinstance(on_value, list):
            return [str(event) for event in on_value]
        if isinstance(on_value, dict):
            return [str(event) for event in on_value]
        return []

    def _extract_steps(self, jobs: dict) -> tuple[list[str], list[str]]:
        """Collect `uses:` action references and `run:` commands across all jobs."""
        actions_used: list[str] = []
        run_commands: list[str] = []

        for job in jobs.values():
            if not isinstance(job, dict):
                continue
            steps = job.get("steps")
            if not isinstance(steps, list):
                continue
            for step in steps:
                if not isinstance(step, dict):
                    continue
                uses = step.get("uses")
                if isinstance(uses, str):
                    actions_used.append(uses)
                run = step.get("run")
                if isinstance(run, str):
                    run_commands.append(run)

        return actions_used, run_commands

    def _build_text(
        self,
        name: object,
        trigger_events: list[str],
        job_names: list[str],
        actions_used: list[str],
        run_commands: list[str],
    ) -> str:
        """Build a text summary suitable for skill extraction and embedding."""
        parts = [f"Workflow: {name if isinstance(name, str) else 'Unnamed workflow'}"]
        if trigger_events:
            parts.append(f"Triggers: {', '.join(trigger_events)}")
        if job_names:
            parts.append(f"Jobs: {', '.join(job_names)}")
        if actions_used:
            parts.append(f"Actions used: {', '.join(actions_used)}")
        if run_commands:
            parts.append("Run commands:\n" + "\n".join(run_commands))
        return "\n".join(parts)
