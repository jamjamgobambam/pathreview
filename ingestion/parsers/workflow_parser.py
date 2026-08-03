import logging
from pathlib import Path

import yaml # type: ignore[import-untyped]

from .base import BaseParser, ParseResult

logger = logging.getLogger(__name__)


class WorkflowParser(BaseParser):
    """Parser for GitHub Actions workflow files."""

    def parse(self, content: str | bytes) -> ParseResult:
        """
        Parse workflow YAML content.

        Args:
            content: Either a repository path (str) or raw YAML text (str).
                     If a path is provided, discovers .github/workflows/*.yml files.

        Returns:
            ParseResult with extracted text and metadata
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8")

        # Heuristic: treat as filesystem path if no newlines and looks like a path
        if "\n" not in content and (content.startswith("/") or content.startswith(".")):
            return self._parse_from_path(Path(content))

        return self._parse_text(content)

    def _parse_from_path(self, repo_path: Path) -> ParseResult:
        """Discover and parse workflow files from a repository path."""
        workflows_dir = repo_path / ".github" / "workflows"
        workflow_files = list(workflows_dir.glob("*.yml"))

        if not workflow_files:
            return ParseResult(
                text="",
                metadata={
                    "source_type": "workflow",
                    "file_count": 0,
                    "workflow_names": [],
                },
                source_type="workflow",
            )

        texts = []
        workflow_names = []
        file_count = 0

        for file_path in workflow_files:
            try:
                raw_text = file_path.read_text(encoding="utf-8")
                file_count += 1

                if not raw_text.strip():
                    continue

                try:
                    data = yaml.safe_load(raw_text)
                except Exception as e:
                    logger.warning(f"Malformed YAML in {file_path.name}: {e}")
                    continue

                extracted = self._extract_workflow_text(data)
                if extracted:
                    texts.append(extracted)
                    workflow_names.append(file_path.name)

            except Exception as e:
                logger.warning(f"Error reading {file_path}: {e}")
                continue

        # Prepend "github actions" so SkillExtractor.TOOLS substring matching fires
        if texts:
            full_text = "github actions\n\n" + "\n\n".join(texts)
        else:
            full_text = ""

        return ParseResult(
            text=full_text,
            metadata={
                "source_type": "workflow",
                "file_count": file_count,
                "workflow_names": workflow_names,
            },
            source_type="workflow",
        )

    def _parse_text(self, text: str) -> ParseResult:
        """Parse raw workflow text that was already read."""
        if not text.strip():
            return ParseResult(
                text="",
                metadata={
                    "source_type": "workflow",
                    "file_count": 0,
                    "workflow_names": [],
                },
                source_type="workflow",
            )

        try:
            data = yaml.safe_load(text)
            extracted = self._extract_workflow_text(data)
            if extracted:
                extracted = "github actions\n\n" + extracted
        except Exception:
            extracted = text

        return ParseResult(
            text=extracted or text,
            metadata={
                "source_type": "workflow",
                "file_count": 1,
                "workflow_names": ["inline"],
            },
            source_type="workflow",
        )

    def _extract_workflow_text(self, data: dict | None) -> str:
        """Extract relevant strings from parsed YAML for skill detection."""
        if not data or not isinstance(data, dict):
            return ""

        parts = []

        workflow_name = data.get("name")
        if workflow_name and isinstance(workflow_name, str):
            parts.append(f"workflow: {workflow_name}")

        jobs = data.get("jobs", {})
        if isinstance(jobs, dict):
            for job_name, job_data in jobs.items():
                if not isinstance(job_data, dict):
                    continue

                parts.append(f"job: {job_name}")

                runs_on = job_data.get("runs-on")
                if runs_on:
                    if isinstance(runs_on, str):
                        parts.append(f"runs-on: {runs_on}")
                    elif isinstance(runs_on, list):
                        parts.append(f"runs-on: {', '.join(runs_on)}")

                steps = job_data.get("steps", [])
                if isinstance(steps, list):
                    for step in steps:
                        if not isinstance(step, dict):
                            continue

                        step_name = step.get("name")
                        if step_name and isinstance(step_name, str):
                            parts.append(f"step: {step_name}")

                        uses = step.get("uses")
                        if uses and isinstance(uses, str):
                            parts.append(f"uses: {uses}")

                        run_cmd = step.get("run")
                        if run_cmd and isinstance(run_cmd, str):
                            parts.append(f"run: {run_cmd}")

        return "\n".join(parts)
