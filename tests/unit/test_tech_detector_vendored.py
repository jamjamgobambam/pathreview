"""Regression tests for issue #150 — tech detector counts vendored/build files.

See https://github.com/ascherj/pathreview/issues/150.

These live in a dedicated file to keep the fix focused on #150. The root-level
``node_modules``/``build`` cases are also asserted by ``test_tech_detector.py``
(``test_node_modules_excluded``, ``test_build_directory_excluded``); the cases
below additionally cover nested directories, Windows path separators, and
look-alike directory names that must NOT be skipped.
"""

import pytest

from agent.tools.tech_detector import TechDetector


@pytest.mark.unit
class TestTechDetectorVendoredExclusion:
    """TechDetector must exclude vendored/build dirs by path segment."""

    @pytest.fixture
    def detector(self) -> TechDetector:
        """Create a TechDetector instance."""
        return TechDetector()

    def test_vendor_dir_at_root_excluded(self, detector: TechDetector) -> None:
        """A root-level vendor/ directory must not count toward languages."""
        files = [
            "src/main.py",
            "vendor/lib.js",
            "vendor/framework.js",
            "app.py",
        ]

        data = detector.execute({"files": files}).data

        assert data["primary_language"] == "Python"
        assert "JavaScript" not in data["all_languages"]

    def test_node_modules_at_root_excluded(self, detector: TechDetector) -> None:
        """A root-level node_modules/ directory must not count toward languages."""
        files = [
            "app.py",
            "node_modules/react/index.js",
            "node_modules/react/umd.js",
        ]

        data = detector.execute({"files": files}).data

        assert data["primary_language"] == "Python"
        assert "JavaScript" not in data["all_languages"]

    def test_build_dir_with_windows_separators_excluded(self, detector: TechDetector) -> None:
        """Build output is skipped even when paths use Windows separators."""
        files = [
            "src\\main.py",
            "build\\generated.js",
            "build\\bundle.js",
        ]

        data = detector.execute({"files": files}).data

        assert data["primary_language"] == "Python"
        assert "JavaScript" not in data["all_languages"]

    def test_nested_vendored_dir_excluded(self, detector: TechDetector) -> None:
        """Vendored dirs nested below the repo root are also skipped."""
        files = [
            "app.py",
            "packages/web/node_modules/react/index.js",
            "packages/web/node_modules/react/umd.js",
        ]

        data = detector.execute({"files": files}).data

        assert data["primary_language"] == "Python"
        assert "JavaScript" not in data["all_languages"]

    def test_lookalike_dirs_not_skipped(self, detector: TechDetector) -> None:
        """Names that merely resemble vendored dirs must NOT be skipped."""
        files = [
            "distribution/app.py",
            "rebuild.py",
            "src/builder/main.py",
        ]

        data = detector.execute({"files": files}).data

        assert data["primary_language"] == "Python"
        assert "Python" in data["all_languages"]
