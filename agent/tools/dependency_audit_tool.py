"""Audit project dependencies for outdated major versions."""

import base64
import json
import re
import tomllib
from urllib.parse import quote

import httpx
import structlog

from .base import BaseTool, ToolResult

logger = structlog.get_logger()


class DependencyAuditTool(BaseTool):
    """Find dependencies that are more than one major version behind."""

    name = "dependency_audit"
    description = "Audit project dependencies for outdated major versions"

    SUPPORTED_FILES = ("requirements.txt", "package.json", "pyproject.toml")
    DEPENDENCY_SECTIONS = (
        "dependencies",
        "devDependencies",
        "optionalDependencies",
        "peerDependencies",
    )

    def __init__(self, api_token: str | None = None) -> None:
        """Initialize the dependency audit tool.

        Args:
            api_token: Optional GitHub API token.
        """
        self.api_token = api_token
        self.github_base_url = "https://api.github.com"
        self.pypi_base_url = "https://pypi.org/pypi"
        self.npm_base_url = "https://registry.npmjs.org"

    def execute(self, input_data: dict) -> ToolResult:
        """Audit supported dependency files.

        Args:
            input_data: Either a ``dependency_files`` mapping or GitHub repository details.

        Returns:
            ToolResult containing audited manifests and outdated dependencies.
        """
        try:
            dependency_files = self._resolve_dependency_files(input_data)
            if dependency_files is None:
                return ToolResult(
                    success=False,
                    data={},
                    error=("Provide dependency_files or both github_username and repo_name"),
                )

            audit_data = self._audit_files(dependency_files)
            return ToolResult(success=True, data=audit_data)
        except Exception as error:
            logger.error("dependency_audit_error", error=str(error))
            return ToolResult(success=False, data={}, error=str(error))

    def _resolve_dependency_files(self, input_data: dict) -> dict[str, str] | None:
        """Return direct manifest contents or retrieve them from GitHub."""
        if "dependency_files" in input_data:
            dependency_files = input_data["dependency_files"]
            if not isinstance(dependency_files, dict):
                raise ValueError("dependency_files must be a mapping of file names to contents")

            return {
                str(file_name): content
                for file_name, content in dependency_files.items()
                if isinstance(content, str)
            }

        username = input_data.get("github_username")
        repo_name = input_data.get("repo_name")
        if not username or not repo_name:
            return None

        return self._fetch_dependency_files(str(username), str(repo_name))

    def _fetch_dependency_files(self, username: str, repo_name: str) -> dict[str, str]:
        """Retrieve supported root-level dependency files from GitHub."""
        dependency_files: dict[str, str] = {}
        headers = {"Accept": "application/vnd.github+json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        for file_name in self.SUPPORTED_FILES:
            url = f"{self.github_base_url}/repos/{username}/{repo_name}/contents/" f"{file_name}"

            try:
                response = httpx.get(url, headers=headers, timeout=10.0)
                if response.status_code == 404:
                    continue

                response.raise_for_status()
                payload = response.json()
                encoded_content = payload.get("content", "")
                if not encoded_content:
                    continue

                dependency_files[file_name] = base64.b64decode(encoded_content).decode("utf-8")
            except (httpx.HTTPError, ValueError, UnicodeDecodeError) as error:
                logger.warning(
                    "dependency_manifest_fetch_failed",
                    file=file_name,
                    username=username,
                    repo=repo_name,
                    error=str(error),
                )

        return dependency_files

    def _audit_files(self, dependency_files: dict[str, str]) -> dict:
        """Parse dependency files and compare declared versions with registries."""
        manifests_found: list[str] = []
        dependencies: list[dict[str, str]] = []
        skipped_dependencies: list[dict[str, str]] = []

        for file_path, content in dependency_files.items():
            file_name = file_path.replace("\\", "/").rsplit("/", maxsplit=1)[-1]
            if file_name not in self.SUPPORTED_FILES:
                continue

            manifests_found.append(file_path)
            try:
                dependencies.extend(self._parse_dependency_file(file_name, file_path, content))
            except (json.JSONDecodeError, tomllib.TOMLDecodeError, ValueError) as error:
                skipped_dependencies.append(
                    {
                        "name": file_path,
                        "reason": f"Could not parse manifest: {error}",
                    }
                )

        outdated_dependencies: list[dict[str, object]] = []
        dependencies_checked = 0

        for dependency in dependencies:
            latest_version = self._get_latest_version(dependency["name"], dependency["ecosystem"])
            if latest_version is None:
                skipped_dependencies.append(
                    {
                        "name": dependency["name"],
                        "reason": "Latest version could not be retrieved",
                    }
                )
                continue

            dependencies_checked += 1
            declared_major = self._get_major_version(dependency["declared_version"])
            latest_major = self._get_major_version(latest_version)
            if declared_major is None or latest_major is None:
                skipped_dependencies.append(
                    {
                        "name": dependency["name"],
                        "reason": "Version could not be compared",
                    }
                )
                continue

            major_versions_behind = latest_major - declared_major
            if major_versions_behind > 1:
                outdated_dependencies.append(
                    {
                        **dependency,
                        "latest_version": latest_version,
                        "major_versions_behind": major_versions_behind,
                    }
                )

        return {
            "manifests_found": manifests_found,
            "dependencies_checked": dependencies_checked,
            "outdated_dependencies": outdated_dependencies,
            "skipped_dependencies": skipped_dependencies,
        }

    def _parse_dependency_file(
        self,
        file_name: str,
        source_file: str,
        content: str,
    ) -> list[dict[str, str]]:
        """Parse a supported dependency file into a common structure."""
        if file_name == "requirements.txt":
            return self._parse_requirements(content, source_file)
        if file_name == "package.json":
            return self._parse_package_json(content, source_file)
        if file_name == "pyproject.toml":
            return self._parse_pyproject(content, source_file)
        return []

    def _parse_requirements(
        self,
        content: str,
        source_file: str,
    ) -> list[dict[str, str]]:
        """Parse common pinned or constrained requirements.txt entries."""
        dependencies: list[dict[str, str]] = []

        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith(("#", "-", "http://", "https://", "git+")):
                continue

            line = line.split(";", maxsplit=1)[0].strip()
            match = re.match(
                r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]+\])?"
                r"\s*(?:===|==|~=|>=|<=|>|<)\s*([0-9][A-Za-z0-9.!+-]*)",
                line,
            )
            if not match:
                continue

            dependencies.append(
                self._dependency_entry(
                    name=match.group(1),
                    ecosystem="pypi",
                    declared_version=match.group(2),
                    source_file=source_file,
                )
            )

        return dependencies

    def _parse_package_json(
        self,
        content: str,
        source_file: str,
    ) -> list[dict[str, str]]:
        """Parse dependency sections from package.json."""
        payload = json.loads(content)
        dependencies: list[dict[str, str]] = []

        for section in self.DEPENDENCY_SECTIONS:
            section_data = payload.get(section, {})
            if not isinstance(section_data, dict):
                continue

            for name, version_spec in section_data.items():
                if not isinstance(version_spec, str):
                    continue

                version = self._extract_version(version_spec)
                if version is None:
                    continue

                dependencies.append(
                    self._dependency_entry(
                        name=str(name),
                        ecosystem="npm",
                        declared_version=version,
                        source_file=source_file,
                    )
                )

        return dependencies

    def _parse_pyproject(
        self,
        content: str,
        source_file: str,
    ) -> list[dict[str, str]]:
        """Parse PEP 621 and Poetry dependencies from pyproject.toml."""
        payload = tomllib.loads(content)
        dependencies: list[dict[str, str]] = []

        project = payload.get("project", {})
        if isinstance(project, dict):
            project_dependencies = project.get("dependencies", [])
            if isinstance(project_dependencies, list):
                for requirement in project_dependencies:
                    if isinstance(requirement, str):
                        entry = self._parse_python_requirement(requirement, source_file)
                        if entry:
                            dependencies.append(entry)

            optional_groups = project.get("optional-dependencies", {})
            if isinstance(optional_groups, dict):
                for group_dependencies in optional_groups.values():
                    if not isinstance(group_dependencies, list):
                        continue
                    for requirement in group_dependencies:
                        if isinstance(requirement, str):
                            entry = self._parse_python_requirement(requirement, source_file)
                            if entry:
                                dependencies.append(entry)

        tool_data = payload.get("tool", {})
        poetry = tool_data.get("poetry", {}) if isinstance(tool_data, dict) else {}
        if isinstance(poetry, dict):
            poetry_dependencies = poetry.get("dependencies", {})
            dependencies.extend(self._parse_poetry_dependencies(poetry_dependencies, source_file))

            groups = poetry.get("group", {})
            if isinstance(groups, dict):
                for group_data in groups.values():
                    if not isinstance(group_data, dict):
                        continue
                    dependencies.extend(
                        self._parse_poetry_dependencies(
                            group_data.get("dependencies", {}), source_file
                        )
                    )

        return dependencies

    def _parse_python_requirement(
        self,
        requirement: str,
        source_file: str,
    ) -> dict[str, str] | None:
        """Parse one PEP-style dependency requirement."""
        line = requirement.split(";", maxsplit=1)[0].strip()
        match = re.match(
            r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]+\])?"
            r"\s*(?:===|==|~=|>=|<=|>|<)\s*([0-9][A-Za-z0-9.!+-]*)",
            line,
        )
        if not match:
            return None

        return self._dependency_entry(
            name=match.group(1),
            ecosystem="pypi",
            declared_version=match.group(2),
            source_file=source_file,
        )

    def _parse_poetry_dependencies(
        self,
        dependencies: object,
        source_file: str,
    ) -> list[dict[str, str]]:
        """Parse a Poetry dependency mapping."""
        if not isinstance(dependencies, dict):
            return []

        parsed: list[dict[str, str]] = []
        for name, version_data in dependencies.items():
            if str(name).lower() == "python":
                continue

            version_spec: str | None = None
            if isinstance(version_data, str):
                version_spec = version_data
            elif isinstance(version_data, dict):
                candidate = version_data.get("version")
                if isinstance(candidate, str):
                    version_spec = candidate

            if version_spec is None:
                continue

            version = self._extract_version(version_spec)
            if version is None:
                continue

            parsed.append(
                self._dependency_entry(
                    name=str(name),
                    ecosystem="pypi",
                    declared_version=version,
                    source_file=source_file,
                )
            )

        return parsed

    def _get_latest_version(self, name: str, ecosystem: str) -> str | None:
        """Get the latest stable version from PyPI or npm."""
        try:
            if ecosystem == "pypi":
                url = f"{self.pypi_base_url}/{quote(name, safe='')}/json"
                response = httpx.get(url, timeout=10.0)
                response.raise_for_status()
                version = response.json().get("info", {}).get("version")
            elif ecosystem == "npm":
                url = f"{self.npm_base_url}/{quote(name, safe='')}"
                response = httpx.get(url, timeout=10.0)
                response.raise_for_status()
                version = response.json().get("dist-tags", {}).get("latest")
            else:
                return None

            return str(version) if version else None
        except (httpx.HTTPError, ValueError, TypeError) as error:
            logger.warning(
                "dependency_version_lookup_failed",
                package=name,
                ecosystem=ecosystem,
                error=str(error),
            )
            return None

    @staticmethod
    def _extract_version(version_spec: str) -> str | None:
        """Extract the first numeric version from a dependency specification."""
        unsupported_prefixes = ("git+", "git://", "http://", "https://", "file:", "workspace:")
        if version_spec.strip().lower().startswith(unsupported_prefixes):
            return None

        match = re.search(r"(?<![A-Za-z0-9])v?([0-9]+(?:\.[0-9A-Za-z!+-]+)*)", version_spec)
        return match.group(1) if match else None

    @staticmethod
    def _get_major_version(version: str) -> int | None:
        """Return the first numeric component of a version string."""
        match = re.search(r"[0-9]+", version)
        return int(match.group()) if match else None

    @staticmethod
    def _dependency_entry(
        name: str,
        ecosystem: str,
        declared_version: str,
        source_file: str,
    ) -> dict[str, str]:
        """Build a normalized dependency entry."""
        return {
            "name": name,
            "ecosystem": ecosystem,
            "declared_version": declared_version,
            "source_file": source_file,
        }
