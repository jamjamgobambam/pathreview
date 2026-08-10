"""Tests for readme_scorer.py"""

import pytest

from agent.tools.readme_scorer import ReadmeScorer


@pytest.mark.unit
class TestReadmeScorer:
    """Test suite for ReadmeScorer."""

    @pytest.fixture
    def scorer(self):
        """Create a ReadmeScorer instance."""
        return ReadmeScorer()

    def test_readme_with_all_quality_signals(self, scorer):
        """Test README with all quality signals returns high score."""
        readme = """
        # Project Name

        Project Name is a production-ready portfolio review platform that helps
        developers analyze project documentation, identify missing information,
        and present their work more clearly to technical reviewers. The project
        focuses on dependable scoring, transparent feedback, and maintainable
        architecture so that contributors can understand how each result is
        produced and how each part of the system can be improved over time.

        The application accepts project content, evaluates documentation quality,
        and returns structured signals that describe whether a README contains the
        information expected from a complete software project. These signals help
        users improve installation instructions, usage examples, feature summaries,
        technology descriptions, deployment references, and supporting links.

        ## Installation

        Create and activate a virtual environment before installing dependencies.
        This keeps project packages separate from other Python applications on the
        same machine and makes local development easier to reproduce.

        ```bash
        python -m venv .venv
        source .venv/bin/activate
        pip install package
        ```

        On Windows PowerShell, activate the environment with the appropriate script
        from the `.venv` directory. After installation, copy the example environment
        file, provide the required configuration values, and confirm that the local
        database or other dependent services are available before starting the app.

        ## Usage

        Import the package and run the main application entry point. The package can
        be used from Python code, automated scripts, or an API service depending on
        the integration needs of the project.

        ```python
        import package

        result = package.run()
        print(result)
        ```

        Users can provide README content and inspect the returned quality signals.
        Each response includes the detected word count, word-count category, section
        indicators, badge detection, demo-link detection, technology-section
        detection, and an overall score. These values can be displayed in a user
        interface or used by another service to generate improvement suggestions.

        ## Features

        - Detects whether README content exists and contains meaningful text.
        - Calculates the total number of whitespace-separated words.
        - Categorizes documentation as minimal, adequate, or comprehensive.
        - Detects installation, setup, and getting-started instructions.
        - Detects usage, quickstart, and example sections.
        - Recognizes build, coverage, license, and status badges.
        - Identifies live demos, hosted examples, and try-it links.
        - Detects technology, tech-stack, and built-with sections.
        - Produces a normalized overall quality score.
        - Returns structured data that is easy to test and integrate.

        ## Tech Stack

        - Python 3.9 or newer for the core application and tests.
        - FastAPI for typed request handling and service endpoints.
        - PostgreSQL for persistent application and review data.
        - Pytest for focused unit tests and regression coverage.
        - Ruff for linting, import organization, and formatting checks.
        - Structured logging for readable development and production diagnostics.

        ## Architecture

        The application uses a modular architecture that separates API handling,
        business logic, persistence, scoring tools, and tests. Request validation is
        handled near the system boundary, while reusable scoring behavior lives in
        focused modules. This separation reduces coupling and makes it easier to add
        new quality signals without rewriting unrelated features.

        Service modules coordinate application behavior and return consistent data
        structures. Database access is isolated so that tests can replace external
        dependencies with mocks or fixtures. Logging captures useful operational
        context without changing the result returned to callers. The design favors
        small functions, explicit inputs, predictable outputs, and targeted tests.

        ## Development

        Contributors should review the contribution guide before changing code.
        Work should be completed on a clearly named branch, divided into small
        sub-tasks, and committed frequently so progress is visible. Each code change
        should include relevant tests that follow the patterns already established
        in the surrounding unit-test files.

        Before opening a pull request, contributors should run focused tests for the
        modified module, then run the complete unit-test command and the full project
        checks. Any failures that existed before the change should be documented so
        reviewers can distinguish pre-existing issues from newly introduced ones.

        ## Testing

        The test suite covers successful inputs, empty content, boundary conditions,
        section detection, score calculations, and expected result fields. Focused
        tests make it easier to diagnose failures because each test describes one
        behavior. Regression tests protect previously reported issues from returning.

        Contributors should run the smallest relevant test first while developing.
        After the focused test passes, they should run the complete test file and
        then the full unit-test suite. Test data should be realistic enough to match
        the expectations being asserted. In particular, a fixture described as
        comprehensive should actually contain enough content to reach that category.

        ## Configuration

        Environment-specific values should be stored outside source control. The
        example environment file documents supported settings without exposing real
        credentials. Developers should verify database URLs, API keys, service hosts,
        and feature flags before starting the application. Production deployments
        should use secure secret management and least-privilege access.

        ## Deployment

        The project can be deployed with containers or a standard Python runtime.
        A reliable deployment should install locked dependencies, apply migrations,
        validate required environment variables, start the API service, and expose a
        health endpoint for monitoring. Teams should test changes in a staging
        environment before releasing them to users.

        ## Troubleshooting

        Common development problems include missing packages, inactive virtual
        environments, unavailable databases, incorrect environment variables, and
        unsupported Python versions. Developers should inspect the full error output,
        reproduce the issue with the smallest command possible, and compare results
        before and after their changes. Focused tests and structured logs usually make
        the source of a failure easier to identify.

        ## Security

        Input should be validated before processing, and sensitive values should not
        be written to logs or committed to the repository. Dependencies should be
        reviewed regularly, credentials should be rotated when necessary, and access
        should follow the principle of least privilege. Security-related behavior
        should be covered by tests just like other application requirements.

        ## Contributing

        Pull requests should explain the problem, summarize the implementation, list
        the tests performed, and mention any known limitations or pre-existing
        failures. Reviewers should be able to understand why the change is needed,
        how it works, and whether it preserves existing behavior. Feedback should be
        addressed before a draft pull request is marked ready for review.

        ## Maintenance

        Maintainers should keep dependencies current, review open issues, improve
        documentation, and remove obsolete code when it is safe to do so. Regular
        cleanup keeps the project understandable as new features are added. Clear
        ownership, small pull requests, and reliable automated checks help prevent
        technical debt from growing unnoticed.

        ## Project Goals

        The project is designed to provide a dependable, understandable, and
        extensible foundation for documentation analysis. Its structure emphasizes
        maintainability, clear feedback, predictable scoring, realistic test data,
        and strong automated verification across the development lifecycle. The
        system should help users improve their project presentation while giving
        contributors a codebase that is straightforward to review and extend.

        ![Build Status](https://example.com/badge.svg)
        ![Coverage](https://example.com/coverage.svg)

        ## Live Demo

        [Try it here](https://demo.example.com)
        """

        result = scorer.execute({"readme_content": readme})

        assert result.success is True
        data = result.data
        assert data["has_readme"] is True
        assert data["word_count"] > 500
        assert data["word_count_category"] == "comprehensive"
        assert data["has_installation_section"] is True
        assert data["has_usage_section"] is True
        assert data["has_badges"] is True
        assert data["has_demo_link"] is True
        assert data["has_tech_stack_section"] is True
        assert data["overall_score"] > 0.7  # Should be high

    def test_readme_with_no_content(self, scorer):
        """Test README with no content returns score of 0.0."""
        result = scorer.execute({"readme_content": ""})

        assert result.success is True
        data = result.data
        assert data["has_readme"] is False
        assert data["word_count"] == 0
        assert data["word_count_category"] == "minimal"
        assert data["overall_score"] == 0.0

    def test_readme_with_only_title(self, scorer):
        """Test README with only a title returns minimal word count category."""
        readme = "# Project Title"

        result = scorer.execute({"readme_content": readme})

        assert result.success is True
        data = result.data
        assert data["has_readme"] is True
        assert data["word_count"] < 100
        assert data["word_count_category"] == "minimal"
        assert data["overall_score"] < 0.3

    def test_word_count_category_minimal(self, scorer):
        """Test word_count_category: < 100 = minimal."""
        readme = "This is a very short readme with just a few words."

        result = scorer.execute({"readme_content": readme})

        data = result.data
        assert data["word_count"] < 100
        assert data["word_count_category"] == "minimal"

    def test_word_count_category_adequate(self, scorer):
        """Test word_count_category: 100-500 = adequate."""
        readme = " ".join(["word"] * 200)  # 200 words

        result = scorer.execute({"readme_content": readme})

        data = result.data
        assert 100 <= data["word_count"] <= 500
        assert data["word_count_category"] == "adequate"

    def test_word_count_category_comprehensive(self, scorer):
        """Test word_count_category: > 500 = comprehensive."""
        readme = " ".join(["word"] * 700)  # 700 words

        result = scorer.execute({"readme_content": readme})

        data = result.data
        assert data["word_count"] > 500
        assert data["word_count_category"] == "comprehensive"

    def test_installation_section_detection(self, scorer):
        """Test detection of installation section."""
        readme_with_install = """
        # Project
        ## Installation
        pip install package
        """

        result = scorer.execute({"readme_content": readme_with_install})
        assert result.data["has_installation_section"] is True

        readme_without_install = """
        # Project
        ## Description
        This is a project.
        """

        result = scorer.execute({"readme_content": readme_without_install})
        assert result.data["has_installation_section"] is False

    def test_usage_section_detection(self, scorer):
        """Test detection of usage section."""
        readme_with_usage = """
        # Project
        ## Usage
        Run the project like this...
        """

        result = scorer.execute({"readme_content": readme_with_usage})
        assert result.data["has_usage_section"] is True

    def test_setup_keyword_counts_as_installation(self, scorer):
        """Test that 'setup' keyword counts as installation."""
        readme = """
        # Project
        ## Getting Started
        Run setup.sh
        """

        result = scorer.execute({"readme_content": readme})
        # "Getting Started" matches the pattern
        assert (
            result.data["has_installation_section"] is True
            or result.data["has_usage_section"] is True
        )

    def test_quickstart_counts_as_usage(self, scorer):
        """Test that 'quickstart' counts as usage."""
        readme = """
        # Project
        ## Quickstart
        Quick example here
        """

        result = scorer.execute({"readme_content": readme})
        assert result.data["has_usage_section"] is True

    def test_badge_detection(self, scorer):
        """Test badge detection."""
        readme_with_badges = """
        ![Status](https://example.com/status.svg)
        ![License](https://example.com/license.svg)
        """

        result = scorer.execute({"readme_content": readme_with_badges})
        assert result.data["has_badges"] is True

    def test_demo_link_detection(self, scorer):
        """Test demo/live link detection."""
        readme_with_demo = """
        # Project
        [Live Demo](https://demo.example.com)
        """

        result = scorer.execute({"readme_content": readme_with_demo})
        assert result.data["has_demo_link"] is True

    def test_tech_stack_section_detection(self, scorer):
        """Test tech stack section detection."""
        readme_with_stack = """
        # Project
        ## Tech Stack
        - Python
        - FastAPI
        - PostgreSQL
        """

        result = scorer.execute({"readme_content": readme_with_stack})
        assert result.data["has_tech_stack_section"] is True

    def test_technologies_keyword_counts(self, scorer):
        """Test that 'Technologies' keyword counts as tech stack."""
        readme = """
        # Project
        ## Technologies
        Python, JavaScript, React
        """

        result = scorer.execute({"readme_content": readme})
        assert result.data["has_tech_stack_section"] is True

    def test_overall_score_calculation(self, scorer):
        """Test that overall score aggregates components."""
        readme = (
            """
        # Good README

        ## Installation
        Install it!

        ## Usage
        Use it!

        ## Tech Stack
        Python, JavaScript

        ![Build](https://example.com/build.svg)

        This readme has lots of content here.
        """
            * 3
        )  # Make it comprehensive

        result = scorer.execute({"readme_content": readme})

        data = result.data
        assert 0.0 <= data["overall_score"] <= 1.0
        # Multiple signals should yield higher score
        assert data["overall_score"] > 0.5

    def test_missing_readme_content_key(self, scorer):
        """Test handling of missing readme_content key."""
        result = scorer.execute({})

        assert result.success is True
        data = result.data
        assert data["has_readme"] is False

    def test_result_has_all_required_fields(self, scorer):
        """Test that result has all required fields."""
        result = scorer.execute({"readme_content": "# Test"})

        data = result.data
        assert "has_readme" in data
        assert "word_count" in data
        assert "word_count_category" in data
        assert "has_installation_section" in data
        assert "has_usage_section" in data
        assert "has_badges" in data
        assert "has_demo_link" in data
        assert "has_tech_stack_section" in data
        assert "overall_score" in data

    def test_case_insensitive_section_detection(self, scorer):
        """Test that section detection is case insensitive."""
        readme = """
        # Project
        ## INSTALLATION
        Install here
        """

        result = scorer.execute({"readme_content": readme})
        assert result.data["has_installation_section"] is True

    def test_whitespace_only_readme(self, scorer):
        """Test handling of whitespace-only README."""
        result = scorer.execute({"readme_content": "   \n\n   \t  "})

        data = result.data
        assert data["has_readme"] is False
        assert data["word_count"] == 0

    def test_example_keyword_counts_as_usage(self, scorer):
        """Test that 'Example' counts as usage section."""
        readme = """
        # Project
        ## Example
        Here's how to use it
        """

        result = scorer.execute({"readme_content": readme})
        assert result.data["has_usage_section"] is True

    def test_score_scales_with_word_count(self, scorer):
        """Test that longer READMEs get bonus in score."""
        short_readme = "# Title\nSmall content."
        long_readme = "# Title\n" + "Content paragraph. " * 100

        result_short = scorer.execute({"readme_content": short_readme})
        result_long = scorer.execute({"readme_content": long_readme})

        assert result_long.data["overall_score"] > result_short.data["overall_score"]

    def test_try_it_as_demo_indicator(self, scorer):
        """Test that 'try it' indicates demo link."""
        readme = "Check it out [try it here](https://example.com)"

        result = scorer.execute({"readme_content": readme})
        assert result.data["has_demo_link"] is True

    def test_built_with_counts_as_tech_stack(self, scorer):
        """Test that 'Built With' counts as tech stack."""
        readme = """
        # Project
        ## Built With
        - Python
        - FastAPI
        """

        result = scorer.execute({"readme_content": readme})
        assert result.data["has_tech_stack_section"] is True
