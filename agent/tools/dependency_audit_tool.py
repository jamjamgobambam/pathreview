"""Audit repository dependency manifests for outdated major versions."""

import base64
import json
import re
import tomllib
from collections.abc import Callable
from urllib.parse import quote

import httpx
import structlog

from .base import BaseTool, ToolResult

logger = structlog.get_logger()

SUPPORTED_MANIFESTS = ("requirements.txt", "package.json", "pyproject.toml")


class DependencyAuditTool(BaseTool):
    """Flag dependencies that are more than one major version behind."""

    name = "dependency_audit"
    description = "Checks for outdated dependencies in project repos"

    def __init__(
        self,
        api_token: str | None = None,
        version_resolver: Callable[[str, str], str | None] | None = None,
    ) -> None:
        """Initialize the dependency audit tool.

        Args:
            api_token: Optional GitHub API token used when fetching manifests.
            version_resolver: Optional resolver used to obtain current package
                versions. Primarily useful for deterministic unit tests.
        """
        self.api_token = api_token
        self.github_base_url = "https://api.github.com"
        self.version_resolver = version_resolver or self._resolve_latest_version

    def execute(self, input_data: dict) -> ToolResult:
        """Audit supported dependency manifests.

        Args:
            input_data: Either a ``manifests`` mapping containing manifest
                contents, or ``github_username`` and ``repo_name`` for a
                repository whose root manifests should be fetched.

        Returns:
            ToolResult containing outdated dependencies and audit metadata.
        """
        manifests = input_data.get("manifests")
        fetch_errors: list[str] = []

        if manifests is not None:
            if not isinstance(manifests, dict):
                return ToolResult(
                    success=False,
                    data={},
                    error="manifests must be a dictionary",
                )

            manifest_contents = {
                filename: content
                for filename, content in manifests.items()
                if filename in SUPPORTED_MANIFESTS and isinstance(content, str)
            }
        else:
            username = input_data.get("github_username")
            repo_name = input_data.get("repo_name")

            if not username or not repo_name:
                return ToolResult(
                    success=False,
                    data={},
                    error=("Provide manifests or both github_username and repo_name"),
                )

            manifest_contents, fetch_errors = self._fetch_manifests(
                username,
                repo_name,
            )

        dependencies: list[dict[str, str]] = []
        parse_errors: list[str] = []

        for filename, content in manifest_contents.items():
            try:
                dependencies.extend(self._parse_manifest(filename, content))
            except (json.JSONDecodeError, tomllib.TOMLDecodeError, TypeError) as exc:
                parse_errors.append(f"{filename}: {exc}")

        outdated_dependencies: list[dict[str, object]] = []
        skipped_dependencies: list[dict[str, str]] = []
        lookup_failures: list[dict[str, str]] = []
        checked_count = 0

        for dependency in dependencies:
            name = dependency["name"]
            version_spec = dependency["version_spec"]
            ecosystem = dependency["ecosystem"]
            source_file = dependency["source_file"]

            declared_major = self._extract_major_version(version_spec)
            if declared_major is None:
                skipped_dependencies.append(
                    {
                        "name": name,
                        "version_spec": version_spec,
                        "source_file": source_file,
                        "reason": "Could not determine declared major version",
                    }
                )
                continue

            try:
                latest_version = self.version_resolver(name, ecosystem)
            except Exception as exc:
                logger.warning(
                    "dependency_version_lookup_failed",
                    dependency=name,
                    ecosystem=ecosystem,
                    error=str(exc),
                )
                latest_version = None

            if not latest_version:
                lookup_failures.append(
                    {
                        "name": name,
                        "ecosystem": ecosystem,
                        "source_file": source_file,
                    }
                )
                continue

            latest_major = self._extract_major_version(latest_version)
            if latest_major is None:
                lookup_failures.append(
                    {
                        "name": name,
                        "ecosystem": ecosystem,
                        "source_file": source_file,
                    }
                )
                continue

            checked_count += 1
            major_versions_behind = latest_major - declared_major

            if major_versions_behind > 1:
                outdated_dependencies.append(
                    {
                        "name": name,
                        "declared_version": version_spec,
                        "latest_version": latest_version,
                        "major_versions_behind": major_versions_behind,
                        "source_file": source_file,
                        "ecosystem": ecosystem,
                    }
                )

        data = {
            "outdated_dependencies": outdated_dependencies,
            "checked_count": checked_count,
            "manifest_files": sorted(manifest_contents),
            "skipped_dependencies": skipped_dependencies,
            "lookup_failures": lookup_failures,
            "parse_errors": parse_errors,
            "fetch_errors": fetch_errors,
        }

        logger.info(
            "dependency_audit_completed",
            checked_count=checked_count,
            outdated_count=len(outdated_dependencies),
            manifest_count=len(manifest_contents),
        )

        return ToolResult(success=True, data=data)

    def _fetch_manifests(
        self,
        username: str,
        repo_name: str,
    ) -> tuple[dict[str, str], list[str]]:
        """Fetch supported root-level manifests from a GitHub repository.

        Args:
            username: Repository owner's GitHub username.
            repo_name: Repository name.

        Returns:
            Tuple containing fetched manifest contents and fetch errors.
        """
        manifests: dict[str, str] = {}
        errors: list[str] = []

        headers = {"Accept": "application/vnd.github+json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        for filename in SUPPORTED_MANIFESTS:
            url = f"{self.github_base_url}/repos/" f"{username}/{repo_name}/contents/{filename}"

            try:
                response = httpx.get(url, headers=headers, timeout=10.0)

                if response.status_code == 404:
                    continue

                response.raise_for_status()
                payload = response.json()

                encoded_content = payload.get("content")
                if not encoded_content:
                    errors.append(f"{filename}: GitHub response had no content")
                    continue

                decoded = base64.b64decode(encoded_content).decode("utf-8")
                manifests[filename] = decoded

            except (httpx.HTTPError, ValueError, UnicodeDecodeError) as exc:
                errors.append(f"{filename}: {exc}")

        return manifests, errors

    def _parse_manifest(
        self,
        filename: str,
        content: str,
    ) -> list[dict[str, str]]:
        """Parse one supported dependency manifest.

        Args:
            filename: Supported dependency manifest filename.
            content: Raw manifest contents.

        Returns:
            List of normalized dependency dictionaries.
        """
        if filename == "requirements.txt":
            return self._parse_requirements(content)

        if filename == "package.json":
            return self._parse_package_json(content)

        if filename == "pyproject.toml":
            return self._parse_pyproject(content)

        return []

    def _parse_requirements(self, content: str) -> list[dict[str, str]]:
        """Parse dependencies from requirements.txt content."""
        dependencies: list[dict[str, str]] = []

        for raw_line in content.splitlines():
            line = raw_line.strip()

            if not line or line.startswith(("#", "-", "git+", "http://", "https://")):
                continue

            requirement = line.split(";", maxsplit=1)[0].strip()

            match = re.match(
                r"^([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?\s*(.*)$",
                requirement,
            )
            if not match:
                continue

            name, version_spec = match.groups()
            version_spec = version_spec.strip()

            if not version_spec or version_spec.startswith("@"):
                continue

            dependencies.append(
                {
                    "name": name,
                    "version_spec": version_spec,
                    "ecosystem": "pypi",
                    "source_file": "requirements.txt",
                }
            )

        return dependencies

    def _parse_package_json(self, content: str) -> list[dict[str, str]]:
        """Parse dependencies from package.json content."""
        payload = json.loads(content)

        if not isinstance(payload, dict):
            return []

        dependencies: list[dict[str, str]] = []

        sections = (
            "dependencies",
            "devDependencies",
            "peerDependencies",
            "optionalDependencies",
        )

        for section in sections:
            values = payload.get(section, {})
            if not isinstance(values, dict):
                continue

            for name, version_spec in values.items():
                if not isinstance(name, str) or not isinstance(version_spec, str):
                    continue

                dependencies.append(
                    {
                        "name": name,
                        "version_spec": version_spec,
                        "ecosystem": "npm",
                        "source_file": "package.json",
                    }
                )

        return dependencies

    def _parse_pyproject(self, content: str) -> list[dict[str, str]]:
        """Parse dependencies from PEP 621 pyproject.toml content."""
        payload = tomllib.loads(content)
        project = payload.get("project", {})

        if not isinstance(project, dict):
            return []

        raw_dependencies: list[str] = []

        dependencies = project.get("dependencies", [])
        if isinstance(dependencies, list):
            raw_dependencies.extend(item for item in dependencies if isinstance(item, str))

        optional = project.get("optional-dependencies", {})
        if isinstance(optional, dict):
            for group in optional.values():
                if isinstance(group, list):
                    raw_dependencies.extend(item for item in group if isinstance(item, str))

        parsed: list[dict[str, str]] = []

        for requirement in raw_dependencies:
            requirement = requirement.split(";", maxsplit=1)[0].strip()

            match = re.match(
                r"^([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?\s*(.*)$",
                requirement,
            )
            if not match:
                continue

            name, version_spec = match.groups()
            version_spec = version_spec.strip()

            if not version_spec or version_spec.startswith("@"):
                continue

            parsed.append(
                {
                    "name": name,
                    "version_spec": version_spec,
                    "ecosystem": "pypi",
                    "source_file": "pyproject.toml",
                }
            )

        return parsed

    @staticmethod
    def _extract_major_version(version_spec: str) -> int | None:
        """Extract the first numeric major version from a version string."""
        match = re.search(r"(?<!\d)(\d+)(?:\.\d+)*", version_spec)
        if not match:
            return None

        return int(match.group(1))

    @staticmethod
    def _resolve_latest_version(name: str, ecosystem: str) -> str | None:
        """Resolve the current package version from PyPI or npm.

        Args:
            name: Package name.
            ecosystem: Either ``pypi`` or ``npm``.

        Returns:
            Latest released version, or None when it cannot be resolved.
        """
        encoded_name = quote(name, safe="")

        try:
            if ecosystem == "pypi":
                response = httpx.get(
                    f"https://pypi.org/pypi/{encoded_name}/json",
                    timeout=10.0,
                )
                response.raise_for_status()
                version = response.json().get("info", {}).get("version")

            elif ecosystem == "npm":
                response = httpx.get(
                    f"https://registry.npmjs.org/{encoded_name}/latest",
                    timeout=10.0,
                )
                response.raise_for_status()
                version = response.json().get("version")

            else:
                return None

        except (httpx.HTTPError, ValueError):
            return None

        return version if isinstance(version, str) else None
