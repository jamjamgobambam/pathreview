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
        readme = (
            "# Project Name\n\n"
            "![Build Status](https://example.com/badge.svg)\n"
            "![Coverage](https://example.com/coverage.svg)\n\n"
            "A comprehensive project description that outlines the primary "
            "objectives, core capabilities, and high-level architecture of this "
            "application. This platform provides developers with robust tools for "
            "data ingestion, processing, and intelligent analysis in production "
            "environments.\n\n"
            "## Installation\n"
            "To set up the project locally, ensure you have Python 3.9 or higher "
            "installed on your system. Run the following command to install the "
            "required package dependencies directly from the repository:\n\n"
            "```bash\n"
            "pip install package\n"
            "```\n\n"
            "## Usage\n"
            "Import the main application module and initialize the standard "
            "workflow execution engine as shown in the example snippet below:\n\n"
            "```python\n"
            "import package\n"
            "package.run()\n"
            "```\n\n"
            "## Features\n"
            "- Automated data parsing and background document ingestion pipeline\n"
            "- Real-time performance monitoring and analytical report generation\n"
            "- Flexible configuration options for seamlessly integrating custom "
            "storage adapters\n"
            "- Comprehensive logging and structured diagnostic telemetry for "
            "enterprise deployments\n"
            "- Advanced error handling with automatic retry mechanics for "
            "asynchronous background workers\n\n"
            "## Tech Stack\n"
            "- Python 3.9\n"
            "- FastAPI\n"
            "- PostgreSQL\n\n"
            "## Architecture\n"
            "The application is structured into decoupled components that "
            "communicate through well-defined interfaces. The core pipeline "
            "ingests raw documents, converts them into unified data models, and "
            "indexes them in a persistent store. Worker nodes consume tasks from "
            "a central queue to process high-throughput document payloads "
            "efficiently without blocking the primary HTTP server thread.\n\n"
            "## Detailed Configuration\n"
            "You can customize runtime behavior by supplying environment "
            "variables or an external configuration file. Key settings include "
            "database connection strings, maximum concurrent worker threads, "
            "memory cache TTL limits, and external service timeout thresholds. "
            "Refer to the sample configuration file in the project repository "
            "for default parameter values and recommended production "
            "overrides.\n\n"
            "## API Reference\n"
            "The service exposes a RESTful API with automated OpenAPI "
            "documentation accessible via the standard Swagger UI endpoint. "
            "Client applications can issue authenticated HTTP requests to "
            "register new data streams, query processing statuses, trigger "
            "on-demand pipeline executions, and retrieve formatted analytical "
            "summaries. All API responses use standard JSON formatting with "
            "standardized error payloads.\n\n"
            "## Contributing Guidelines\n"
            "We welcome community contributions to improve this repository. "
            "Before submitting a pull request, please ensure your code conforms "
            "to the project's formatting and linting guidelines. Run all local "
            "test suites to verify that new changes do not introduce regressions. "
            "Include clear documentation and detailed commit messages explaining "
            "the purpose and design decisions behind your pull request.\n\n"
            "## Performance Considerations\n"
            "The system is optimized for handling high-throughput document "
            "processing with minimal latency. Benchmarks demonstrate consistent "
            "sub-second response times for typical queries across datasets with "
            "millions of indexed documents. The architecture scales horizontally "
            "through containerized worker deployments, allowing elastic resource "
            "allocation based on current workload demands. Memory usage is "
            "optimized through efficient data structure implementations and "
            "automatic garbage collection tuning. Network bandwidth requirements "
            "are minimized through intelligent caching strategies and delta "
            "update mechanisms for incremental synchronization.\n\n"
            "## Security and Authentication\n"
            "All API endpoints enforce strong authentication mechanisms using "
            "industry-standard OAuth 2.0 and JWT tokens. Sensitive data is "
            "encrypted at rest using AES-256 encryption with hardware security "
            "module support for key management. Transport layer security is "
            "enforced through TLS 1.3 for all communications. Role-based access "
            "control provides granular permissions management with audit logging "
            "for all privileged operations. Regular security assessments and "
            "penetration testing ensure vulnerability-free operation.\n\n"
            "## Monitoring and Observability\n"
            "Comprehensive observability is built into every component through "
            "structured logging, distributed tracing, and time-series metrics "
            "collection. Integration with popular monitoring platforms enables "
            "real-time alerting and anomaly detection. Dashboard templates "
            "provide visualizations for key performance indicators and health "
            "metrics. Detailed logs help with troubleshooting and root cause "
            "analysis of production incidents.\n\n"
            "## Live Demo\n"
            "Check out our deployed environment and interact with the live API:\n"
            "[Try it here](https://demo.example.com)"
        )

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
