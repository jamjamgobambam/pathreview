"""Dependency vulnerability scan gate for CI.

Runs ``pip-audit`` (Python) and ``npm audit`` (frontend) and fails the build when
a vulnerability advisory appears that is not already recorded in the committed
baseline at ``.github/audit-baseline.json``.

The baseline captures the advisories that were already present when this gate was
introduced, so the pipeline does not red-wall on day one over pre-existing,
not-yet-fixable findings while still blocking *newly introduced* vulnerabilities.
Regenerate it deliberately after intentionally changing dependencies::

    python scripts/dependency_audit.py --update-baseline

Severity handling differs by ecosystem: ``pip-audit`` does not emit a normalized
severity, so every new Python advisory is gated; ``npm audit`` reports a severity
per advisory, so only ``high`` and ``critical`` npm advisories are gated.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BASELINE_PATH = REPO_ROOT / ".github" / "audit-baseline.json"
FRONTEND_DIR = REPO_ROOT / "frontend"

# npm severities that fail the build. Python advisories carry no severity from
# pip-audit, so they are all gated regardless of this set.
GATED_NPM_SEVERITIES = frozenset({"high", "critical"})


@dataclass(frozen=True)
class Advisory:
    """A single vulnerability advisory reported by one of the scanners.

    Attributes:
        ecosystem: Either ``"python"`` or ``"npm"``.
        advisory_id: The scanner's stable identifier for the advisory.
        package: The name of the affected package.
        severity: Lower-cased severity string, or ``""`` when unknown.
        title: A short human-readable summary for triage output.
    """

    ecosystem: str
    advisory_id: str
    package: str
    severity: str
    title: str


@dataclass(frozen=True)
class Baseline:
    """Sets of already-known advisory ids, keyed by ecosystem."""

    python: frozenset[str]
    npm: frozenset[str]


@dataclass(frozen=True)
class ScanResult:
    """The advisories that are new relative to the baseline."""

    new_python: list[Advisory]
    new_npm: list[Advisory]

    @property
    def passed(self) -> bool:
        """Return ``True`` when no new advisories were found."""
        return not self.new_python and not self.new_npm


def _pip_audit_dependencies(report: dict | list) -> list[dict]:
    """Return the dependency list from a pip-audit report, tolerating formats.

    Different ``pip-audit`` versions emit either a top-level ``{"dependencies":
    [...]}`` object or a bare list of dependency records.
    """
    if isinstance(report, list):
        return report
    return report.get("dependencies", [])


def parse_pip_audit(report: dict | list) -> list[Advisory]:
    """Extract advisories from ``pip-audit --format=json`` output.

    Args:
        report: The parsed JSON produced by ``pip-audit``.

    Returns:
        One :class:`Advisory` per (package, vulnerability id) pair. pip-audit does
        not provide a severity, so :attr:`Advisory.severity` is left empty.
    """
    advisories: list[Advisory] = []
    for dep in _pip_audit_dependencies(report):
        name = dep.get("name", "")
        for vuln in dep.get("vulns", []):
            advisory_id = vuln.get("id", "")
            if not advisory_id:
                continue
            description = vuln.get("description") or ""
            advisories.append(Advisory("python", advisory_id, name, "", description[:80]))
    return advisories


def parse_npm_audit(report: dict) -> list[Advisory]:
    """Extract advisories from ``npm audit --json`` output.

    Args:
        report: The parsed JSON produced by ``npm audit`` (npm v7+ schema).

    Returns:
        One :class:`Advisory` per concrete advisory. String ``via`` entries are
        transitive references to other advisories and are skipped so each
        advisory is counted once at its source.
    """
    advisories: list[Advisory] = []
    for package, info in report.get("vulnerabilities", {}).items():
        for via in info.get("via", []):
            if not isinstance(via, dict):
                continue
            source = via.get("source")
            if source is None:
                continue
            severity = (via.get("severity") or "").lower()
            title = via.get("title") or ""
            advisories.append(Advisory("npm", str(source), package, severity, title[:80]))
    return advisories


def gated_npm(advisories: list[Advisory]) -> list[Advisory]:
    """Return only the npm advisories at or above the gated severity."""
    return [a for a in advisories if a.severity in GATED_NPM_SEVERITIES]


def new_advisories(current: list[Advisory], known_ids: frozenset[str]) -> list[Advisory]:
    """Return the advisories whose ids are not already in ``known_ids``."""
    return [a for a in current if a.advisory_id not in known_ids]


def evaluate(pip_report: dict | list, npm_report: dict, baseline: Baseline) -> ScanResult:
    """Compare current scans against the baseline and report what is new.

    Args:
        pip_report: Parsed ``pip-audit`` JSON.
        npm_report: Parsed ``npm audit`` JSON.
        baseline: The known-advisory baseline to diff against.

    Returns:
        A :class:`ScanResult` listing the new Python and npm advisories.
    """
    python = parse_pip_audit(pip_report)
    npm = gated_npm(parse_npm_audit(npm_report))
    return ScanResult(
        new_advisories(python, baseline.python),
        new_advisories(npm, baseline.npm),
    )


def load_baseline(path: Path) -> Baseline:
    """Load the advisory baseline, treating a missing file as empty."""
    if not path.exists():
        return Baseline(frozenset(), frozenset())
    data = json.loads(path.read_text())
    return Baseline(frozenset(data.get("python", [])), frozenset(data.get("npm", [])))


def build_baseline(pip_report: dict | list, npm_report: dict) -> dict:
    """Build a baseline document snapshotting all currently-present advisories."""
    python = sorted({a.advisory_id for a in parse_pip_audit(pip_report)})
    npm = sorted({a.advisory_id for a in gated_npm(parse_npm_audit(npm_report))})
    return {
        "_comment": (
            "Advisories already present when the CI dependency scan was added. The "
            "scan fails only on advisory ids NOT listed here. Regenerate with "
            "`python scripts/dependency_audit.py --update-baseline` after "
            "intentionally changing dependencies. See docs/CONTRIBUTING.md."
        ),
        "python": python,
        "npm": npm,
    }


def format_report(result: ScanResult) -> str:
    """Render a human-readable summary of the scan result for CI logs."""
    if result.passed:
        return "Dependency scan passed: no new advisories outside the baseline."

    lines = ["Dependency scan FAILED: new advisories found outside the baseline.", ""]
    for advisory in result.new_python:
        lines.append(f"  [python] {advisory.advisory_id} {advisory.package}: {advisory.title}")
    for advisory in result.new_npm:
        lines.append(
            f"  [npm/{advisory.severity}] {advisory.advisory_id} "
            f"{advisory.package}: {advisory.title}"
        )
    lines += [
        "",
        "Fix the dependency, or, if the advisory is accepted, add its id to",
        "`.github/audit-baseline.json` (or run with --update-baseline) with a note.",
    ]
    return "\n".join(lines)


def _run_json(command: list[str], cwd: Path) -> dict:
    """Run a scanner and parse its JSON stdout.

    The scanners exit non-zero when advisories are found, so the exit code is
    ignored; only empty output is treated as a hard failure.
    """
    proc = subprocess.run(command, capture_output=True, text=True, cwd=cwd)  # noqa: S603
    if not proc.stdout.strip():
        raise RuntimeError(
            f"`{' '.join(command)}` produced no JSON (exit {proc.returncode}).\n"
            f"stderr:\n{proc.stderr}"
        )
    return json.loads(proc.stdout)


def run_pip_audit() -> dict:
    """Run ``pip-audit`` against the installed environment and return its JSON."""
    return _run_json(["pip-audit", "--format=json"], cwd=REPO_ROOT)


def run_npm_audit() -> dict:
    """Run ``npm audit`` in the frontend directory and return its JSON."""
    return _run_json(["npm", "audit", "--json"], cwd=FRONTEND_DIR)


def main(argv: list[str] | None = None) -> int:
    """Run both scanners and gate the build on new advisories.

    Returns:
        ``0`` when the scan passes (or the baseline is updated), ``1`` otherwise.
    """
    parser = argparse.ArgumentParser(description="CI dependency vulnerability scan gate.")
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Snapshot current advisories to the baseline file instead of gating.",
    )
    args = parser.parse_args(argv)

    pip_report = run_pip_audit()
    npm_report = run_npm_audit()

    if args.update_baseline:
        document = build_baseline(pip_report, npm_report)
        BASELINE_PATH.write_text(json.dumps(document, indent=2) + "\n")
        print(f"Baseline written to {BASELINE_PATH}")
        return 0

    result = evaluate(pip_report, npm_report, load_baseline(BASELINE_PATH))
    print(format_report(result))
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
