"""Dependency freshness audit tool."""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from typing import Any

import structlog

from .base import BaseTool, ToolResult

logger = structlog.get_logger()


@dataclass(frozen=True)
class ParsedDependency:
    """A dependency declaration discovered in a supported manifest file."""

    name: str
    declared_version: str | None
    source_file: str
    section: str


class DependencyAuditTool(BaseTool):
    """Flag dependencies that are more than one major version behind."""

    name = "dependency_audit"
    description = "Checks dependency manifests for outdated major package versions"

    SUPPORTED_FILENAMES = ("requirements.txt", "package.json", "pyproject.toml")
    PACKAGE_PATTERN = re.compile(
        r"^\s*([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?\s*(?:==|~=|>=|<=|>|<)?\s*([^;,\s]+)?"
    )
    VERSION_PATTERN = re.compile(r"(\d+)(?:\.\d+)*(?:[-+._a-zA-Z0-9]*)?")

    def execute(self, input_data: dict) -> ToolResult:
        """Audit dependency manifest contents.

        Args:
            input_data: Dict with a ``files`` mapping of file paths to contents and
                optional ``latest_versions`` mapping of package names to latest versions.

        Returns:
            ToolResult containing audited dependencies, outdated findings, skipped files,
            and non-fatal warnings.
        """
        files = input_data.get("files", {})
        latest_versions = self._normalize_latest_versions(input_data.get("latest_versions", {}))

        if not isinstance(files, dict):
            return ToolResult(
                success=True,
                data={
                    "audited_dependencies": [],
                    "outdated_dependencies": [],
                    "skipped_files": [],
                    "warnings": ["Expected files to be a mapping of path to contents."],
                },
            )

        try:
            dependencies, skipped_files, warnings = self._parse_files(files)
            audited = []
            outdated = []

            for dependency in dependencies:
                audit_result = self._audit_dependency(dependency, latest_versions)
                audited.append(audit_result)
                if audit_result.get("status") == "outdated":
                    outdated.append(audit_result)

            logger.info(
                "dependency_audit_completed",
                audited_dependencies=len(audited),
                outdated_dependencies=len(outdated),
            )

            return ToolResult(
                success=True,
                data={
                    "audited_dependencies": audited,
                    "outdated_dependencies": outdated,
                    "skipped_files": skipped_files,
                    "warnings": warnings,
                },
            )

        except Exception as e:
            logger.error("dependency_audit_error", error=str(e))
            return ToolResult(success=False, data={}, error=str(e))

    def _parse_files(
        self,
        files: dict[str, str],
    ) -> tuple[list[ParsedDependency], list[str], list[str]]:
        """Parse all supported dependency manifest files."""
        dependencies = []
        skipped_files = []
        warnings = []

        for path, content in files.items():
            filename = path.rsplit("/", 1)[-1]
            if filename not in self.SUPPORTED_FILENAMES:
                skipped_files.append(path)
                continue

            if not isinstance(content, str):
                warnings.append(f"Skipped {path}: expected text content.")
                continue

            parsed, parse_warnings = self._parse_supported_file(path, filename, content)
            dependencies.extend(parsed)
            warnings.extend(parse_warnings)

        return dependencies, skipped_files, warnings

    def _parse_supported_file(
        self,
        path: str,
        filename: str,
        content: str,
    ) -> tuple[list[ParsedDependency], list[str]]:
        """Parse a dependency file using the parser for its filename."""
        if filename == "requirements.txt":
            return self._parse_requirements(path, content), []
        if filename == "package.json":
            return self._parse_package_json(path, content)
        if filename == "pyproject.toml":
            return self._parse_pyproject(path, content)
        return [], [f"Unsupported dependency file: {path}"]

    def _parse_requirements(self, path: str, content: str) -> list[ParsedDependency]:
        """Parse common package declarations from requirements.txt content."""
        dependencies = []

        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue

            line = line.split("#", 1)[0].strip()
            match = self.PACKAGE_PATTERN.match(line)
            if not match:
                continue

            dependencies.append(
                ParsedDependency(
                    name=match.group(1),
                    declared_version=self._clean_version(match.group(2)),
                    source_file=path,
                    section="requirements",
                )
            )

        return dependencies

    def _parse_package_json(
        self,
        path: str,
        content: str,
    ) -> tuple[list[ParsedDependency], list[str]]:
        """Parse dependency sections from package.json content."""
        try:
            package_data = json.loads(content)
        except json.JSONDecodeError as e:
            return [], [f"Could not parse {path}: {e.msg}."]

        dependencies = []
        dependency_sections = (
            "dependencies",
            "devDependencies",
            "peerDependencies",
            "optionalDependencies",
        )
        for section in dependency_sections:
            declared_packages = package_data.get(section, {})
            if not isinstance(declared_packages, dict):
                continue

            for name, declared_version in declared_packages.items():
                dependencies.append(
                    ParsedDependency(
                        name=name,
                        declared_version=self._clean_version(str(declared_version)),
                        source_file=path,
                        section=section,
                    )
                )

        return dependencies, []

    def _parse_pyproject(
        self,
        path: str,
        content: str,
    ) -> tuple[list[ParsedDependency], list[str]]:
        """Parse dependency sections from pyproject.toml content."""
        try:
            project_data = tomllib.loads(content)
        except tomllib.TOMLDecodeError as e:
            return [], [f"Could not parse {path}: {e}."]

        dependencies = []
        project_section = project_data.get("project", {})
        if isinstance(project_section, dict):
            dependencies.extend(
                self._parse_dependency_list(
                    path,
                    project_section.get("dependencies", []),
                    "project.dependencies",
                )
            )

            optional_dependencies = project_section.get("optional-dependencies", {})
            if isinstance(optional_dependencies, dict):
                for group, dependency_list in optional_dependencies.items():
                    dependencies.extend(
                        self._parse_dependency_list(
                            path,
                            dependency_list,
                            f"project.optional-dependencies.{group}",
                        )
                    )

        poetry_dependencies = self._get_nested(project_data, ["tool", "poetry", "dependencies"])
        if isinstance(poetry_dependencies, dict):
            dependencies.extend(self._parse_poetry_dependencies(path, poetry_dependencies))

        return dependencies, []

    def _parse_dependency_list(
        self,
        path: str,
        dependency_list: Any,
        section: str,
    ) -> list[ParsedDependency]:
        """Parse PEP 508 style dependency strings from pyproject.toml."""
        if not isinstance(dependency_list, list):
            return []

        dependencies = []
        for dependency in dependency_list:
            if not isinstance(dependency, str):
                continue

            match = self.PACKAGE_PATTERN.match(dependency)
            if not match:
                continue

            dependencies.append(
                ParsedDependency(
                    name=match.group(1),
                    declared_version=self._clean_version(match.group(2)),
                    source_file=path,
                    section=section,
                )
            )

        return dependencies

    def _parse_poetry_dependencies(
        self,
        path: str,
        poetry_dependencies: dict[str, Any],
    ) -> list[ParsedDependency]:
        """Parse Poetry dependency declarations."""
        dependencies = []

        for name, declaration in poetry_dependencies.items():
            if name.lower() == "python":
                continue

            declared_version = declaration
            if isinstance(declaration, dict):
                declared_version = declaration.get("version")

            dependencies.append(
                ParsedDependency(
                    name=name,
                    declared_version=self._clean_version(str(declared_version)),
                    source_file=path,
                    section="tool.poetry.dependencies",
                )
            )

        return dependencies

    def _audit_dependency(
        self,
        dependency: ParsedDependency,
        latest_versions: dict[str, str],
    ) -> dict[str, Any]:
        """Compare a parsed dependency declaration with the latest known version."""
        latest_version = latest_versions.get(self._normalize_package_name(dependency.name))
        declared_major = self._extract_major(dependency.declared_version)
        latest_major = self._extract_major(latest_version)
        major_gap = None
        status = "unknown"

        if declared_major is None:
            status = "unpinned"
        elif latest_major is None:
            status = "latest_unknown"
        else:
            major_gap = latest_major - declared_major
            status = "outdated" if major_gap > 1 else "current"

        return {
            "name": dependency.name,
            "source_file": dependency.source_file,
            "section": dependency.section,
            "declared_version": dependency.declared_version,
            "latest_version": latest_version,
            "major_gap": major_gap,
            "status": status,
        }

    def _normalize_latest_versions(self, latest_versions: Any) -> dict[str, str]:
        """Normalize latest-version package names for case-insensitive lookup."""
        if not isinstance(latest_versions, dict):
            return {}

        normalized = {}
        for package_name, version in latest_versions.items():
            normalized[self._normalize_package_name(str(package_name))] = str(version)
        return normalized

    @staticmethod
    def _normalize_package_name(package_name: str) -> str:
        """Normalize package names using Python packaging name conventions."""
        return re.sub(r"[-_.]+", "-", package_name).lower()

    @classmethod
    def _clean_version(cls, version: str | None) -> str | None:
        """Extract the first version-looking token from a dependency specifier."""
        if not version:
            return None

        match = cls.VERSION_PATTERN.search(version.strip())
        if not match:
            return None
        return match.group(0)

    @classmethod
    def _extract_major(cls, version: str | None) -> int | None:
        """Extract the major version integer from a version string."""
        if not version:
            return None

        match = cls.VERSION_PATTERN.search(version)
        if not match:
            return None
        return int(match.group(1))

    @staticmethod
    def _get_nested(data: dict[str, Any], keys: list[str]) -> Any:
        """Fetch a nested dictionary value without raising KeyError."""
        current: Any = data
        for key in keys:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return current
