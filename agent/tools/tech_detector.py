"""Technology stack detector tool."""

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
            input_data: Must contain 'files' (list of file paths).

        Returns:
            ToolResult with detected technologies.
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

        except Exception as error:
            logger.error("tech_detector_error", error=str(error))
            return ToolResult(
                success=False,
                data={},
                error=str(error),
            )

    def _detect_tech(self, files: list[str]) -> dict:
        """Detect technologies from a file list.

        Args:
            files: List of file paths.

        Returns:
            Dictionary with detected languages and frameworks.
        """
        filtered_files = [filepath for filepath in files if not self._should_skip_file(filepath)]

        languages = set()
        frameworks = set()

        # Detect languages by file extension.
        for filepath in filtered_files:
            for extension, language in self.EXT_TO_LANG.items():
                if filepath.endswith(extension):
                    languages.add(language)

        # Detect languages and frameworks by configuration files.
        for filepath in filtered_files:
            for config_file, (framework, language) in self.CONFIG_INDICATORS.items():
                if filepath.endswith(config_file):
                    languages.add(language)

                    if framework not in (
                        "Docker",
                        "Infrastructure",
                        "CI/CD",
                        "Build",
                    ):
                        frameworks.add(framework)

        primary_language = "Unknown"

        if languages:
            primary_language = sorted(languages)[0]

        all_languages = sorted(languages)
        all_frameworks = sorted(frameworks)

        logger.info(
            "tech_detected",
            primary_lang=primary_language,
            languages_count=len(all_languages),
            frameworks_count=len(all_frameworks),
        )

        return {
            "primary_language": primary_language,
            "all_languages": all_languages,
            "frameworks": all_frameworks,
        }

    @staticmethod
    def _should_skip_file(filepath: str) -> bool:
        """Check whether a file is inside a vendored or generated directory.

        Args:
            filepath: Repository-relative or absolute file path.

        Returns:
            True if the file should be excluded from technology detection.
        """
        skip_directories = {
            "node_modules",
            "vendor",
            "dist",
            "build",
            ".git",
            "__pycache__",
            ".venv",
            "venv",
        }

        normalized_path = filepath.replace("\\", "/")
        path_parts = [part for part in normalized_path.split("/") if part]

        directory_parts = path_parts[:-1]

        return any(part in skip_directories for part in directory_parts)
