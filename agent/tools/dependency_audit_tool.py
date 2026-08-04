"""Dependency audit tool.

Flags dependencies that are more than one major version behind their latest
release across Python (``requirements.txt``, ``pyproject.toml``) and Node.js
(``package.json``) manifests. This supports DevOps/CI-CD workflows by surfacing
dependencies that carry the most upgrade/maintenance risk.
"""

import json
import re
import tomllib

import httpx
import structlog

from .base import BaseTool, ToolResult

logger = structlog.get_logger()

# Operators/prefixes that can precede a version number in a manifest spec,
# e.g. "^", "~", ">=", "==", "~=", or a leading "v" (as in "v1.2.3").
_VERSION_PREFIX_RE = re.compile(r"^[\^~>=<!=\s vV]+")
_LEADING_INT_RE = re.compile(r"(\d+)")
# A distribution name at the start of a requirement line, before any spec/extras.
_REQ_NAME_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)")


class DependencyAuditTool(BaseTool):
    """Detect dependencies lagging more than one major version behind latest."""

    name = "dependency_audit"
    description = (
        "Flag dependencies that are more than one major version behind their "
        "latest release in requirements.txt, package.json, or pyproject.toml"
    )

    def __init__(self, check_latest_online: bool = False, max_major_lag: int = 1) -> None:
        """Initialize the tool.

        Args:
            check_latest_online: If True, query the PyPI/npm registries for the
                latest version whenever it is not supplied in the input. Defaults
                to False so the tool is deterministic and offline-friendly.
            max_major_lag: A dependency is flagged when it trails the latest
                release by more than this many major versions. Default 1 (i.e.
                flag when two or more majors behind).
        """
        self.check_latest_online = check_latest_online
        self.max_major_lag = max_major_lag

    def execute(self, input_data: dict) -> ToolResult:
        """Audit dependency manifests for badly outdated major versions.

        Args:
            input_data: May contain:
                - ``manifests``: dict mapping a manifest filename
                  (``requirements.txt``, ``package.json``, ``pyproject.toml``) to
                  its raw text contents.
                - ``latest_versions``: optional dict mapping a package name to its
                  latest version string. Names are matched case/separator
                  insensitively.
                - ``max_major_lag``: optional per-call override of the threshold.

        Returns:
            ToolResult whose ``data`` holds ``outdated`` (list of findings),
            ``checked`` (count of comparable dependencies), and ``skipped``
            (items that could not be parsed or resolved).
        """
        manifests = input_data.get("manifests") or {}
        latest_versions = self._normalize_latest(input_data.get("latest_versions") or {})
        max_major_lag = input_data.get("max_major_lag", self.max_major_lag)

        outdated: list[dict] = []
        skipped: list[dict] = []
        checked = 0

        try:
            for filename, content in manifests.items():
                try:
                    deps = self._parse_manifest(filename, content)
                except Exception as e:  # one bad manifest must not fail the run
                    logger.warning("dependency_audit_parse_failed", file=filename, error=str(e))
                    skipped.append({"file": filename, "reason": f"parse error: {e}"})
                    continue

                for name, current_spec, ecosystem in deps:
                    current_major = self._extract_major(current_spec)
                    if current_major is None:
                        skipped.append({"name": name, "reason": "unpinned or unparseable version"})
                        continue

                    latest = self._resolve_latest(name, ecosystem, latest_versions)
                    if latest is None:
                        skipped.append({"name": name, "reason": "latest version unknown"})
                        continue

                    latest_major = self._extract_major(latest)
                    if latest_major is None:
                        skipped.append({"name": name, "reason": "latest version unparseable"})
                        continue

                    checked += 1
                    majors_behind = latest_major - current_major
                    if majors_behind > max_major_lag:
                        outdated.append(
                            {
                                "name": name,
                                "ecosystem": ecosystem,
                                "current": current_spec,
                                "latest": latest,
                                "majors_behind": majors_behind,
                            }
                        )

            # Most-outdated first, then alphabetical for stable output.
            outdated.sort(key=lambda item: (-item["majors_behind"], item["name"]))
            logger.info(
                "dependency_audit_complete",
                checked=checked,
                outdated=len(outdated),
                skipped=len(skipped),
            )
            return ToolResult(
                success=True,
                data={"outdated": outdated, "checked": checked, "skipped": skipped},
            )

        except Exception as e:
            logger.error("dependency_audit_error", error=str(e))
            return ToolResult(success=False, data={}, error=str(e))

    # ---- Manifest parsing ----

    def _parse_manifest(self, filename: str, content: str) -> list[tuple[str, str, str]]:
        """Dispatch to the parser for a given manifest filename.

        Args:
            filename: Manifest filename (may include a path prefix).
            content: Raw manifest text.

        Returns:
            List of ``(name, version_spec, ecosystem)`` tuples.

        Raises:
            ValueError: If the manifest filename is not supported.
        """
        base = filename.rsplit("/", 1)[-1].lower()
        if base.startswith("requirements") and base.endswith(".txt"):
            return self._parse_requirements(content)
        if base == "package.json":
            return self._parse_package_json(content)
        if base == "pyproject.toml":
            return self._parse_pyproject(content)
        raise ValueError(f"unsupported manifest: {filename}")

    def _parse_requirements(self, content: str) -> list[tuple[str, str, str]]:
        """Parse a ``requirements.txt`` body into dependency records."""
        deps: list[tuple[str, str, str]] = []
        for raw_line in content.splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if not line or line.startswith("-"):
                continue  # blank, comment, or pip option (-r, -e, --hash, ...)
            if "://" in line or line.startswith("git+"):
                continue  # VCS/URL requirement, no comparable version
            parsed = self._parse_requirement_string(line)
            if parsed:
                deps.append(parsed)
        return deps

    def _parse_requirement_string(self, req: str) -> tuple[str, str, str] | None:
        """Parse a single PEP 508 requirement string into a record."""
        line = req.split("#", 1)[0].split(";", 1)[0].strip()  # drop markers/comments
        if not line:
            return None
        match = _REQ_NAME_RE.match(line)
        if not match:
            return None
        name = match.group(1)
        spec = line[match.end() :].strip()
        if spec.startswith("["):  # drop extras, e.g. "pkg[extra]==1.0"
            close = spec.find("]")
            if close != -1:
                spec = spec[close + 1 :].strip()
        return (name, spec, "pypi")

    def _parse_package_json(self, content: str) -> list[tuple[str, str, str]]:
        """Parse ``package.json`` dependencies and devDependencies."""
        data = json.loads(content)
        deps: list[tuple[str, str, str]] = []
        for section in ("dependencies", "devDependencies"):
            section_data = data.get(section) or {}
            if not isinstance(section_data, dict):
                continue
            for name, spec in section_data.items():
                if not isinstance(spec, str) or self._is_non_registry_npm_spec(spec):
                    continue
                deps.append((name, spec, "npm"))
        return deps

    def _parse_pyproject(self, content: str) -> list[tuple[str, str, str]]:
        """Parse ``pyproject.toml`` PEP 621 and Poetry dependency tables."""
        data = tomllib.loads(content)
        deps: list[tuple[str, str, str]] = []

        project = data.get("project")
        if isinstance(project, dict):
            for req in project.get("dependencies", []) or []:
                if isinstance(req, str):
                    parsed = self._parse_requirement_string(req)
                    if parsed:
                        deps.append(parsed)

        tool = data.get("tool")
        poetry = tool.get("poetry") if isinstance(tool, dict) else None
        poetry_deps = poetry.get("dependencies") if isinstance(poetry, dict) else None
        if isinstance(poetry_deps, dict):
            for name, spec in poetry_deps.items():
                if name.lower() == "python":
                    continue  # Poetry lists the Python interpreter here
                if isinstance(spec, str):
                    deps.append((name, spec, "pypi"))
                elif isinstance(spec, dict) and isinstance(spec.get("version"), str):
                    deps.append((name, spec["version"], "pypi"))
        return deps

    # ---- Version handling ----

    @staticmethod
    def _extract_major(spec: str) -> int | None:
        """Extract the leading major-version integer from a version spec.

        Handles common range operators and prefixes (``^``, ``~``, ``>=``,
        ``==``, ``~=``, leading ``v``) and compound ranges (``>=1.2,<2.0``).
        Returns None for unpinned/wildcard/unparseable specs (``*``, ``x``, "").
        """
        cleaned = _VERSION_PREFIX_RE.sub("", spec.strip())
        if not cleaned or cleaned[0] in "*xX":
            return None
        match = _LEADING_INT_RE.match(cleaned)
        if not match:
            return None
        return int(match.group(1))

    @staticmethod
    def _is_non_registry_npm_spec(spec: str) -> bool:
        """Return True for npm specs that are not comparable registry versions."""
        spec = spec.strip()
        if not spec or spec in ("*", "latest", "x"):
            return True
        lowered = spec.lower()
        if lowered.startswith(("file:", "link:", "workspace:", "git", "http", "npm:", "github:")):
            return True
        return "/" in spec  # github shorthand like "user/repo"

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize a package name for matching (PEP 503-style)."""
        return re.sub(r"[-_.]+", "-", name.strip().lower())

    def _normalize_latest(self, latest_versions: dict) -> dict[str, str]:
        """Normalize the keys of a supplied latest-versions map."""
        return {self._normalize_name(str(k)): str(v) for k, v in latest_versions.items()}

    def _resolve_latest(
        self, name: str, ecosystem: str, latest_versions: dict[str, str]
    ) -> str | None:
        """Resolve the latest version for a dependency.

        Prefers the injected ``latest_versions`` map (keeps runs deterministic);
        falls back to a live registry lookup only when ``check_latest_online`` is
        enabled.
        """
        key = self._normalize_name(name)
        if key in latest_versions:
            return latest_versions[key]
        if self.check_latest_online:
            return self._fetch_latest_online(name, ecosystem)
        return None

    def _fetch_latest_online(self, name: str, ecosystem: str) -> str | None:
        """Best-effort latest-version lookup from PyPI or the npm registry."""
        try:
            if ecosystem == "pypi":
                resp = httpx.get(f"https://pypi.org/pypi/{name}/json", timeout=5.0)
                resp.raise_for_status()
                version = resp.json().get("info", {}).get("version")
            elif ecosystem == "npm":
                resp = httpx.get(f"https://registry.npmjs.org/{name}/latest", timeout=5.0)
                resp.raise_for_status()
                version = resp.json().get("version")
            else:
                return None
            return version if isinstance(version, str) else None
        except Exception as e:
            logger.warning("dependency_audit_latest_fetch_failed", name=name, error=str(e))
            return None
