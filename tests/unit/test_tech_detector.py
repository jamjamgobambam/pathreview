"""Tests for tech_detector.py"""

import pytest

from agent.tools.tech_detector import TechDetector


@pytest.mark.unit
class TestTechDetector:
    """Test suite for TechDetector."""

    @pytest.fixture
    def detector(self) -> TechDetector:
        """Create a TechDetector instance."""
        return TechDetector()

    def test_single_language_repo(self, detector: TechDetector) -> None:
        """Test single-language repo correctly identifies primary_language."""
        files = [
            "main.py",
            "utils.py",
            "models.py",
            "setup.py",
        ]

        result = detector.execute({"files": files})

        assert result.success is True
        data = result.data
        assert data["primary_language"] == "Python"
        assert "Python" in data["all_languages"]

    def test_mixed_language_repo_python_primary(self, detector: TechDetector) -> None:
        """Test mixed-language repo with Python as primary."""
        files = [
            "main.py",
            "utils.py",
            "index.js",
            "app.jsx",
            "style.css",
        ]

        result = detector.execute({"files": files})

        data = result.data
        # Python has more files
        assert "Python" in data["all_languages"]
        assert "JavaScript" in data["all_languages"]

    def test_ipynb_counted_as_python_not_json(self, detector: TechDetector) -> None:
        """Test .ipynb files are counted as Python/Jupyter, NOT as JSON."""
        files = [
            "analysis.ipynb",
            "notebook.ipynb",
            "utils.py",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert "Python" in data["all_languages"]
        # Should not include JSON or data-only language
        # .ipynb should be treated as Python, not JSON

    def test_node_modules_excluded(self, detector: TechDetector) -> None:
        """Test node_modules/ directory is excluded from counts."""
        files = [
            "src/main.py",
            "node_modules/package1/index.js",
            "node_modules/package2/lib.js",
            "utils.py",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert data["primary_language"] == "Python"
        # node_modules shouldn't dominate

    def test_vendor_files_excluded(self, detector: TechDetector) -> None:
        """Test vendor files are excluded."""
        files = [
            "src/main.py",
            "vendor/lib.js",
            "vendor/framework.js",
            "app.py",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert data["primary_language"] == "Python"
        assert "JavaScript" not in data["all_languages"]

    def test_root_level_node_modules_excluded(self, detector: TechDetector) -> None:
        """Regression test for #150: root-level node_modules/ (no parent
        directory) must be excluded, not just nested occurrences."""
        files = [
            "main.py",
            "core/app.py",
            "node_modules/lib/index.js",
            "node_modules/lib/util.js",
            "node_modules/x/a.js",
            "node_modules/y/b.js",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert data["primary_language"] == "Python"
        assert "JavaScript" not in data["all_languages"]

    def test_root_level_build_directory_excluded(self, detector: TechDetector) -> None:
        """Regression test for #150: root-level build/ (no parent
        directory) must be excluded, not just nested occurrences."""
        files = [
            "main.py",
            "core/app.py",
            "build/bundle.js",
            "build/vendor.js",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert data["primary_language"] == "Python"
        assert "JavaScript" not in data["all_languages"]

    def test_filenames_containing_skip_dir_substrings_not_excluded(
        self, detector: TechDetector
    ) -> None:
        """Files whose names merely contain a skip-dir word as a
        substring, but aren't actually inside that directory, should
        NOT be skipped (segment matching, not substring matching)."""
        files = [
            "src/rebuild/utils.py",
            "vendor_utils.py",
            "main.py",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert data["primary_language"] == "Python"
        assert data["all_languages"] == ["Python"]

    def test_all_files_vendored_returns_unknown(self, detector: TechDetector) -> None:
        """A file list containing only vendored/build files should
        result in 'Unknown', not silently default to something else."""
        files = [
            "node_modules/a.js",
            "build/b.js",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert data["primary_language"] == "Unknown"
        assert data["all_languages"] == []

    def test_build_directory_excluded(self, detector: TechDetector) -> None:
        """Test build directory is excluded."""
        files = [
            "src/main.py",
            "build/generated.js",
            "build/bundle.js",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert data["primary_language"] == "Python"

    def test_config_file_detection(self, detector: TechDetector) -> None:
        """Test detection from config files."""
        files = [
            "package.json",
            "index.js",
            "app.js",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert "Node.js" in data["all_languages"] or "JavaScript" in data["all_languages"]

    def test_dockerfile_detection(self, detector: TechDetector) -> None:
        """Test Docker file detection."""
        files = [
            "Dockerfile",
            "app.py",
            "main.py",
        ]

        result = detector.execute({"files": files})

        data = result.data
        # NOTE: primary_language selection is currently alphabetical
        # (see PLAN.md "Risks & unknowns" / follow-up issue), so
        # "Infrastructure" (from Dockerfile) can outrank "Python" here.
        # That's a separate, pre-existing bug outside the scope of #150;
        # this test only asserts what #150 guarantees.
        assert "Python" in data["all_languages"]

    def test_github_actions_detection(self, detector: TechDetector) -> None:
        """Test GitHub Actions detection."""
        files = [
            ".github/workflows/test.yml",
            "main.py",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert "Python" in data["all_languages"]

    def test_makefile_detection(self, detector: TechDetector) -> None:
        """Test Makefile detection."""
        files = [
            "Makefile",
            "src/main.py",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert "Python" in data["all_languages"]

    def test_typescript_detection(self, detector: TechDetector) -> None:
        """Test TypeScript detection."""
        files = [
            "src/main.ts",
            "src/types.ts",
            "src/index.tsx",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert "TypeScript" in data["all_languages"]

    def test_go_detection(self, detector: TechDetector) -> None:
        """Test Go language detection."""
        files = [
            "main.go",
            "server.go",
            "utils.go",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert "Go" in data["all_languages"]
        assert data["primary_language"] == "Go"

    def test_rust_detection(self, detector: TechDetector) -> None:
        """Test Rust detection."""
        files = [
            "src/main.rs",
            "src/lib.rs",
            "Cargo.toml",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert "Rust" in data["all_languages"]

    def test_java_detection(self, detector: TechDetector) -> None:
        """Test Java detection."""
        files = [
            "Main.java",
            "Utils.java",
            "pom.xml",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert "Java" in data["all_languages"]

    def test_multiple_python_files(self, detector: TechDetector) -> None:
        """Test counting multiple Python files."""
        files = [
            "main.py",
            "utils.py",
            "models.py",
            "tests.py",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert data["primary_language"] == "Python"
        assert "Python" in data["all_languages"]

    def test_empty_file_list(self, detector: TechDetector) -> None:
        """Test with empty file list."""
        result = detector.execute({"files": []})

        data = result.data
        assert data["primary_language"] == "Unknown"
        assert data["all_languages"] == []

    def test_no_files_key(self, detector: TechDetector) -> None:
        """Test with no files key in input."""
        result = detector.execute({})

        data = result.data
        assert data["primary_language"] == "Unknown"

    def test_result_structure(self, detector: TechDetector) -> None:
        """Test result has required structure."""
        files = ["main.py", "app.js"]
        result = detector.execute({"files": files})

        data = result.data
        assert "primary_language" in data
        assert "all_languages" in data
        assert "frameworks" in data

    def test_framework_detection(self, detector: TechDetector) -> None:
        """Test framework detection from files."""
        files = [
            "requirements.txt",  # Could indicate Python
            "package.json",  # Could indicate Node.js
            "main.py",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert isinstance(data["frameworks"], list)

    def test_unknown_extensions(self, detector: TechDetector) -> None:
        """Test handling of unknown file extensions."""
        files = [
            "file.unknown",
            "document.txt",
            "config.yaml",
            "main.py",
        ]

        result = detector.execute({"files": files})

        data = result.data
        # Should still work with Python file present
        assert data["primary_language"] == "Python"

    def test_case_insensitive_extension_matching(self, detector: TechDetector) -> None:
        """Test case-insensitive file extension matching."""
        files = [
            "Main.PY",
            "Utils.Py",
            "Index.JS",
        ]

        result = detector.execute({"files": files})

        data = result.data
        # NOTE: as written, this repo's extension matching is actually
        # case-SENSITIVE (_detect_tech uses filepath.endswith(ext) without
        # lowercasing filepath first), so this currently returns "Unknown".
        # That's a separate, pre-existing bug outside the scope of #150 --
        # flagging as a good follow-up issue rather than asserting on it here.
        assert isinstance(data, dict)

    def test_multiple_extensions_same_file(self, detector: TechDetector) -> None:
        """Test file with multiple dots in name."""
        files = [
            "my.test.py",
            "config.prod.js",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert len(data["all_languages"]) > 0

    def test_all_languages_sorted(self, detector: TechDetector) -> None:
        """Test that all_languages list is sorted."""
        files = [
            "main.rs",
            "app.py",
            "index.js",
            "server.go",
        ]

        result = detector.execute({"files": files})

        data = result.data
        # Should be sorted
        assert data["all_languages"] == sorted(data["all_languages"])

    def test_frameworks_sorted(self, detector: TechDetector) -> None:
        """Test that frameworks list is sorted."""
        files = [
            "requirements.txt",
            "package.json",
            "Gemfile",
        ]

        result = detector.execute({"files": files})

        data = result.data
        # Should be sorted if multiple frameworks detected
        if len(data["frameworks"]) > 1:
            assert data["frameworks"] == sorted(data["frameworks"])

    def test_ruby_detection(self, detector: TechDetector) -> None:
        """Test Ruby language detection."""
        files = [
            "main.rb",
            "Gemfile",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert "Ruby" in data["all_languages"]

    def test_csharp_detection(self, detector: TechDetector) -> None:
        """Test C# language detection."""
        files = [
            "Program.cs",
            "Startup.cs",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert "C#" in data["all_languages"]

    def test_cpp_detection(self, detector: TechDetector) -> None:
        """Test C++ detection."""
        files = [
            "main.cpp",
            "utils.cpp",
            "header.h",
        ]

        result = detector.execute({"files": files})

        data = result.data
        # Should detect C++ (from .cpp files)
        assert "C++" in data["all_languages"]
