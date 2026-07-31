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
        ![Build Status](https://example.com/badge.svg)
        ![Coverage](https://example.com/coverage.svg)
        ![License](https://example.com/license-badge.svg)
        ![Version](https://example.com/version-badge.svg)

        A comprehensive project description. This project exists to solve a specific problem
        that other tools in this space either ignore or handle poorly. It focuses on being
        fast, lightweight, and easy to integrate into existing pipelines without forcing you
        to rewrite your entire stack around it. Whether you're a solo developer prototyping
        an idea or a team maintaining a production system, this project aims to get out of
        your way and let you focus on what matters.

        ## Table of Contents
        - [Features](#features)
        - [Tech Stack](#tech-stack)
        - [Demo](#demo)
        - [Prerequisites](#prerequisites)
        - [Installation](#installation-or-quick-start)
        - [Configuration](#configuration)
        - [Usage](#usage)
        - [Architecture](#architecture)
        - [Testing](#testing)
        - [Roadmap](#roadmap)
        - [Contributing](#contributing)
        - [FAQ / Troubleshooting](#faq--troubleshooting)
        - [License](#license)
        - [Acknowledgments](#acknowledgments)
        - [Contact](#contact)

        ## Features
        - **Feature 1** — Handles the core workflow end to end, with sensible defaults so you
        can get started without extensive configuration.
        - **Feature 2** — Extensible plugin system that lets you swap out components without
        touching the core codebase.
        - **Feature 3** — Built-in monitoring and logging so you can observe what's happening
        in production without bolting on third-party tools.
        - **Feature 4** — Async-first design for high-throughput workloads.
        - **Feature 5** — Comprehensive type hints and validation to catch errors early.

        ## Tech Stack
        - **Language:** Python 3.9+
        - **Framework:** FastAPI for the API layer
        - **Database:** PostgreSQL for persistent storage
        - **Caching:** Redis for session and query caching
        - **Task Queue:** Celery for background job processing
        - **Containerization:** Docker and Docker Compose for local development and deployment

        ## Live Demo
        [Try it here](https://demo.example.com)

        A hosted sandbox environment is available so you can explore the core features
        without installing anything locally. Note that the demo environment resets every
        24 hours and shouldn't be used for storing real data.

        <!-- Add a screenshot or GIF here if the project has a UI -->
        <!-- ![Screenshot](path/to/screenshot.png) -->

        ## Prerequisites
        Before installing, make sure you have the following set up:
        - Python 3.9 or higher
        - PostgreSQL 14 or higher, running locally or accessible remotely
        - Redis (optional, only required if you enable caching)
        - An API key from [Provider Name], if you plan to use the integration features
        - `pip` and `virtualenv` (or `poetry`/`pipenv` if you prefer)

        ## Installation or Quick Start
        Clone the repository and install dependencies:
        ```bash
        git clone https://github.com/user/repo.git
        cd repo
        pip install -r requirements.txt
        ```

        Or install directly from PyPI:
        ```bash
        pip install package
        ```

        For a full local development setup including the database and cache, use Docker
        Compose:
        ```bash
        docker-compose up -d
        ```

        ## Configuration
        Copy `.env.example` to `.env` and update the values to match your environment:
        ```bash
        cp .env.example .env
        ```

        Key environment variables:
        ```bash
        DATABASE_URL=postgresql://user:pass@localhost/dbname
        REDIS_URL=redis://localhost:6379/0
        API_KEY=your_api_key_here
        DEBUG=False
        LOG_LEVEL=INFO
        ```

        Refer to `config/settings.py` for the full list of configurable options and their
        defaults.

        ## Usage
        Basic usage:
        ```python
        import package

        client = package.Client(api_key="your_key")
        result = client.run()
        print(result)
        ```

        ### Running as a service
        ```bash
        uvicorn app.main:app --host 0.0.0.0 --port 8000
        ```

        ### Common workflows
        - Batch processing multiple inputs at once via `client.run_batch(inputs)`
        - Streaming results with `client.stream()` for large datasets
        - Scheduling recurring jobs through the built-in task scheduler

        ## Architecture
        The project follows a layered architecture separating concerns between the API
        layer, business logic, and data access. Requests come in through FastAPI routes,
        get validated and processed by service classes, and persist through a repository
        pattern that abstracts away the underlying database. This separation makes it
        straightforward to swap out PostgreSQL for another datastore later without
        touching the API or business logic. Background jobs are handled asynchronously
        through Celery to keep request/response times fast, and Redis is used both as a
        cache and as the Celery broker.

        ## Testing
        Run the full test suite with:
        ```bash
        pytest
        ```

        Run with coverage reporting:
        ```bash
        pytest --cov=package --cov-report=html
        ```

        Integration tests require a running PostgreSQL instance; see `tests/README.md`
        for setup instructions.

        ## Roadmap
        - [ ] Add support for multi-tenant deployments
        - [ ] Improve batch processing throughput
        - [ ] Add GraphQL API alongside REST
        - [ ] Expand plugin ecosystem
        - [ ] Publish official Helm chart for Kubernetes deployments

        ## Contributing
        Contributions are welcome and appreciated. To contribute:
        1. Fork the repository
        2. Create a feature branch (`git checkout -b feature/my-feature`)
        3. Make your changes and add tests
        4. Ensure the test suite passes and code is linted
        5. Open a pull request describing your changes

        Please read `CONTRIBUTING.md` for coding standards, commit message conventions,
        and the review process before submitting.

        ## FAQ / Troubleshooting
        **Q: I'm getting a database connection error on startup.**
        A: Double-check that `DATABASE_URL` in your `.env` file matches your PostgreSQL
        credentials and that the database is running and reachable.

        **Q: The package installs but imports fail.**
        A: Make sure you're using a supported Python version (3.9+) and that your virtual
        environment is activated.

        **Q: How do I reset my local development environment?**
        A: Run `docker-compose down -v` to remove containers and volumes, then
        `docker-compose up -d` to start fresh.

        ## License
        This project is licensed under the MIT License. See the `LICENSE` file for full
        details.

        ## Acknowledgments
        - Thanks to the maintainers of FastAPI, SQLAlchemy, and Celery, whose work this
        project builds on
        - Inspired by similar tools in the open-source community that shaped early
        design decisions
        - Thanks to all contributors who have submitted issues, pull requests, and
        feedback

        ## Contact
        - Maintainer: [Your Name](mailto:email@example.com)
        - Issues and feature requests: [GitHub Issues](https://github.com/user/repo/issues)
        - Discussions: [GitHub Discussions](https://github.com/user/repo/discussions)
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
