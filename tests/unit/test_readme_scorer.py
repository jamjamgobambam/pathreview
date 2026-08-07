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
        # PathReview — AI-Powered Code Review Platform

        PathReview is a comprehensive, open-source code review platform that
        leverages artificial intelligence to provide detailed, actionable
        feedback on pull requests and code submissions. The platform combines
        static analysis, natural language processing, and large language model
        integration to help development teams maintain high code quality
        standards across their repositories. Whether you are a solo developer
        looking for a second pair of eyes or a large engineering organization
        seeking to standardize review practices, PathReview adapts to your
        workflow and delivers consistent, high-quality reviews.

        ## Installation

        Follow these steps to install PathReview in your local development
        environment. The platform requires Python 3.9 or higher, Node.js 18
        or higher, and a running PostgreSQL instance for persistent storage.

        ```bash
        git clone https://github.com/example/pathreview.git
        cd pathreview
        python -m venv .venv
        source .venv/bin/activate
        pip install -e ".[dev]"
        cd frontend && npm install
        ```

        After installing dependencies, copy the example environment file and
        configure your local settings. You will need to provide database
        credentials and an API key for the language model provider you want
        to use. See the setup guide for a complete list of environment
        variables and their descriptions.

        ```bash
        cp .env.example .env
        # Edit .env with your configuration
        make migrate
        make seed
        ```

        ## Usage

        Start the development servers with a single command. The backend API
        server runs on port 8000 and the frontend development server runs on
        port 5173 with hot module replacement enabled.

        ```python
        import pathreview
        client = pathreview.Client(api_key="your-key")
        result = client.review("https://github.com/user/repo/pull/42")
        print(result.summary)
        print(result.suggestions)
        ```

        You can also use the command-line interface to submit reviews from
        your terminal without writing any code. The CLI supports all the same
        options as the Python client library and can be integrated into your
        continuous integration pipeline for automated review on every pull
        request.

        ## Features

        - Automated code review with actionable feedback and suggestions
        - Resume and README quality scoring with detailed breakdowns
        - Retrieval-augmented generation for context-aware review comments
        - Built-in safety guardrails including PII scrubbing and bias detection
        - RESTful API with comprehensive OpenAPI documentation
        - Modern React frontend with responsive design and dark mode support
        - Extensible plugin architecture for custom review rules and tools
        - Batch processing support for reviewing multiple files at once

        ## Tech Stack

        - Python 3.9 with FastAPI for the backend API server
        - React 18 with TypeScript for the frontend application
        - PostgreSQL 15 for persistent data storage and retrieval
        - Redis for caching and rate limiting across services
        - LangChain for orchestrating large language model interactions
        - Alembic for database schema migrations and version control
        - Docker and Docker Compose for containerized development

        ![Build Status](https://example.com/badge.svg)
        ![Coverage](https://example.com/coverage.svg)
        ![License](https://example.com/license.svg)

        ## Live Demo

        [Try it here](https://demo.example.com)

        Visit our hosted demo environment to explore the platform without any
        local setup. The demo includes sample repositories and pre-generated
        reviews so you can see the full range of feedback the platform
        provides.

        ## API Reference

        The PathReview API follows RESTful conventions and returns JSON
        responses for all endpoints. Authentication is handled via JSON Web
        Tokens issued at the login endpoint. Rate limiting is applied per
        user with configurable thresholds to prevent abuse. The API
        documentation is auto-generated from the FastAPI route definitions
        and is available at the docs endpoint when the server is running.

        ## Architecture

        The platform follows a modular architecture with clear separation
        of concerns. The ingestion layer handles document parsing and
        chunking. The retrieval-augmented generation layer manages vector
        storage and semantic search. The agent layer orchestrates tool
        execution and response generation. The safety layer provides
        guardrails for content filtering and bias detection. Each layer
        communicates through well-defined interfaces making it easy to
        extend or replace individual components without affecting the rest
        of the system.

        ## Contributing

        We welcome contributions from the community. Please read our
        contributing guide for details on our code of conduct, development
        workflow, branch naming conventions, and the process for submitting
        pull requests. All contributions must include relevant tests and
        pass the automated quality checks before they can be merged.

        ## Testing

        Run the full test suite to verify your changes before submitting
        a pull request. The project uses pytest for unit and integration
        testing with comprehensive fixtures and mock objects for external
        service dependencies.

        ## Deployment

        PathReview can be deployed using Docker Compose for small teams
        or Kubernetes for larger organizations requiring horizontal
        scaling and high availability. The deployment guide covers both
        approaches with step-by-step instructions and configuration
        templates for common cloud providers.

        ## License

        This project is licensed under the MIT License. See the LICENSE
        file for the full license text and terms of use.
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
        readme = """
        # Good README

        ## Installation
        Install it!

        ## Usage
        Use it!

        ## Tech Stack
        Python, JavaScript

        ![Build](https://example.com/build.svg)

        This readme has lots of content here.
        """ * 3  # Make it comprehensive

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
