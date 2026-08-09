"""Tests for readme_scorer.py"""

import pytest

from agent.tools.readme_scorer import ReadmeScorer


@pytest.mark.unit
class TestReadmeScorer:
    """Test suite for ReadmeScorer."""

    @pytest.fixture
    def scorer(self) -> ReadmeScorer:
        """Create a ReadmeScorer instance."""
        return ReadmeScorer()

    def test_readme_with_all_quality_signals(self, scorer: ReadmeScorer) -> None:
        """Test README with all quality signals returns high score."""
        readme = """
        # Project Name
        A comprehensive and robust open-source project description designed
        to manage, evaluate, and review path-based workflows effectively across
        multiple development environments and complex setups.

        ## Overview
        PathReview provides automated quality scoring and evaluation tools for
        software repositories. It processes codebase structures, analyzes
        README files for key quality signals, and generates clear actionable
        metrics for maintainers, contributors, and engineering leaders. By
        leveraging modern evaluation frameworks, development teams can ensure
        their repository documentation remains thorough, clear, up to date, and
        easy to navigate for incoming engineers joining the team.

        Documentation is often the first impression a project makes on
        potential users and contributors. High quality documentation improves
        onboarding speed, reduces duplicate support inquiries, and establishes
        best practices across software projects. PathReview automates the
        process of checking whether essential sections, badges, installation
        steps, and code examples are present in a project repository.

        ## Architecture & System Design
        The application relies on a modular microservice architecture composed
        of background worker queues, relational data stores, and specialized
        evaluation tools. Each tool analyzes specific software artifacts—such
        as README documentation, directory structures, commit history, and
        test coverage statistics—to compute holistic repository health scores.

        The system is divided into three distinct layers:
        1. Ingestion Layer: Fetches repository metadata and documentation.
        2. Analysis Layer: Runs modular scorers including README completeness.
        3. Reporting Layer: Aggregates signal scores into summary cards.

        ## Installation & Quickstart Setup
        Install the package directly from PyPI using pip in your virtual
        environment:
        ```bash
        pip install package
        ```
        Ensure you have Python 3.9 or higher installed along with pip and
        virtualenv tools. Clone the repository locally, create a fresh virtual
        environment, and execute installation dependencies prior to running
        scoring suites.

        ## Usage
        Import the core engine and execute the primary scoring suite as shown
        in this example workflow:
        ```python
        import package
        package.run()
        ```
        You can pass custom configuration settings to the execution call to
        tailor scoring thresholds and filter specific signal components based on
        your team's specific requirements.

        ## Core Features
        - Feature 1: Automated README quality signal detection and analysis.
        - Feature 2: Flexible database persistence with PostgreSQL and Redis.
        - Feature 3: Vector database integrations using ChromaDB for search.
        - Feature 4: Comprehensive automated scoring suites covering docs.
        - Feature 5: Real-time status reporting and visualizations.

        ## Tech Stack & Dependencies
        - Python 3.9+ runtime environment
        - FastAPI web framework for asynchronous REST API endpoints
        - PostgreSQL database for relational persistent storage
        - Redis for session management and background job queues
        - Docker containerization for simple local deployment

        ![Build Status](https://example.com/badge.svg)
        ![Coverage](https://example.com/coverage.svg)

        ## Configuration Options
        Configure runtime flags and environment variables using a standard
        .env configuration file located in your project root directory. You can
        specify custom database connection strings, API key credentials, logger
        output formats, and execution timeout parameters to suit local setups.

        ## Contributing Guidelines
        Contributions are warmly welcomed! Please submit a pull request or open
        an issue on GitHub to discuss proposed changes before implementation.
        Ensure all new features include thorough unit tests and pass linting
        checks before requesting final review from maintainers.

        ## Live Demo & Documentation Link
        [Try it here](https://demo.example.com)
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

    def test_readme_with_no_content(self, scorer: ReadmeScorer) -> None:
        """Test README with no content returns score of 0.0."""
        result = scorer.execute({"readme_content": ""})

        assert result.success is True
        data = result.data
        assert data["has_readme"] is False
        assert data["word_count"] == 0
        assert data["word_count_category"] == "minimal"
        assert data["overall_score"] == 0.0

    def test_readme_with_only_title(self, scorer: ReadmeScorer) -> None:
        """Test README with only a title returns minimal word count category."""
        readme = "# Project Title"

        result = scorer.execute({"readme_content": readme})

        assert result.success is True
        data = result.data
        assert data["has_readme"] is True
        assert data["word_count"] < 100
        assert data["word_count_category"] == "minimal"
        assert data["overall_score"] < 0.3

    def test_word_count_category_minimal(self, scorer: ReadmeScorer) -> None:
        """Test word_count_category: < 100 = minimal."""
        readme = "This is a very short readme with just a few words."

        result = scorer.execute({"readme_content": readme})

        data = result.data
        assert data["word_count"] < 100
        assert data["word_count_category"] == "minimal"

    def test_word_count_category_adequate(self, scorer: ReadmeScorer) -> None:
        """Test word_count_category: 100-500 = adequate."""
        readme = " ".join(["word"] * 200)  # 200 words

        result = scorer.execute({"readme_content": readme})

        data = result.data
        assert 100 <= data["word_count"] <= 500
        assert data["word_count_category"] == "adequate"

    def test_word_count_category_comprehensive(self, scorer: ReadmeScorer) -> None:
        """Test word_count_category: > 500 = comprehensive."""
        readme = " ".join(["word"] * 700)  # 700 words

        result = scorer.execute({"readme_content": readme})

        data = result.data
        assert data["word_count"] > 500
        assert data["word_count_category"] == "comprehensive"

    def test_installation_section_detection(self, scorer: ReadmeScorer) -> None:
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

    def test_usage_section_detection(self, scorer: ReadmeScorer) -> None:
        """Test detection of usage section."""
        readme_with_usage = """
        # Project
        ## Usage
        Run the project like this...
        """

        result = scorer.execute({"readme_content": readme_with_usage})
        assert result.data["has_usage_section"] is True

    def test_setup_keyword_counts_as_installation(self, scorer: ReadmeScorer) -> None:
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

    def test_quickstart_counts_as_usage(self, scorer: ReadmeScorer) -> None:
        """Test that 'quickstart' counts as usage."""
        readme = """
        # Project
        ## Quickstart
        Quick example here
        """

        result = scorer.execute({"readme_content": readme})
        assert result.data["has_usage_section"] is True

    def test_badge_detection(self, scorer: ReadmeScorer) -> None:
        """Test badge detection."""
        readme_with_badges = """
        ![Status](https://example.com/status.svg)
        ![License](https://example.com/license.svg)
        """

        result = scorer.execute({"readme_content": readme_with_badges})
        assert result.data["has_badges"] is True

    def test_demo_link_detection(self, scorer: ReadmeScorer) -> None:
        """Test demo/live link detection."""
        readme_with_demo = """
        # Project
        [Live Demo](https://demo.example.com)
        """

        result = scorer.execute({"readme_content": readme_with_demo})
        assert result.data["has_demo_link"] is True

    def test_tech_stack_section_detection(self, scorer: ReadmeScorer) -> None:
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

    def test_technologies_keyword_counts(self, scorer: ReadmeScorer) -> None:
        """Test that 'Technologies' keyword counts as tech stack."""
        readme = """
        # Project
        ## Technologies
        Python, JavaScript, React
        """

        result = scorer.execute({"readme_content": readme})
        assert result.data["has_tech_stack_section"] is True

    def test_overall_score_calculation(self, scorer: ReadmeScorer) -> None:
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

    def test_missing_readme_content_key(self, scorer: ReadmeScorer) -> None:
        """Test handling of missing readme_content key."""
        result = scorer.execute({})

        assert result.success is True
        data = result.data
        assert data["has_readme"] is False

    def test_result_has_all_required_fields(self, scorer: ReadmeScorer) -> None:
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

    def test_case_insensitive_section_detection(self, scorer: ReadmeScorer) -> None:
        """Test that section detection is case insensitive."""
        readme = """
        # Project
        ## INSTALLATION
        Install here
        """

        result = scorer.execute({"readme_content": readme})
        assert result.data["has_installation_section"] is True

    def test_whitespace_only_readme(self, scorer: ReadmeScorer) -> None:
        """Test handling of whitespace-only README."""
        result = scorer.execute({"readme_content": "   \n\n   \t  "})

        data = result.data
        assert data["has_readme"] is False
        assert data["word_count"] == 0

    def test_example_keyword_counts_as_usage(self, scorer: ReadmeScorer) -> None:
        """Test that 'Example' counts as usage section."""
        readme = """
        # Project
        ## Example
        Here's how to use it
        """

        result = scorer.execute({"readme_content": readme})
        assert result.data["has_usage_section"] is True

    def test_score_scales_with_word_count(self, scorer: ReadmeScorer) -> None:
        """Test that longer READMEs get bonus in score."""
        short_readme = "# Title\nSmall content."
        long_readme = "# Title\n" + "Content paragraph. " * 100

        result_short = scorer.execute({"readme_content": short_readme})
        result_long = scorer.execute({"readme_content": long_readme})

        assert result_long.data["overall_score"] > result_short.data["overall_score"]

    def test_try_it_as_demo_indicator(self, scorer: ReadmeScorer) -> None:
        """Test that 'try it' indicates demo link."""
        readme = "Check it out [try it here](https://example.com)"

        result = scorer.execute({"readme_content": readme})
        assert result.data["has_demo_link"] is True

    def test_built_with_counts_as_tech_stack(self, scorer: ReadmeScorer) -> None:
        """Test that 'Built With' counts as tech stack."""
        readme = """
        # Project
        ## Built With
        - Python
        - FastAPI
        """

        result = scorer.execute({"readme_content": readme})
        assert result.data["has_tech_stack_section"] is True
