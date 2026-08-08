"""Parser for GitHub Actions workflow files (.github/workflows/*.yml).

Extracts CI/CD skill signals from workflow YAML content, producing
SkillDetection results for technologies like GitHub Actions, Docker,
pytest, and common setup actions.
"""

import re

from .base import SkillDetection

# Maps well-known ``uses:`` action prefixes/exact names to (skill_name, category, confidence).
ACTIONS_SKILL_MAP: dict[str, tuple[str, str, float]] = {
    "actions/setup-python": ("Python", "Language", 0.90),
    "actions/setup-node": ("Node.js", "Runtime", 0.90),
    "actions/setup-java": ("Java", "Language", 0.90),
    "actions/setup-go": ("Go", "Language", 0.90),
    "actions/setup-dotnet": ("C#", "Language", 0.90),
    "docker/build-push-action": ("Docker", "Tool", 0.95),
    "docker/login-action": ("Docker", "Tool", 0.90),
    "docker/setup-buildx-action": ("Docker", "Tool", 0.90),
    "gradle/gradle-build-action": ("Gradle", "Tool", 0.90),
    "actions/cache": ("GitHub Actions", "CI/CD", 0.80),
    "actions/checkout": ("GitHub Actions", "CI/CD", 0.95),
    "actions/upload-artifact": ("GitHub Actions", "CI/CD", 0.80),
    "actions/download-artifact": ("GitHub Actions", "CI/CD", 0.80),
    "github/codeql-action": ("GitHub Actions", "CI/CD", 0.85),
    "codecov/codecov-action": ("GitHub Actions", "CI/CD", 0.80),
    "aws-actions/configure-aws-credentials": ("AWS", "Cloud", 0.90),
    "google-github-actions/auth": ("GCP", "Cloud", 0.90),
    "azure/login": ("Azure", "Cloud", 0.90),
    "helm/kind-action": ("Kubernetes", "Tool", 0.90),
    "azure/k8s-deploy": ("Kubernetes", "Tool", 0.90),
}

# Maps run-step keywords (lowercased) to (skill_name, category, confidence).
# Ordered from more specific to less specific to avoid false positives.
RUN_SKILL_MAP: list[tuple[str, str, str, float]] = [
    ("pytest", "pytest", "Testing", 0.95),
    ("jest", "Jest", "Testing", 0.90),
    ("cargo test", "Rust", "Language", 0.85),
    ("cargo build", "Rust", "Language", 0.85),
    ("go test", "Go", "Language", 0.85),
    ("go build", "Go", "Language", 0.85),
    ("mvn", "Maven", "Tool", 0.85),
    ("gradle", "Gradle", "Tool", 0.85),
    ("docker build", "Docker", "Tool", 0.95),
    ("docker-compose", "Docker", "Tool", 0.90),
    ("docker compose", "Docker", "Tool", 0.90),
    ("kubectl", "Kubernetes", "Tool", 0.90),
    ("helm", "Helm", "Tool", 0.90),
    ("terraform", "Terraform", "Tool", 0.90),
    ("ansible", "Ansible", "Tool", 0.85),
    ("npm test", "Node.js", "Runtime", 0.85),
    ("npm run", "Node.js", "Runtime", 0.80),
    ("yarn test", "Node.js", "Runtime", 0.85),
    ("yarn", "Node.js", "Runtime", 0.75),
    ("pip install", "Python", "Language", 0.85),
    ("python ", "Python", "Language", 0.80),
    ("ruff", "Python", "Language", 0.75),
    ("black ", "Python", "Language", 0.75),
    ("mypy", "Python", "Language", 0.75),
    ("flake8", "Python", "Language", 0.75),
    ("bandit", "Python", "Language", 0.70),
]

# Matches ``uses: <action>`` in YAML list items or plain key-value lines.
# Handles:  "    - uses: owner/action@v2"  and  "      uses: owner/action@v2"
_USES_RE = re.compile(
    r"^[ \t]*(?:-[ \t]+)?uses:[ \t]*(.+)$",
    re.MULTILINE,
)

# Matches single-line ``run: <command>``.
_RUN_SINGLE_RE = re.compile(
    r"^[ \t]*(?:-[ \t]+)?run:[ \t]+(.+)$",
    re.MULTILINE,
)

# Matches block-scalar ``run: |`` or ``run: >`` followed by indented lines.
_RUN_BLOCK_RE = re.compile(
    r"^[ \t]*(?:-[ \t]+)?run:[ \t]*[|>][ \t]*\n((?:[ \t]+.*\n?)+)",
    re.MULTILINE,
)


def _is_workflow_file(filename: str | None) -> bool:
    """Return True if *filename* looks like a GitHub Actions workflow path."""
    if filename is None:
        return False
    normalized = filename.replace("\\", "/").lower()
    return ".github/workflows/" in normalized and normalized.endswith((".yml", ".yaml"))


class WorkflowParser:
    """Parse GitHub Actions workflow files and extract CI/CD skill signals.

    This parser operates on raw YAML text using lightweight regex matching
    so that it works without an external ``pyyaml`` dependency.  It
    recognises two kinds of evidence:

    * ``uses:`` lines — map well-known action names to skills via
      :data:`ACTIONS_SKILL_MAP`.
    * ``run:`` lines (single-line and block-scalar) — map common shell
      commands to skills via :data:`RUN_SKILL_MAP`.

    Any file that is routed here also earns a ``GitHub Actions`` signal at
    high confidence, because the mere presence of a workflow file proves the
    repository uses GitHub Actions for CI/CD.
    """

    def parse(self, content: str, filename: str | None = None) -> list[SkillDetection]:
        """Extract skill detections from a GitHub Actions workflow file.

        Args:
            content: Raw YAML text of the workflow file.
            filename: Optional path used only to validate the file is a
                workflow file.  If supplied and not a workflow path, an
                empty list is returned immediately.

        Returns:
            List of :class:`~ingestion.parsers.skill_extractor.SkillDetection`
            objects, one per detected technology, sorted by confidence
            descending.

        Raises:
            ValueError: If *content* is not a string.
        """
        if not isinstance(content, str):
            raise ValueError("content must be a str")

        # If a filename is provided, only proceed when it is a workflow file.
        if filename is not None and not _is_workflow_file(filename):
            return []

        if not content.strip():
            return []

        # skills_dict: skill_name -> SkillDetection
        skills: dict[str, SkillDetection] = {}

        # Any workflow file means GitHub Actions is in use.
        self._add_or_update(
            skills,
            "GitHub Actions",
            "CI/CD",
            0.95,
            ["Presence of a .github/workflows/ file"],
        )

        self._extract_uses_skills(content, skills)
        self._extract_run_skills(content, skills)

        return sorted(skills.values(), key=lambda s: s.confidence, reverse=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _add_or_update(
        self,
        skills: dict[str, SkillDetection],
        name: str,
        category: str,
        confidence: float,
        evidence: list[str],
    ) -> None:
        """Insert or strengthen an existing skill entry."""
        if name in skills:
            existing = skills[name]
            merged_evidence = list({*existing.evidence, *evidence})
            new_confidence = max(existing.confidence, confidence)
            skills[name] = SkillDetection(
                name=name,
                category=category,
                confidence=new_confidence,
                evidence=merged_evidence,
            )
        else:
            skills[name] = SkillDetection(
                name=name,
                category=category,
                confidence=confidence,
                evidence=list(evidence),
            )

    def _extract_uses_skills(self, content: str, skills: dict[str, SkillDetection]) -> None:
        """Parse ``uses:`` lines (including YAML list items) and map to known skills."""
        for match in _USES_RE.finditer(content):
            action_ref = match.group(1).strip().strip("'\"")
            # Strip the version tag (everything after @).
            action_name = action_ref.split("@")[0].lower()
            for known_action, (skill, category, conf) in ACTIONS_SKILL_MAP.items():
                if action_name == known_action.lower() or action_name.startswith(
                    known_action.lower() + "/"
                ):
                    self._add_or_update(
                        skills,
                        skill,
                        category,
                        conf,
                        [f"uses: {action_ref}"],
                    )
                    break

    def _extract_run_skills(self, content: str, skills: dict[str, SkillDetection]) -> None:
        """Parse ``run:`` lines and block run values for shell command signals."""
        run_texts: list[str] = []

        for m in _RUN_SINGLE_RE.finditer(content):
            run_texts.append(m.group(1))

        for m in _RUN_BLOCK_RE.finditer(content):
            run_texts.append(m.group(1))

        for run_text in run_texts:
            lower = run_text.lower()
            for keyword, skill, category, conf in RUN_SKILL_MAP:
                if keyword in lower:
                    self._add_or_update(
                        skills,
                        skill,
                        category,
                        conf,
                        [f"run step contains '{keyword}'"],
                    )
