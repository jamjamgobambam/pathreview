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
        A comprehensive project description that explains the problem solved,
        the target audience, and how the product can be used in real-world
        scenarios.

        ## Overview
        This README provides a detailed overview of the project architecture,
        deployment strategy, and the expected user experience. It is meant to
        serve as a reference for contributors, maintainers, and end users who
        need a clear and concise summary of what the project does.

        This project uses a modular design with separate components for API
        handling, data ingestion, and machine learning evaluation. Each
        component is designed to be independently deployable and easily
        testable. The documentation includes instructions for local development,
        environment setup, and how to run the full test suite.

        The architecture section also includes performance expectations,
        scalability goals, and the manner in which the system separates
        concerns between storage, business logic, and presentation layers.

        ## Installation
        ```bash
        pip install package
        ```

        To install the package from source, clone the repository, create a Python
        virtual environment, and install the required dependencies. The
        requirements file contains all of the packages needed for development,
        testing, and production usage.

        For reproducible development environments, the repository also includes
        a Docker Compose configuration to start the local services, including
        the database, cache, and worker processes. Installation notes cover
        Python version compatibility, virtual environment activation,
        dependency pinning, and the recommended upgrade path for third-party
        libraries.

        ## Usage
        ```python
        import package
        package.run()
        ```

        The usage section includes sample commands and code snippets. Users can
        execute the main entry point, configure the application through
        environment variables, and run one-off tasks using the command line
        interface.

        Additional usage examples demonstrate how to run the HTTP API locally,
        how to invoke background jobs, and how to use the package in a larger
        orchestration pipeline. Each usage example includes expected output,
        optional debug flags, and troubleshooting tips for common environment
        issues.

        ## Features
        - Feature 1: Structured data ingestion with automatic normalization and
          validation.
        - Feature 2: Configurable pipeline processing using clear chunking and
          embedding strategies.
        - Feature 3: Real-time scoring and feedback for README quality, badge
          detection, and demo link validation.
        - Feature 4: Comprehensive error handling and retry logic for external
          API calls.
        - Feature 5: Modular architecture supporting both REST and event-driven
          patterns.
        - Feature 6: Pluggable provider adapters for third-party services and
          custom storage backends.
        - Feature 7: Built-in logging, metrics, and health-check endpoints for
          service observability.

        ## Tech Stack
        - Python 3.9
        - FastAPI
        - PostgreSQL
        - SQLAlchemy
        - Redis
        - Docker
        - TypeScript for frontend utilities
        - GitHub Actions for continuous integration

        This section further explains how each technology is used in the
        project. Python is the primary implementation language for backend
        services, FastAPI provides a lightweight web framework, PostgreSQL
        stores persistent state, and Redis is used for caching and messaging.

        The frontend and developer tooling are built with modern libraries that
        support incremental builds, type-safe configuration, and automated
        linting. Docker ensures consistent environments across local development
        and continuous integration.

        The repository also documents how to use GitHub Actions for test
        execution, linting, release packaging, and deployment previews. It
        explains the relationship between local developer workflows and CI
        pipelines, including how feature branches are validated before merge.

        ## Configuration
        Configuration is managed through environment variables, a configuration
        file, and optional secret management. The README details the available
        options, default values, and examples for local and cloud deployments.

        Example configuration includes database connection settings, Redis
        cache TTL values, service endpoint URLs, and feature flag definitions.
        There are instructions for managing credentials securely in
        development, staging, and production environments.

        The configuration section also includes a sample `.env.example` file,
        descriptions of each setting, and guidance on which options are required
        versus optional. It highlights best practices for keeping sensitive
        values out of version control and for validating configuration on
        application startup.

        ## Contribution
        Contributions are welcome. The repository includes guidelines for
        submitting issues, pull requests, and code reviews. The project uses a
        standard branching strategy and includes instructions for running the
        test suite before opening a PR.

        Contributors can follow the contribution guide to understand how to
        format commit messages, write descriptive change summaries, and assign
        reviewers. The README also documents the code style conventions, the
        preferred issue labeling scheme, and the process for proposing
        architecture changes.

        ## Testing
        Automated tests cover unit, integration, and end-to-end scenarios. The
        README outlines how to execute tests, run linting checks, and generate
        coverage reports.

        The project includes a dedicated test directory with fixture data, mock
        services, and scripts for running the test matrix locally. There are
        instructions for running `pytest` with coverage output, checking style
        with the linter, and validating documentation builds.

        The README also details how to interpret common failures, how to re-run
        flaky tests, and how to add new test cases when changing existing
        functionality.

        ## Troubleshooting
        Common troubleshooting topics are covered here, including how to handle
        dependency conflicts, database migrations, and environment drift between
        local and staging systems.

        The troubleshooting section provides pointers for resolving
        authentication issues, restoring service connectivity, and debugging
        unexpected failures during startup. It also includes links to external
        resources for the tooling and services used by the project.

        ![Build Status](https://example.com/badge.svg)
        ![Coverage](https://example.com/coverage.svg)
        ![License](https://example.com/license.svg)

        ## Live Demo
        [Try it here](https://demo.example.com)

        ## Additional Resources
        For additional details, see the API documentation, architecture decision
        records, and setup guides included in the repository. This README is
        intentionally verbose to support newcomers and longtime maintainers
        alike.
        """

        result = scorer.execute({"readme_content": readme})

        assert result.success is True
        data = result.data
        assert data["has_readme"] is True
        assert data["word_count"] > 100
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
        assert (
            data["word_count"] > 500
        )  # Probably shouldn't use it as the main proxy for cohesiveness.
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
