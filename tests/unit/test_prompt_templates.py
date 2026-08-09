"""Tests for prompt_templates.py - Snapshot tests"""

import hashlib
import re
from collections.abc import Mapping
from unittest.mock import patch

import pytest

from rag.generator.prompt_templates import PROMPT_TEMPLATES, get_template

EXPECTED_TEMPLATE_HASHES = {
    ("first_impression", "v1"): (
        "9e7697ff3efd892c82c63ffcc8365690685fb1c29f79d45d84e057b2d0672dd0"
    ),
    ("gaps_feedback", "v1"): ("b2673a1a1f018f2f2fdf37b2dfb6b30634404ba7bb2c241cc01b6240b9097950"),
    ("presentation_feedback", "v1"): (
        "87230b7045d66a1fae7d06e2509c6fae31046e0c4e8d30a3c3d6fe9ad2a7a3d7"
    ),
    ("projects_feedback", "v1"): (
        "7e53575582f45389e4a3e4f93c7c137da629d3a14809e16f746732b9a06740d1"
    ),
    ("skills_feedback", "v1"): ("a24d6d717d4f365c28a686f28b3e77f47204c325ce892fc32d68eb82259f6816"),
}


def _template_hashes(
    templates: Mapping[str, Mapping[str, str]],
) -> dict[tuple[str, str], str]:
    """Return a SHA-256 digest keyed by template name and version."""
    return {
        (name, version): hashlib.sha256(template.encode("utf-8")).hexdigest()
        for name, versions in templates.items()
        for version, template in versions.items()
    }


def _assert_prompt_snapshots(
    templates: Mapping[str, Mapping[str, str]],
    expected_hashes: Mapping[tuple[str, str], str] = EXPECTED_TEMPLATE_HASHES,
) -> None:
    """Assert that the prompt inventory and content match reviewed snapshots."""
    actual_hashes = _template_hashes(templates)
    actual_keys = set(actual_hashes)
    expected_keys = set(expected_hashes)

    assert actual_keys == expected_keys, (
        "Prompt template versions changed. "
        f"Unexpected versions without snapshots: {sorted(actual_keys - expected_keys)}; "
        f"snapshot versions missing from templates: {sorted(expected_keys - actual_keys)}."
    )

    for name, version in sorted(expected_keys):
        assert actual_hashes[(name, version)] == expected_hashes[(name, version)], (
            f"Prompt template {name} {version} changed without a reviewed snapshot. "
            "For an intentional prompt change, add a new version and its expected hash."
        )


@pytest.mark.unit
class TestPromptTemplates:
    """Test suite for prompt templates."""

    def test_all_5_templates_exist(self) -> None:
        """Test all 5 templates exist in PROMPT_TEMPLATES."""
        expected_templates = {
            "skills_feedback",
            "projects_feedback",
            "presentation_feedback",
            "gaps_feedback",
            "first_impression",
        }

        actual_templates = set(PROMPT_TEMPLATES.keys())
        assert actual_templates == expected_templates

    def test_skills_feedback_template_exists(self) -> None:
        """Test skills_feedback template exists."""
        assert "skills_feedback" in PROMPT_TEMPLATES
        assert "v1" in PROMPT_TEMPLATES["skills_feedback"]

    def test_projects_feedback_template_exists(self) -> None:
        """Test projects_feedback template exists."""
        assert "projects_feedback" in PROMPT_TEMPLATES
        assert "v1" in PROMPT_TEMPLATES["projects_feedback"]

    def test_presentation_feedback_template_exists(self) -> None:
        """Test presentation_feedback template exists."""
        assert "presentation_feedback" in PROMPT_TEMPLATES
        assert "v1" in PROMPT_TEMPLATES["presentation_feedback"]

    def test_gaps_feedback_template_exists(self) -> None:
        """Test gaps_feedback template exists."""
        assert "gaps_feedback" in PROMPT_TEMPLATES
        assert "v1" in PROMPT_TEMPLATES["gaps_feedback"]

    def test_first_impression_template_exists(self) -> None:
        """Test first_impression template exists."""
        assert "first_impression" in PROMPT_TEMPLATES
        assert "v1" in PROMPT_TEMPLATES["first_impression"]

    def test_each_template_contains_context_placeholder(self) -> None:
        """Test each template contains {context} placeholder."""
        for template_name, versions in PROMPT_TEMPLATES.items():
            for version, template_text in versions.items():
                assert (
                    "{context}" in template_text
                ), f"{template_name} v{version} missing {{context}}"

    def test_each_template_contains_github_username_placeholder(self) -> None:
        """Test each template contains {github_username} placeholder."""
        for template_name, versions in PROMPT_TEMPLATES.items():
            for version, template_text in versions.items():
                assert (
                    "{github_username}" in template_text
                ), f"{template_name} v{version} missing {{github_username}}"

    def test_each_template_contains_project_count_placeholder(self) -> None:
        """Test each template contains {project_count} placeholder."""
        for template_name, versions in PROMPT_TEMPLATES.items():
            for version, template_text in versions.items():
                assert (
                    "{project_count}" in template_text
                ), f"{template_name} v{version} missing {{project_count}}"

    def test_get_template_returns_correct_template(self) -> None:
        """Test get_template() returns correct template."""
        template = get_template("skills_feedback", "v1")

        assert isinstance(template, str)
        assert "{context}" in template
        assert "skills" in template.lower()

    def test_get_template_projects_feedback(self) -> None:
        """Test get_template for projects_feedback."""
        template = get_template("projects_feedback", "v1")

        assert isinstance(template, str)
        assert "project" in template.lower()

    def test_get_template_presentation_feedback(self) -> None:
        """Test get_template for presentation_feedback."""
        template = get_template("presentation_feedback", "v1")

        assert isinstance(template, str)
        assert "presentation" in template.lower() or "readme" in template.lower()

    def test_get_template_gaps_feedback(self) -> None:
        """Test get_template for gaps_feedback."""
        template = get_template("gaps_feedback", "v1")

        assert isinstance(template, str)
        assert "gap" in template.lower() or "skill" in template.lower()

    def test_get_template_first_impression(self) -> None:
        """Test get_template for first_impression."""
        template = get_template("first_impression", "v1")

        assert isinstance(template, str)
        assert "impression" in template.lower() or "summary" in template.lower()

    def test_get_template_unknown_name_raises_error(self) -> None:
        """Test get_template() raises KeyError/ValueError for unknown template."""
        with pytest.raises((KeyError, ValueError)):
            get_template("nonexistent_template")

    def test_get_template_unknown_version_raises_error(self) -> None:
        """Test get_template() raises KeyError/ValueError for unknown version."""
        with pytest.raises((KeyError, ValueError)):
            get_template("skills_feedback", "v999")

    def test_all_templates_have_v1(self) -> None:
        """Test all templates have v1 version."""
        for template_name in PROMPT_TEMPLATES:
            assert "v1" in PROMPT_TEMPLATES[template_name]

    def test_templates_are_strings(self) -> None:
        """Test all templates are strings."""
        for _template_name, versions in PROMPT_TEMPLATES.items():
            for _version, template_text in versions.items():
                assert isinstance(template_text, str)
                assert len(template_text) > 0

    def test_templates_have_reasonable_length(self) -> None:
        """Test templates have reasonable length."""
        for template_name, versions in PROMPT_TEMPLATES.items():
            for version, template_text in versions.items():
                # Templates should be at least 100 chars
                assert len(template_text) > 100, f"{template_name} v{version} too short"

    def test_skills_feedback_mentions_technical_skills(self) -> None:
        """Test skills_feedback template mentions technical skills."""
        template = PROMPT_TEMPLATES["skills_feedback"]["v1"]

        assert "skill" in template.lower()

    def test_projects_feedback_mentions_code_quality(self) -> None:
        """Test projects_feedback template mentions code quality."""
        template = PROMPT_TEMPLATES["projects_feedback"]["v1"]

        assert "project" in template.lower() or "quality" in template.lower()

    def test_gaps_feedback_mentions_missing_skills(self) -> None:
        """Test gaps_feedback template mentions missing/gap concepts."""
        template = PROMPT_TEMPLATES["gaps_feedback"]["v1"]

        assert (
            "gap" in template.lower()
            or "missing" in template.lower()
            or "demand" in template.lower()
        )

    def test_presentation_feedback_mentions_readme(self) -> None:
        """Test presentation_feedback template mentions README or presentation."""
        template = PROMPT_TEMPLATES["presentation_feedback"]["v1"]

        assert (
            "readme" in template.lower()
            or "presentation" in template.lower()
            or "organization" in template.lower()
        )

    def test_first_impression_is_concise(self) -> None:
        """Test first_impression template instructs concise output."""
        template = PROMPT_TEMPLATES["first_impression"]["v1"]

        assert (
            "2" in template
            or "3" in template
            or "sentence" in template.lower()
            or "summary" in template.lower()
        )

    def test_get_template_default_version(self) -> None:
        """Test get_template() defaults to v1 when version not specified."""
        template_default = get_template("skills_feedback")
        template_v1 = get_template("skills_feedback", "v1")

        assert template_default == template_v1

    def test_template_snapshot_content_hash(self) -> None:
        """Verify every prompt version matches its reviewed content snapshot."""
        _assert_prompt_snapshots(PROMPT_TEMPLATES)

    def test_template_snapshot_rejects_same_version_content_change(self) -> None:
        """Reject content edits that reuse an existing prompt version."""
        mutated_templates = {name: versions.copy() for name, versions in PROMPT_TEMPLATES.items()}
        mutated_templates["skills_feedback"]["v1"] += "\nACCIDENTAL SAME-VERSION EDIT"

        with pytest.raises(AssertionError, match="skills_feedback v1 changed"):
            _assert_prompt_snapshots(mutated_templates)

    def test_template_snapshot_rejects_unreviewed_version(self) -> None:
        """Reject new prompt versions until an expected snapshot is reviewed."""
        mutated_templates = {name: versions.copy() for name, versions in PROMPT_TEMPLATES.items()}
        mutated_templates["skills_feedback"]["v2"] = mutated_templates["skills_feedback"]["v1"]

        with pytest.raises(AssertionError, match="Unexpected versions without snapshots"):
            _assert_prompt_snapshots(mutated_templates)

    def test_skills_feedback_requests_json_format(self) -> None:
        """Test skills_feedback requests JSON output."""
        template = PROMPT_TEMPLATES["skills_feedback"]["v1"]

        assert "json" in template.lower()

    def test_projects_feedback_requests_json_format(self) -> None:
        """Test projects_feedback requests JSON output."""
        template = PROMPT_TEMPLATES["projects_feedback"]["v1"]

        assert "json" in template.lower()

    def test_presentation_feedback_requests_json_format(self) -> None:
        """Test presentation_feedback requests JSON output."""
        template = PROMPT_TEMPLATES["presentation_feedback"]["v1"]

        assert "json" in template.lower()

    def test_gaps_feedback_requests_json_format(self) -> None:
        """Test gaps_feedback requests JSON output."""
        template = PROMPT_TEMPLATES["gaps_feedback"]["v1"]

        assert "json" in template.lower()

    def test_first_impression_plain_text(self) -> None:
        """Test first_impression may request plain text."""
        template = PROMPT_TEMPLATES["first_impression"]["v1"]

        # Should specify format (JSON or plain text)
        assert (
            "json" in template.lower()
            or "text" in template.lower()
            or "summary" in template.lower()
        )

    def test_templates_have_portfolio_context(self) -> None:
        """Test templates mention portfolio or context."""
        for name in PROMPT_TEMPLATES:
            template = PROMPT_TEMPLATES[name]["v1"]
            # All should have context mention or portfolio mention
            assert "{context}" in template or "portfolio" in template.lower()

    def test_template_get_logs_retrieval(self) -> None:
        """Test that get_template logs retrieval."""
        with patch("rag.generator.prompt_templates.logger") as mock_logger:
            get_template("skills_feedback")

        mock_logger.info.assert_called_once_with(
            "template_retrieved", name="skills_feedback", version="v1"
        )

    def test_each_template_name_is_valid_identifier(self) -> None:
        """Test template names are valid Python identifiers."""
        for name in PROMPT_TEMPLATES:
            assert name.isidentifier()
            assert "_" in name  # Should use snake_case

    def test_template_versions_are_strings(self) -> None:
        """Test template version keys are strings."""
        for _template_name, versions in PROMPT_TEMPLATES.items():
            assert isinstance(versions, dict)
            for version_key in versions:
                assert isinstance(version_key, str)
                assert version_key.startswith("v")

    def test_no_hardcoded_usernames_in_templates(self) -> None:
        """Test templates don't contain hardcoded test usernames."""
        forbidden = ["john", "jane", "test", "demo"]

        for _name, versions in PROMPT_TEMPLATES.items():
            for _version, template_text in versions.items():
                for forbidden_word in forbidden:
                    # Should use {github_username} placeholder instead
                    assert not (
                        forbidden_word in template_text.lower()
                        and "{github_username}" not in template_text
                    )

    def test_templates_use_consistent_placeholders(self) -> None:
        """Test all templates use consistent placeholder syntax."""
        for _name, versions in PROMPT_TEMPLATES.items():
            for _version, template_text in versions.items():
                # All placeholders should use {name} syntax
                placeholders = re.findall(r"\{(\w+)\}", template_text)
                assert "context" in placeholders
                assert "github_username" in placeholders
                assert "project_count" in placeholders
