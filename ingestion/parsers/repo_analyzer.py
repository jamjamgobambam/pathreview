from datetime import datetime

from .base import BaseParser, ParseResult


class RepoAnalyzer(BaseParser):
    """Analyzer for GitHub repository metadata."""

    # File extensions for language detection
    LANGUAGE_EXTENSIONS = {
        "py": "Python",
        "js": "JavaScript",
        "ts": "TypeScript",
        "jsx": "JavaScript",
        "tsx": "TypeScript",
        "java": "Java",
        "cs": "C#",
        "cpp": "C++",
        "c": "C",
        "go": "Go",
        "rs": "Rust",
        "rb": "Ruby",
        "php": "PHP",
        "swift": "Swift",
        "kt": "Kotlin",
        "scala": "Scala",
    }

    def parse(self, content: str | bytes) -> ParseResult:
        """
        Analyze GitHub repository metadata.

        Args:
            content: Repository metadata dict (passed as JSON-serializable dict or bytes)

        Returns:
            ParseResult with analyzed repo metadata
        """
        if isinstance(content, bytes):
            import json
            repo_data = json.loads(content.decode("utf-8"))
        elif isinstance(content, dict):
            repo_data = content
        elif isinstance(content, str):
            import json
            repo_data = json.loads(content)
        else:
            raise ValueError("Content must be a dict, JSON string, or JSON bytes")

        # Extract basic metrics
        star_count = repo_data.get("stargazers_count", 0)
        fork_count = repo_data.get("forks_count", 0)
        open_issues_count = repo_data.get("open_issues_count", 0)

        # Check for README
        has_readme = bool(repo_data.get("readme_content"))

        # Detect primary language
        primary_language = repo_data.get("language", "Unknown")

        # Check for CI/CD
        has_ci = self._detect_ci(repo_data)

        # Check for tests
        has_tests = self._detect_tests(repo_data)

        # Extract last commit date
        last_commit_date = repo_data.get("pushed_at", None)

        # Detect tech stack
        tech_stack = self._detect_tech_stack(repo_data)

        # Build comprehensive text summary for embedding
        summary_parts = [
            f"Repository: {repo_data.get('name', 'Unknown')}",
            f"Description: {repo_data.get('description', 'No description')}",
            f"Language: {primary_language}",
            f"Stars: {star_count}",
            f"Forks: {fork_count}",
            f"Open Issues: {open_issues_count}",
            f"Has README: {has_readme}",
            f"Has Tests: {has_tests}",
            f"Has CI/CD: {has_ci}",
            f"Tech Stack: {', '.join(tech_stack) if tech_stack else 'Not detected'}",
            f"URL: {repo_data.get('html_url', 'Unknown')}",
        ]

        summary_text = "\n".join(summary_parts)

        metadata = {
            "source_type": "repo",
            "primary_language": primary_language,
            "has_tests": has_tests,
            "has_readme": has_readme,
            "has_ci": has_ci,
            "last_commit_date": last_commit_date,
            "star_count": star_count,
            "fork_count": fork_count,
            "open_issues_count": open_issues_count,
            "tech_stack": tech_stack,
            "repo_name": repo_data.get("name", "Unknown"),
            "repo_url": repo_data.get("html_url", ""),
        }

        return ParseResult(
            text=summary_text,
            metadata=metadata,
            source_type="repo",
        )

    def _detect_ci(self, repo_data: dict) -> bool:
        """Check if repository has CI/CD configured."""
        ci_indicators = [
            ".github/workflows" in str(repo_data.get("file_structure", "")),
            ".travis.yml" in str(repo_data.get("file_structure", "")),
            ".circleci" in str(repo_data.get("file_structure", "")),
            "gitlab-ci" in str(repo_data.get("file_structure", "")),
        ]
        return any(ci_indicators)

    def _detect_tests(self, repo_data: dict) -> bool:
        """Check if repository has test files or directories."""
        file_structure = str(repo_data.get("file_structure", "")).lower()
        test_indicators = [
            "tests/" in file_structure or "test/" in file_structure,
            "pytest.ini" in file_structure,
            "test_" in file_structure,
            "__tests__" in file_structure,
            "spec/" in file_structure,
        ]
        return any(test_indicators)

    def _detect_tech_stack(self, repo_data: dict) -> list[str]:
        """Detect technologies from file extensions and config files."""
        tech_stack = set()
        file_structure = str(repo_data.get("file_structure", "")).lower()

        # Check for primary language
        language = repo_data.get("language", "").lower()
        if language:
            tech_stack.add(language)

        # Check file extensions
        for ext, tech in self.LANGUAGE_EXTENSIONS.items():
            if f".{ext}" in file_structure:
                tech_stack.add(tech)

        # Check for frameworks and tools
        frameworks = {
            "package.json": ["Node.js", "npm"],
            "requirements.txt": ["pip"],
            "pipfile": ["Pipenv"],
            "dockerfile": ["Docker"],
            "docker-compose": ["Docker Compose"],
            "webpack.config": ["Webpack"],
            "tsconfig.json": ["TypeScript"],
            "vite.config": ["Vite"],
            "next.config": ["Next.js"],
            "nuxt.config": ["Nuxt"],
            "gatsby-config": ["Gatsby"],
            "rails": ["Rails"],
            "django": ["Django"],
            "flask": ["Flask"],
            "fastapi": ["FastAPI"],
            "cargo.toml": ["Cargo"],
            "go.mod": ["Go Modules"],
            "composer.json": ["Composer"],
            "maven": ["Maven"],
            "gradle": ["Gradle"],
        }

        for config_file, techs in frameworks.items():
            if config_file in file_structure:
                tech_stack.update(techs)

        # Check for React/Vue/Angular
        if "react" in file_structure or "jsx" in file_structure:
            tech_stack.add("React")
        if "vue" in file_structure or ".vue" in file_structure:
            tech_stack.add("Vue.js")
        if "angular" in file_structure or ".component.ts" in file_structure:
            tech_stack.add("Angular")

        return sorted(list(tech_stack))
