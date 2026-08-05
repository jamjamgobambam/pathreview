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

    # Directory names to exclude from language/framework detection.
    # Matched as whole path segments (not substrings), so this only
    # excludes an actual vendored/build directory anywhere in the path —
    # not a file or directory that merely contains one of these names
    # (e.g. "src/rebuild/main.py" is not skipped).
    SKIP_DIRECTORIES = {
        "node_modules",
        "vendor",
        "dist",
        "build",
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "target",
        ".next",
        ".nuxt",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".eggs",
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
        # Filter out vendor/build directories
        filtered_files = [f for f in files if not self._should_skip_file(f)]

        languages = set()
        frameworks = set()

        # Detect by file extension
        for filepath in filtered_files:
            for ext, lang in self.EXT_TO_LANG.items():
                if filepath.endswith(ext):
                    languages.add(lang)

        # Detect by config files
        for filepath in filtered_files:
            for config_file, (framework, lang) in self.CONFIG_INDICATORS.items():
                if filepath.endswith(config_file):
                    languages.add(lang)
                    if framework not in ("Docker", "Infrastructure", "CI/CD", "Build"):
                        frameworks.add(framework)

        # Determine primary language (most common)
        primary = "Unknown"
        if languages:
            lang_list = sorted(languages)
            primary = lang_list[0]

        all_languages = sorted(languages)
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

    @classmethod
    def _should_skip_file(cls, filepath: str) -> bool:
        """Check if file should be skipped.

        Matches directory names as whole path segments after normalizing
        separators, so it catches a vendored/build directory whether it's
        at the repo root or nested, and whether the path uses "/" or "\\"
        (see issue #150 — the previous substring-based check required a
        leading "/", which missed both of those cases).

        Args:
            filepath: File path

        Returns:
            True if file should be skipped
        """
        normalized = filepath.replace("\\", "/")
        # Only check directory segments, not the filename itself, so a
        # file literally named e.g. "build" isn't mistaken for the
        # "build/" directory.
        directory_segments = normalized.split("/")[:-1]

        return any(
            segment in cls.SKIP_DIRECTORIES or segment.endswith(".egg-info")
            for segment in directory_segments
        )
