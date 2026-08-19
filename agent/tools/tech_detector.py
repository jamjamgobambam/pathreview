"""Technology stack detector tool."""

from collections import Counter

import structlog

from .base import BaseTool, ToolResult

logger = structlog.get_logger()


class TechDetector(BaseTool):
    """Detect technology stack from repository files."""

    name = "tech_detector"
    description = "Detect technology stack from repository files"

    # File extension to language mapping
    EXT_TO_LANG = {
        ".py": "Python",
        ".ipynb": "Python",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".go": "Go",
        ".rs": "Rust",
        ".java": "Java",
        ".kt": "Kotlin",
        ".cs": "C#",
        ".cpp": "C++",
        ".c": "C",
        ".h": "C",
        ".rb": "Ruby",
        ".php": "PHP",
        ".swift": "Swift",
        ".scala": "Scala",
        ".r": "R",
        ".m": "Objective-C",
        ".groovy": "Groovy",
    }

    # Config file to language/framework mapping
    CONFIG_INDICATORS = {
        "package.json": ("Node.js", "JavaScript"),
        "package-lock.json": ("Node.js", "JavaScript"),
        "yarn.lock": ("Node.js", "JavaScript"),
        "requirements.txt": ("Python", "Python"),
        "setup.py": ("Python", "Python"),
        "Pipfile": ("Python", "Python"),
        "Gemfile": ("Ruby", "Ruby"),
        "Cargo.toml": ("Rust", "Rust"),
        "pom.xml": ("Java", "Java"),
        "build.gradle": ("Java", "Java"),
        "Dockerfile": ("Docker", "Infrastructure"),
        "docker-compose.yml": ("Docker", "Infrastructure"),
        ".github/workflows": ("GitHub Actions", "CI/CD"),
        "Makefile": ("Make", "Build"),
        "cmake": ("CMake", "Build"),
    }

    def execute(self, input_data: dict) -> ToolResult:
        """Detect tech stack from files.

        Args:
            input_data: Must contain 'files' (list of file paths)

        Returns:
            ToolResult with detected technologies
        """
        files = input_data.get("files", [])

        if not files:
            logger.warning("tech_detector_no_files")
            return ToolResult(
                success=True,
                data={
                    "primary_language": "Unknown",
                    "all_languages": [],
                    "frameworks": [],
                },
            )

        try:
            result = self._detect_tech(files)
            return ToolResult(success=True, data=result)

        except Exception as e:
            logger.error("tech_detector_error", error=str(e))
            return ToolResult(success=False, data={}, error=str(e))

    def _detect_tech(self, files: list[str]) -> dict:
        """Detect technologies from file list.

        Args:
            files: List of file paths

        Returns:
            Dict with detected languages and frameworks
        """
        filtered_files = [f for f in files if not self._should_skip_file(f)]

        language_counts: Counter[str] = Counter()
        first_seen: dict[str, int] = {}
        frameworks = set()

        # Detect by file extension
        for index, filepath in enumerate(filtered_files):
            normalized_path = filepath.lower()
            for ext, lang in self.EXT_TO_LANG.items():
                if normalized_path.endswith(ext):
                    language_counts[lang] += 1
                    first_seen.setdefault(lang, index)

        # Detect by config files
        for index, filepath in enumerate(filtered_files):
            normalized_path = filepath.lower()
            for config_file, (framework, lang) in self.CONFIG_INDICATORS.items():
                if normalized_path.endswith(config_file.lower()):
                    language_counts[lang] += 1
                    first_seen.setdefault(lang, index)
                    if framework not in ("Docker", "Infrastructure", "CI/CD", "Build"):
                        frameworks.add(framework)

        # Determine primary language (most common)
        primary = "Unknown"
        if language_counts:
            primary = min(
                language_counts,
                key=lambda lang: (-language_counts[lang], first_seen[lang], lang),
            )

        all_languages = sorted(language_counts)
        all_frameworks = sorted(frameworks)

        logger.info(
            "tech_detected",
            primary_lang=primary,
            languages_count=len(all_languages),
            frameworks_count=len(all_frameworks),
        )

        return {
            "primary_language": primary,
            "all_languages": all_languages,
            "frameworks": all_frameworks,
        }

    @staticmethod
    def _should_skip_file(filepath: str) -> bool:
        """Check if file should be skipped.

        Args:
            filepath: File path

        Returns:
            True if file should be skipped
        """
        skip_patterns = {
            "node_modules",
            "vendor",
            "dist",
            "build",
            ".git",
            "__pycache__",
            ".venv",
            "venv",
        }

        normalized_path = filepath.replace("\\", "/").lower()
        path_parts = [part for part in normalized_path.split("/") if part]

        return any(part in skip_patterns for part in path_parts)
