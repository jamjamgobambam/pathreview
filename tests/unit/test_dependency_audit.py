"""Tests for scripts/dependency_audit.py"""

import json

import pytest

from scripts.dependency_audit import (
    Advisory,
    Baseline,
    build_baseline,
    evaluate,
    format_report,
    gated_npm,
    load_baseline,
    new_advisories,
    parse_npm_audit,
    parse_pip_audit,
)

# A pip-audit --format=json report with one advisory (no severity field, as
# pip-audit does not emit one).
PIP_AUDIT_REPORT = {
    "dependencies": [
        {
            "name": "chromadb",
            "version": "1.5.9",
            "vulns": [
                {
                    "id": "PYSEC-2026-311",
                    "fix_versions": [],
                    "description": "A pre-authentication code injection vulnerability.",
                }
            ],
        },
        {"name": "fastapi", "version": "0.115.0", "vulns": []},
    ]
}

# An npm audit --json report mixing severities. String `via` entries are
# transitive references and must not be double-counted.
NPM_AUDIT_REPORT = {
    "vulnerabilities": {
        "vitest": {
            "severity": "critical",
            "via": [{"source": 1120126, "severity": "critical", "title": "Vitest UI RCE"}],
        },
        "ws": {
            "severity": "high",
            "via": [
                {"source": 1123259, "severity": "high", "title": "ws DoS"},
                {"source": 1119108, "severity": "moderate", "title": "ws memory disclosure"},
            ],
        },
        "esbuild": {
            "severity": "moderate",
            "via": [{"source": 1102341, "severity": "moderate", "title": "esbuild dev server"}],
        },
        "vite": {
            "severity": "high",
            # Transitive reference to esbuild's advisory, plus a real one.
            "via": ["esbuild", {"source": 1123525, "severity": "high", "title": "vite fs.deny"}],
        },
    }
}


@pytest.mark.unit
class TestParsePipAudit:
    """Test suite for pip-audit report parsing."""

    def test_extracts_advisory_ids(self):
        """Advisory ids are extracted for packages that have vulns."""
        advisories = parse_pip_audit(PIP_AUDIT_REPORT)

        assert [a.advisory_id for a in advisories] == ["PYSEC-2026-311"]
        assert advisories[0].ecosystem == "python"
        assert advisories[0].package == "chromadb"
        assert advisories[0].severity == ""  # pip-audit provides no severity

    def test_ignores_clean_packages(self):
        """Packages with an empty vulns list contribute no advisories."""
        advisories = parse_pip_audit(PIP_AUDIT_REPORT)

        assert all(a.package != "fastapi" for a in advisories)

    def test_accepts_bare_list_format(self):
        """A top-level list of dependency records is tolerated."""
        report = PIP_AUDIT_REPORT["dependencies"]

        advisories = parse_pip_audit(report)

        assert [a.advisory_id for a in advisories] == ["PYSEC-2026-311"]

    def test_empty_report_yields_no_advisories(self):
        """An empty report produces an empty list rather than crashing."""
        assert parse_pip_audit({}) == []
        assert parse_pip_audit({"dependencies": []}) == []


@pytest.mark.unit
class TestParseNpmAudit:
    """Test suite for npm audit report parsing."""

    def test_extracts_each_source_advisory(self):
        """One advisory is produced per dict `via` entry."""
        advisories = parse_npm_audit(NPM_AUDIT_REPORT)
        ids = {a.advisory_id for a in advisories}

        assert ids == {"1120126", "1123259", "1119108", "1102341", "1123525"}

    def test_skips_string_via_references(self):
        """String `via` entries (transitive refs) are not counted."""
        advisories = parse_npm_audit(NPM_AUDIT_REPORT)

        # "esbuild" appears as a string via under vite but must not add an entry.
        vite_entries = [a for a in advisories if a.package == "vite"]
        assert [a.advisory_id for a in vite_entries] == ["1123525"]

    def test_severity_is_lowercased(self):
        """Severities are normalised to lower case for comparison."""
        advisories = parse_npm_audit(NPM_AUDIT_REPORT)
        crit = next(a for a in advisories if a.advisory_id == "1120126")

        assert crit.severity == "critical"

    def test_empty_report_yields_no_advisories(self):
        """A report with no vulnerabilities returns an empty list."""
        assert parse_npm_audit({}) == []
        assert parse_npm_audit({"vulnerabilities": {}}) == []


@pytest.mark.unit
class TestGatedNpm:
    """Test suite for the npm severity threshold."""

    def test_keeps_only_high_and_critical(self):
        """Moderate and low advisories are dropped; high/critical are kept."""
        gated = gated_npm(parse_npm_audit(NPM_AUDIT_REPORT))
        ids = {a.advisory_id for a in gated}

        assert ids == {"1120126", "1123259", "1123525"}  # critical + two high

    def test_drops_everything_below_threshold(self):
        """A report of only moderate advisories gates to nothing."""
        report = {
            "vulnerabilities": {
                "esbuild": {"severity": "moderate", "via": [{"source": 1, "severity": "moderate"}]}
            }
        }

        assert gated_npm(parse_npm_audit(report)) == []


@pytest.mark.unit
class TestNewAdvisories:
    """Test suite for baseline diffing."""

    def test_returns_only_ids_absent_from_baseline(self):
        """Advisories already in the baseline are filtered out."""
        current = [
            Advisory("npm", "1123259", "ws", "high", ""),
            Advisory("npm", "9999999", "left-pad", "high", ""),
        ]

        result = new_advisories(current, frozenset({"1123259"}))

        assert [a.advisory_id for a in result] == ["9999999"]

    def test_empty_baseline_returns_all(self):
        """With no baseline, every advisory is considered new."""
        current = [Advisory("python", "PYSEC-1", "pkg", "", "")]

        assert new_advisories(current, frozenset()) == current


@pytest.mark.unit
class TestEvaluate:
    """Test suite for the end-to-end evaluation against a baseline."""

    def test_passes_when_baseline_covers_everything(self):
        """A baseline covering all current advisories yields a passing result."""
        baseline = Baseline(
            python=frozenset({"PYSEC-2026-311"}),
            npm=frozenset({"1120126", "1123259", "1123525"}),
        )

        result = evaluate(PIP_AUDIT_REPORT, NPM_AUDIT_REPORT, baseline)

        assert result.passed
        assert result.new_python == []
        assert result.new_npm == []

    def test_fails_on_new_python_advisory(self):
        """A Python advisory not in the baseline fails the scan."""
        baseline = Baseline(
            python=frozenset(),
            npm=frozenset({"1120126", "1123259", "1123525"}),
        )

        result = evaluate(PIP_AUDIT_REPORT, NPM_AUDIT_REPORT, baseline)

        assert not result.passed
        assert [a.advisory_id for a in result.new_python] == ["PYSEC-2026-311"]

    def test_fails_on_new_high_npm_advisory(self):
        """A new high/critical npm advisory fails the scan."""
        baseline = Baseline(
            python=frozenset({"PYSEC-2026-311"}),
            npm=frozenset({"1120126", "1123259"}),  # missing the vite 'high'
        )

        result = evaluate(PIP_AUDIT_REPORT, NPM_AUDIT_REPORT, baseline)

        assert not result.passed
        assert [a.advisory_id for a in result.new_npm] == ["1123525"]

    def test_ignores_new_moderate_npm_advisory(self):
        """A brand-new moderate npm advisory does not fail the scan."""
        report = {
            "vulnerabilities": {
                "left-pad": {
                    "severity": "moderate",
                    "via": [{"source": 8888888, "severity": "moderate", "title": "x"}],
                }
            }
        }
        baseline = Baseline(python=frozenset(), npm=frozenset())

        result = evaluate({"dependencies": []}, report, baseline)

        assert result.passed


@pytest.mark.unit
class TestBaselineIO:
    """Test suite for loading and building the baseline document."""

    def test_missing_file_loads_empty_baseline(self, tmp_path):
        """A non-existent baseline path yields empty sets, not an error."""
        baseline = load_baseline(tmp_path / "does-not-exist.json")

        assert baseline.python == frozenset()
        assert baseline.npm == frozenset()

    def test_round_trips_through_disk(self, tmp_path):
        """A built baseline can be written and reloaded to the same ids."""
        document = build_baseline(PIP_AUDIT_REPORT, NPM_AUDIT_REPORT)
        path = tmp_path / "audit-baseline.json"
        path.write_text(json.dumps(document))

        baseline = load_baseline(path)

        assert baseline.python == frozenset({"PYSEC-2026-311"})
        # Only high/critical npm ids are baselined.
        assert baseline.npm == frozenset({"1120126", "1123259", "1123525"})

    def test_build_baseline_is_documented(self):
        """The generated baseline carries an explanatory comment."""
        document = build_baseline(PIP_AUDIT_REPORT, NPM_AUDIT_REPORT)

        assert "_comment" in document
        assert "--update-baseline" in document["_comment"]


@pytest.mark.unit
class TestFormatReport:
    """Test suite for the human-readable report."""

    def test_passing_report_is_concise(self):
        """A passing result reports success on a single line."""
        result = evaluate({"dependencies": []}, {}, Baseline(frozenset(), frozenset()))

        assert "passed" in format_report(result).lower()

    def test_failing_report_lists_advisories(self):
        """A failing result names each new advisory and how to resolve it."""
        result = evaluate(PIP_AUDIT_REPORT, NPM_AUDIT_REPORT, Baseline(frozenset(), frozenset()))

        message = format_report(result)

        assert "FAILED" in message
        assert "PYSEC-2026-311" in message
        assert "audit-baseline.json" in message
