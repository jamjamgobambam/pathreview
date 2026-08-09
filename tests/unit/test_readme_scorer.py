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
        # PathReview Analyzer

        PathReview Analyzer is a command-line tool and Python library that inspects
        the quality of open-source project documentation. It scans a repository,
        reads the README file, and produces a structured quality report covering
        length, required sections, badges, demo links, and the technology stack.
        Teams run it in continuous integration to make sure every project ships with
        clear, complete, and welcoming documentation before it is released to users.

        ![Build Status](https://example.com/badge.svg)
        ![Coverage](https://example.com/coverage.svg)
        ![License](https://example.com/license.svg)

        ## Overview

        Good documentation is one of the strongest signals of a healthy project, yet
        it is easy to overlook when deadlines are tight. PathReview Analyzer removes
        the guesswork by turning documentation quality into a measurable score that
        you can track over time. The report highlights exactly what is missing, so
        contributors know what to improve instead of guessing. Because the tool is
        fast and deterministic, it fits naturally into pull-request checks and
        nightly pipelines without slowing your team down or producing noisy output.

        ## Features

        - Word-count analysis that classifies each README as minimal, adequate, or
          comprehensive so you can see at a glance how much detail it contains.
        - Section detection for installation, usage, and technology information using
          flexible, case-insensitive matching that tolerates many common headings.
        - Badge and demo-link detection that rewards projects for advertising build
          status, test coverage, and a working live demonstration of the software.
        - A single overall score between zero and one that aggregates every signal
          into one number your team can trust and compare across many repositories.

        ## Tech Stack

        - Python 3.9 for the core scoring engine and the command-line interface.
        - FastAPI for the optional web service that exposes scores over HTTP.
        - PostgreSQL for storing historical scores and tracking trends over time.
        - Redis for caching repeated lookups and keeping the service responsive.

        ## Installation

        Install the published package from PyPI using pip. We recommend creating a
        dedicated virtual environment first, so that dependencies stay isolated from
        the rest of your system and remain easy to upgrade or remove again later.

        ```bash
        python -m venv .venv
        source .venv/bin/activate
        pip install pathreview-analyzer
        ```

        ## Usage

        The command-line interface accepts a path to any repository and prints a
        readable report. You can also import the scorer directly and call it from
        your own Python code, which is handy when you want to embed these checks
        inside an existing test suite or a small continuous-integration script.

        ```python
        from pathreview import ReadmeScorer

        scorer = ReadmeScorer()
        report = scorer.execute({"readme_content": open("README.md").read()})
        print(report.data["overall_score"])
        ```

        ## Configuration

        Every threshold is configurable through a small YAML file. You can raise the
        word-count boundaries, require specific sections, or disable checks that do
        not apply to your project. Sensible defaults are provided, so most teams never
        need to change anything at all to get useful, actionable results right away.

        ## Live Demo

        Want to see it in action before installing anything? Try it here in the hosted
        playground and paste in any README to receive an instant score and breakdown.

        [Try the live demo](https://demo.example.com)

        ## Contributing

        Contributions are welcome and appreciated. Please read the contributing guide,
        open an issue to discuss any significant changes, and make sure the full test
        suite passes before you submit a pull request for review by the maintainers.

        ## License

        This project is released under the MIT license. See the license file in the
        repository root for the full text and the details about permitted use.
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
        assert result.data["has_installation_section"] is True or result.data[
            "has_usage_section"
        ] is True

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
