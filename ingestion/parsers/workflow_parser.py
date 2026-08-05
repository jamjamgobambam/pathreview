import yaml

from .base import BaseParser, ParseResult
from .skill_extractor import SkillExtractor


class WorkflowParser(BaseParser):
    """Parser for GitHub Actions workflow files (``.github/workflows/*.yml``).

    Detects CI/CD and DevOps skills structurally from the workflow's triggers,
    jobs, and steps (GitHub Actions, Docker, pytest, deployment) and threads them
    into the result as authoritative labels. It also reuses the existing
    :class:`SkillExtractor` on the generated summary for supplementary signal,
    stored separately under ``metadata["extracted_skills"]``.
    """

    def parse(self, content: str | bytes) -> ParseResult:
        """Parse a GitHub Actions workflow file.

        Args:
            content: Workflow YAML as a string or UTF-8 bytes.

        Returns:
            A :class:`ParseResult` with ``source_type="workflow"``, a
            human-readable ``text`` summary suitable for embedding, and
            ``metadata`` carrying triggers, job info, actions used, boolean skill
            flags, and the detected skills.

        Raises:
            ValueError: If ``content`` is not ``str``/``bytes``, or is not valid
                (single-document) YAML.
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        elif not isinstance(content, str):
            raise ValueError("Content must be a string or bytes")

        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid workflow YAML: {exc}") from exc

        # Valid YAML that is not a mapping (empty file, bare scalar, top-level
        # list) is not a workflow; treat it as an empty document rather than raise.
        if not isinstance(data, dict):
            data = {}

        workflow_name = self._as_str(data.get("name")) or "unnamed"
        triggers = self._extract_triggers(data)
        jobs = self._extract_jobs(data)
        actions_used = self._collect_uses(jobs)
        run_commands = self._collect_runs(jobs)

        # Structural skill detection (authoritative). A file with triggers or jobs
        # is by definition a GitHub Actions workflow.
        haystack = " ".join(actions_used + run_commands + list(jobs.keys())).lower()
        has_docker = "docker" in haystack
        runs_pytest = "pytest" in haystack
        has_deployment = "deploy" in haystack or "deployment" in triggers

        skills: list[str] = []
        if triggers or jobs:
            skills.append("GitHub Actions")
        if has_docker:
            skills.append("Docker")
        if runs_pytest:
            skills.append("pytest")
        if has_deployment:
            skills.append("deployment")

        text = self._build_summary(
            workflow_name, triggers, jobs, actions_used, run_commands, skills
        )

        # Reuse SkillExtractor for supplementary signal (issue #14). This is not
        # load-bearing: the structural labels above are authoritative.
        extracted = [d.name for d in SkillExtractor().extract_skills(text)]

        metadata = {
            "source_type": "workflow",
            "workflow_name": workflow_name,
            "triggers": ", ".join(triggers),
            "job_count": len(jobs),
            "job_names": ", ".join(jobs.keys()),
            "actions_used": ", ".join(actions_used),
            "has_docker": has_docker,
            "runs_pytest": runs_pytest,
            "has_deployment": has_deployment,
            "skills": ", ".join(skills),
            "extracted_skills": ", ".join(extracted),
        }

        return ParseResult(
            text=text,
            metadata=metadata,
            source_type="workflow",
        )

    def _extract_triggers(self, data: dict) -> list[str]:
        """Extract trigger event names from the ``on:`` key.

        PyYAML resolves an unquoted ``on`` key to the boolean ``True`` (YAML 1.1),
        so we look under both ``"on"`` and ``True``.
        """
        on_value = data.get("on")
        if on_value is None:
            on_value = data.get(True)

        if isinstance(on_value, str):
            return [on_value]
        if isinstance(on_value, list):
            return [s for s in (self._as_str(v) for v in on_value) if s]
        if isinstance(on_value, dict):
            return [s for s in (self._as_str(k) for k in on_value) if s]
        return []

    def _extract_jobs(self, data: dict) -> dict[str, dict]:
        """Return a mapping of job name to its (dict) configuration."""
        jobs_value = data.get("jobs")
        if not isinstance(jobs_value, dict):
            return {}
        return {
            self._as_str(name): (config if isinstance(config, dict) else {})
            for name, config in jobs_value.items()
        }

    def _collect_uses(self, jobs: dict[str, dict]) -> list[str]:
        """Collect every ``uses:`` value (step-level and reusable job-level)."""
        uses: list[str] = []
        for config in jobs.values():
            job_uses = config.get("uses")
            if isinstance(job_uses, str):
                uses.append(job_uses)
            for step in self._steps(config):
                step_uses = step.get("uses")
                if isinstance(step_uses, str):
                    uses.append(step_uses)
        return uses

    def _collect_runs(self, jobs: dict[str, dict]) -> list[str]:
        """Collect every ``run:`` command across all job steps."""
        runs: list[str] = []
        for config in jobs.values():
            for step in self._steps(config):
                step_run = step.get("run")
                if isinstance(step_run, str):
                    runs.append(step_run)
        return runs

    def _steps(self, config: dict) -> list[dict]:
        """Return the list of step mappings for a job config."""
        steps = config.get("steps")
        if not isinstance(steps, list):
            return []
        return [s for s in steps if isinstance(s, dict)]

    def _build_summary(
        self,
        name: str,
        triggers: list[str],
        jobs: dict[str, dict],
        actions_used: list[str],
        run_commands: list[str],
        skills: list[str],
    ) -> str:
        """Build a human-readable, embeddable summary of the workflow."""
        lines = [f"Workflow file: {name}"]
        if skills:
            lines.append(f"Detected skills: {', '.join(skills)}")
        if triggers:
            lines.append(f"Triggers: {', '.join(triggers)}")
        if jobs:
            lines.append(f"Jobs ({len(jobs)}): {', '.join(jobs.keys())}")
            for job_name, config in jobs.items():
                runs_on = self._as_str(config.get("runs-on"))
                if runs_on:
                    lines.append(f"  Job '{job_name}' runs on {runs_on}")
        if actions_used:
            lines.append(f"Actions used: {', '.join(actions_used)}")
        if run_commands:
            lines.append("Commands:")
            lines.extend(f"  run: {cmd}" for cmd in run_commands)
        return "\n".join(lines)

    @staticmethod
    def _as_str(value: object) -> str:
        """Coerce a YAML scalar/key to a string ("" for ``None``)."""
        if value is None:
            return ""
        return str(value)
