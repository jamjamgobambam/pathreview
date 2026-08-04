"""Repository file-tree analyzer."""

from pathlib import PurePosixPath

import structlog

from .base import BaseTool, ToolResult

logger = structlog.get_logger()


class RepoAnalyzer(BaseTool):
    """Analyze repository file paths for engineering signals."""

    name = "repo_analyzer"
    description = "Analyze repository file paths for test coverage signals"

    def execute(self, input_data: dict) -> ToolResult:
        """Analyze repository files for test signals.

        Args:
            input_data: Must contain 'files' (list of file paths)

        Returns:
            ToolResult with has_tests boolean
        """
        files = input_data.get("files", [])

        if not files:
            logger.warning("repo_analyzer_no_files")
            return ToolResult(success=True, data={"has_tests": False})

        try:
            has_tests = self._has_tests(files)
            return ToolResult(success=True, data={"has_tests": has_tests})
        except Exception as e:
            logger.error("repo_analyzer_error", error=str(e))
            return ToolResult(success=False, data={}, error=str(e))

    @staticmethod
    def _has_tests(files: list[str]) -> bool:
        """Return True when repository file paths indicate automated tests."""
        for filepath in files:
            normalized = filepath.replace("\\", "/").strip("/")
            if not normalized:
                continue

            path = PurePosixPath(normalized)
            parts = [part.lower() for part in path.parts]
            filename = parts[-1] if parts else ""

            if any(segment in {"test", "tests"} for segment in parts[:-1]):
                return True

            if filename == "pytest.ini":
                return True

            if filename.startswith("test_") and filename.endswith(".py"):
                return True

        return False
