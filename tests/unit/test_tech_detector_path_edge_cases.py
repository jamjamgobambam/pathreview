"""Edge-case tests for TechDetector path filtering."""

import pytest

from agent.tools.tech_detector import TechDetector


@pytest.mark.unit
class TestTechDetectorPathEdgeCases:
    """Test vendored and generated directory path handling."""

    def test_windows_style_paths_are_excluded(self) -> None:
        """Exclude vendored and build directories using Windows separators."""
        detector = TechDetector()
        files = [
            r"src\main.py",
            r"frontend\node_modules\package\index.js",
            r"frontend\build\bundle.js",
        ]

        result = detector.execute({"files": files})

        assert result.success is True
        assert result.data["primary_language"] == "Python"
        assert result.data["all_languages"] == ["Python"]

    def test_deeply_nested_vendored_paths_are_excluded(self) -> None:
        """Exclude deeply nested dependency and build-output paths."""
        detector = TechDetector()
        files = [
            "src/main.py",
            "src/node_modules/pkg/sub/file.js",
            "frontend/build/assets/vendor.js",
        ]

        result = detector.execute({"files": files})

        assert result.success is True
        assert result.data["primary_language"] == "Python"
        assert result.data["all_languages"] == ["Python"]

    def test_filename_matching_directory_name_is_not_excluded(self) -> None:
        """Keep normal source files whose names resemble skipped directories."""
        detector = TechDetector()
        files = [
            "src/main.py",
            "src/node_modules.py",
            "src/build.py",
        ]

        result = detector.execute({"files": files})

        assert result.success is True
        assert result.data["primary_language"] == "Python"
        assert result.data["all_languages"] == ["Python"]
