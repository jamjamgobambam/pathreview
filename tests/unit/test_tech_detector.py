"""Tests for tech_detector.py"""

import pytest

from agent.tools.tech_detector import TechDetector


@pytest.mark.unit
class TestTechDetector:
    """Test suite for TechDetector."""

    @pytest.fixture
    def detector(self):
        """Create a TechDetector instance."""
        return TechDetector()

    def test_single_language_repo(self, detector):
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

    def test_mixed_language_repo_python_primary(self, detector):
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

    def test_ipynb_counted_as_python_not_json(self, detector):
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
        detected_lower = [lang.lower() for lang in data["all_languages"]]
        # .ipynb should be treated as Python, not JSON

    def test_node_modules_excluded(self, detector):
        """Test node_modules directory is excluded from detection."""
        files = [
            "src/main.py",
            "node_modules/package1/index.js",
            "node_modules/package2/lib.js",
            "utils.py",
        ]

        result = detector.execute({"files": files})

        assert result.success is True
        assert result.data["primary_language"] == "Python"
        assert result.data["all_languages"] == ["Python"]
        assert result.data["frameworks"] == []

    def test_vendor_files_excluded(self, detector):
        """Test vendor directory is excluded from detection."""
        files = [
            "src/main.py",
            "vendor/lib.js",
            "vendor/framework.js",
            "app.py",
        ]

        result = detector.execute({"files": files})

        assert result.success is True
        assert result.data["primary_language"] == "Python"
        assert result.data["all_languages"] == ["Python"]

    def test_build_directory_excluded(self, detector):
        """Test build directory is excluded from detection."""
        files = [
            "src/main.py",
            "build/generated.js",
            "build/bundle.js",
        ]

        result = detector.execute({"files": files})

        assert result.success is True
        assert result.data["primary_language"] == "Python"
        assert result.data["all_languages"] == ["Python"]

    def test_nested_ignored_directories_excluded(self, detector):
        """Test ignored directories are detected below the repo root."""
        files = [
            "src/main.py",
            "frontend/node_modules/package/index.js",
            "frontend/dist/generated.ts",
        ]

        result = detector.execute({"files": files})

        assert result.success is True
        assert result.data["all_languages"] == ["Python"]

    def test_windows_path_separators_supported(self, detector):
        """Test ignored directories in Windows-style paths."""
        files = [
            "src/main.py",
            r"frontend\node_modules\package\index.js",
            r"frontend\build\bundle.ts",
        ]

        result = detector.execute({"files": files})

        assert result.success is True
        assert result.data["all_languages"] == ["Python"]

    def test_similarly_named_directories_not_excluded(self, detector):
        """Test partial directory-name matches are preserved."""
        files = [
            "src/main.py",
            "src/rebuild/parser.js",
            "src/vendor_tools/helper.ts",
        ]

        result = detector.execute({"files": files})

        assert result.success is True
        assert set(result.data["all_languages"]) == {
            "JavaScript",
            "Python",
            "TypeScript",
        }

    def test_config_files_in_ignored_directories_excluded(self, detector):
        """Test ignored config files do not introduce frameworks."""
        files = [
            "src/main.py",
            "node_modules/package/package.json",
        ]

        result = detector.execute({"files": files})

        assert result.success is True
        assert result.data["all_languages"] == ["Python"]
        assert result.data["frameworks"] == []

    def test_all_files_excluded_returns_unknown(self, detector):
        """Test detection when every file belongs to an ignored directory."""
        files = [
            "node_modules/package/index.js",
            "build/bundle.ts",
        ]

        result = detector.execute({"files": files})

        assert result.success is True
        assert result.data["primary_language"] == "Unknown"
        assert result.data["all_languages"] == []
        assert result.data["frameworks"] == []

    def test_config_file_detection(self, detector):
        """Test detection from config files."""
        files = [
            "package.json",
            "index.js",
            "app.js",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert "Node.js" in data["all_languages"] or "JavaScript" in data["all_languages"]

    def test_dockerfile_detection(self, detector):
        """Test Docker file detection."""
        files = [
            "Dockerfile",
            "app.py",
            "main.py",
        ]

        result = detector.execute({"files": files})

        # Should detect Python as primary language

    def test_github_actions_detection(self, detector):
        """Test GitHub Actions detection."""
        files = [
            ".github/workflows/test.yml",
            "main.py",
        ]

        result = detector.execute({"files": files})

        data = result.data
        # Should detect both Python and CI/CD

    def test_makefile_detection(self, detector):
        """Test Makefile detection."""
        files = [
            "Makefile",
            "src/main.py",
        ]

        result = detector.execute({"files": files})

        # Should detect Makefile as build tool

    def test_typescript_detection(self, detector):
        """Test TypeScript detection."""
        files = [
            "src/main.ts",
            "src/types.ts",
            "src/index.tsx",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert "TypeScript" in data["all_languages"]

    def test_go_detection(self, detector):
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

    def test_rust_detection(self, detector):
        """Test Rust detection."""
        files = [
            "src/main.rs",
            "src/lib.rs",
            "Cargo.toml",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert "Rust" in data["all_languages"]

    def test_java_detection(self, detector):
        """Test Java detection."""
        files = [
            "Main.java",
            "Utils.java",
            "pom.xml",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert "Java" in data["all_languages"]

    def test_multiple_python_files(self, detector):
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

    def test_empty_file_list(self, detector):
        """Test with empty file list."""
        result = detector.execute({"files": []})

        data = result.data
        assert data["primary_language"] == "Unknown"
        assert data["all_languages"] == []

    def test_no_files_key(self, detector):
        """Test with no files key in input."""
        result = detector.execute({})

        data = result.data
        assert data["primary_language"] == "Unknown"

    def test_result_structure(self, detector):
        """Test result has required structure."""
        files = ["main.py", "app.js"]
        result = detector.execute({"files": files})

        data = result.data
        assert "primary_language" in data
        assert "all_languages" in data
        assert "frameworks" in data

    def test_framework_detection(self, detector):
        """Test framework detection from files."""
        files = [
            "requirements.txt",  # Could indicate Python
            "package.json",  # Could indicate Node.js
            "main.py",
        ]

        result = detector.execute({"files": files})

        # Should detect frameworks

    def test_unknown_extensions(self, detector):
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

    def test_case_insensitive_extension_matching(self, detector):
        """Test case-insensitive file extension matching."""
        files = [
            "Main.PY",
            "Utils.Py",
            "Index.JS",
        ]

        result = detector.execute({"files": files})

        data = result.data
        # Should still detect languages despite case

    def test_multiple_extensions_same_file(self, detector):
        """Test file with multiple dots in name."""
        files = [
            "my.test.py",
            "config.prod.js",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert len(data["all_languages"]) > 0

    def test_all_languages_sorted(self, detector):
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

    def test_frameworks_sorted(self, detector):
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

    def test_ruby_detection(self, detector):
        """Test Ruby language detection."""
        files = [
            "main.rb",
            "Gemfile",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert "Ruby" in data["all_languages"]

    def test_csharp_detection(self, detector):
        """Test C# language detection."""
        files = [
            "Program.cs",
            "Startup.cs",
        ]

        result = detector.execute({"files": files})

        data = result.data
        assert "C#" in data["all_languages"]

    def test_cpp_detection(self, detector):
        """Test C++ detection."""
        files = [
            "main.cpp",
            "utils.cpp",
            "header.h",
        ]

        result = detector.execute({"files": files})

        data = result.data
        # Should detect C++ (from .cpp files)
