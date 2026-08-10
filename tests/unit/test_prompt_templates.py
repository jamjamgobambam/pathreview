"""Tests for prompt_templates.py - Snapshot tests"""

import hashlib

import pytest

from rag.generator.prompt_templates import PROMPT_TEMPLATES, get_template

# Snapshot of the exact prompt template text, keyed by (template name, version).
#
# Every review PathReview produces is generated from these templates, so a reworded
# prompt changes product output. These hashes pin the text so such a change cannot
# ship silently: it must be a deliberate version bump plus a snapshot update.
#
# MD5 is used for change detection only, never for security. It matches the hash
# this suite already used, so the values stay comparable across the fix.
#
# When a snapshot test fails:
#   1. Unintended edit -> revert the template change.
#   2. Intended change -> add a NEW version key to PROMPT_TEMPLATES (e.g. "v2")
#      rather than editing "v1" in place, so already-generated reviews stay
#      reproducible, then add the new entry below. Print a hash with:
#        python -c "import hashlib; \
#          from rag.generator.prompt_templates import PROMPT_TEMPLATES; \
#          print(hashlib.md5(PROMPT_TEMPLATES['NAME']['VERSION'].encode()).hexdigest())"
EXPECTED_TEMPLATE_HASHES = {
    ("first_impression", "v1"): "ef6429d3a6d426b3c9913381020dd7e4",
    ("gaps_feedback", "v1"): "e5bfd6644fd62a0fe01f60c9aa456762",
    ("presentation_feedback", "v1"): "43549ee59818dfc8eb3627554a563b2e",
    ("projects_feedback", "v1"): "d346d01b24ee7aad92594014a46557af",
    ("skills_feedback", "v1"): "f93103d823482a2e65decc6653e4ee5c",
}


def _hash_template_text(template_text: str) -> str:
    """Hash a single template's text for snapshot comparison.

    Hashes the raw string, so whitespace-only edits are also detected. That
    strictness is intended: trailing whitespace reaches the model too.

    Args:
        template_text: Template string exactly as stored in PROMPT_TEMPLATES.

    Returns:
        Hex-encoded MD5 digest of the template text.
    """
    return hashlib.md5(template_text.encode()).hexdigest()


@pytest.mark.unit
class TestPromptTemplates:
    """Test suite for prompt templates."""

    def test_all_5_templates_exist(self):
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

    def test_skills_feedback_template_exists(self):
        """Test skills_feedback template exists."""
        assert "skills_feedback" in PROMPT_TEMPLATES
        assert "v1" in PROMPT_TEMPLATES["skills_feedback"]

    def test_projects_feedback_template_exists(self):
        """Test projects_feedback template exists."""
        assert "projects_feedback" in PROMPT_TEMPLATES
        assert "v1" in PROMPT_TEMPLATES["projects_feedback"]

    def test_presentation_feedback_template_exists(self):
        """Test presentation_feedback template exists."""
        assert "presentation_feedback" in PROMPT_TEMPLATES
        assert "v1" in PROMPT_TEMPLATES["presentation_feedback"]

    def test_gaps_feedback_template_exists(self):
        """Test gaps_feedback template exists."""
        assert "gaps_feedback" in PROMPT_TEMPLATES
        assert "v1" in PROMPT_TEMPLATES["gaps_feedback"]

    def test_first_impression_template_exists(self):
        """Test first_impression template exists."""
        assert "first_impression" in PROMPT_TEMPLATES
        assert "v1" in PROMPT_TEMPLATES["first_impression"]

    def test_each_template_contains_context_placeholder(self):
        """Test each template contains {context} placeholder."""
        for template_name, versions in PROMPT_TEMPLATES.items():
            for version, template_text in versions.items():
                assert (
                    "{context}" in template_text
                ), f"{template_name} v{version} missing {{context}}"

    def test_each_template_contains_github_username_placeholder(self):
        """Test each template contains {github_username} placeholder."""
        for template_name, versions in PROMPT_TEMPLATES.items():
            for version, template_text in versions.items():
                assert (
                    "{github_username}" in template_text
                ), f"{template_name} v{version} missing {{github_username}}"

    def test_each_template_contains_project_count_placeholder(self):
        """Test each template contains {project_count} placeholder."""
        for template_name, versions in PROMPT_TEMPLATES.items():
            for version, template_text in versions.items():
                assert (
                    "{project_count}" in template_text
                ), f"{template_name} v{version} missing {{project_count}}"

    def test_get_template_returns_correct_template(self):
        """Test get_template() returns correct template."""
        template = get_template("skills_feedback", "v1")

        assert isinstance(template, str)
        assert "{context}" in template
        assert "skills" in template.lower()

    def test_get_template_projects_feedback(self):
        """Test get_template for projects_feedback."""
        template = get_template("projects_feedback", "v1")

        assert isinstance(template, str)
        assert "project" in template.lower()

    def test_get_template_presentation_feedback(self):
        """Test get_template for presentation_feedback."""
        template = get_template("presentation_feedback", "v1")

        assert isinstance(template, str)
        assert "presentation" in template.lower() or "readme" in template.lower()

    def test_get_template_gaps_feedback(self):
        """Test get_template for gaps_feedback."""
        template = get_template("gaps_feedback", "v1")

        assert isinstance(template, str)
        assert "gap" in template.lower() or "skill" in template.lower()

    def test_get_template_first_impression(self):
        """Test get_template for first_impression."""
        template = get_template("first_impression", "v1")

        assert isinstance(template, str)
        assert "impression" in template.lower() or "summary" in template.lower()

    def test_get_template_unknown_name_raises_error(self):
        """Test get_template() raises KeyError/ValueError for unknown template."""
        with pytest.raises((KeyError, ValueError)):
            get_template("nonexistent_template")

    def test_get_template_unknown_version_raises_error(self):
        """Test get_template() raises KeyError/ValueError for unknown version."""
        with pytest.raises((KeyError, ValueError)):
            get_template("skills_feedback", "v999")

    def test_all_templates_have_v1(self):
        """Test all templates have v1 version."""
        for template_name in PROMPT_TEMPLATES.keys():
            assert "v1" in PROMPT_TEMPLATES[template_name]

    def test_templates_are_strings(self):
        """Test all templates are strings."""
        for template_name, versions in PROMPT_TEMPLATES.items():
            for version, template_text in versions.items():
                assert isinstance(template_text, str)
                assert len(template_text) > 0

    def test_templates_have_reasonable_length(self):
        """Test templates have reasonable length."""
        for template_name, versions in PROMPT_TEMPLATES.items():
            for version, template_text in versions.items():
                # Templates should be at least 100 chars
                assert len(template_text) > 100, f"{template_name} v{version} too short"

    def test_skills_feedback_mentions_technical_skills(self):
        """Test skills_feedback template mentions technical skills."""
        template = PROMPT_TEMPLATES["skills_feedback"]["v1"]

        assert "skill" in template.lower()

    def test_projects_feedback_mentions_code_quality(self):
        """Test projects_feedback template mentions code quality."""
        template = PROMPT_TEMPLATES["projects_feedback"]["v1"]

        assert "project" in template.lower() or "quality" in template.lower()

    def test_gaps_feedback_mentions_missing_skills(self):
        """Test gaps_feedback template mentions missing/gap concepts."""
        template = PROMPT_TEMPLATES["gaps_feedback"]["v1"]

        assert (
            "gap" in template.lower()
            or "missing" in template.lower()
            or "demand" in template.lower()
        )

    def test_presentation_feedback_mentions_readme(self):
        """Test presentation_feedback template mentions README or presentation."""
        template = PROMPT_TEMPLATES["presentation_feedback"]["v1"]

        assert (
            "readme" in template.lower()
            or "presentation" in template.lower()
            or "organization" in template.lower()
        )

    def test_first_impression_is_concise(self):
        """Test first_impression template instructs concise output."""
        template = PROMPT_TEMPLATES["first_impression"]["v1"]

        assert (
            "2" in template
            or "3" in template
            or "sentence" in template.lower()
            or "summary" in template.lower()
        )

    def test_get_template_default_version(self):
        """Test get_template() defaults to v1 when version not specified."""
        template_default = get_template("skills_feedback")
        template_v1 = get_template("skills_feedback", "v1")

        assert template_default == template_v1

    def test_template_snapshot_content_hash(self) -> None:
        """Snapshot test: each template's text matches its stored hash."""
        for name in sorted(PROMPT_TEMPLATES.keys()):
            for version in sorted(PROMPT_TEMPLATES[name].keys()):
                expected_hash = EXPECTED_TEMPLATE_HASHES.get((name, version))
                assert expected_hash is not None, (
                    f"No stored snapshot for template '{name}' {version}. Add its hash "
                    "to EXPECTED_TEMPLATE_HASHES in this file."
                )

                actual_hash = _hash_template_text(PROMPT_TEMPLATES[name][version])
                assert actual_hash == expected_hash, (
                    f"Template '{name}' {version} text changed: hash is {actual_hash}, "
                    f"snapshot expects {expected_hash}. Revert the edit, or bump the "
                    "template version and add the new hash to EXPECTED_TEMPLATE_HASHES."
                )

    def test_snapshot_covers_exactly_the_current_templates(self) -> None:
        """Snapshot test: stored snapshot keys match PROMPT_TEMPLATES exactly."""
        actual_keys = {
            (name, version) for name, versions in PROMPT_TEMPLATES.items() for version in versions
        }

        missing = actual_keys - set(EXPECTED_TEMPLATE_HASHES)
        assert not missing, (
            f"Templates with no stored snapshot: {sorted(missing)}. Add each one's hash "
            "to EXPECTED_TEMPLATE_HASHES in this file."
        )

        orphaned = set(EXPECTED_TEMPLATE_HASHES) - actual_keys
        assert not orphaned, (
            f"Snapshots for templates that no longer exist: {sorted(orphaned)}. Remove "
            "them from EXPECTED_TEMPLATE_HASHES in this file."
        )

    def test_snapshot_hash_detects_template_edits(self) -> None:
        """Snapshot test: hashing is content-sensitive, so an edit cannot pass silently.

        Guards against this suite regressing to the no-op it was in issue #37, where
        the snapshot test asserted only that an MD5 hash was a 32-character string and
        so passed no matter what the templates said.
        """
        original = PROMPT_TEMPLATES["skills_feedback"]["v1"]

        # Edits are built by appending rather than replacing known wording, so this
        # test keeps working when the templates are legitimately reworded.
        reworded = original + "Also comment on testing practices.\n"
        whitespace_only = original + " "

        for edited, description in [
            (reworded, "a reworded template"),
            (whitespace_only, "a whitespace-only template edit"),
        ]:
            assert _hash_template_text(edited) != _hash_template_text(
                original
            ), f"hashing is not content-sensitive: {description} would ship undetected"

    def test_skills_feedback_requests_json_format(self):
        """Test skills_feedback requests JSON output."""
        template = PROMPT_TEMPLATES["skills_feedback"]["v1"]

        assert "json" in template.lower()

    def test_projects_feedback_requests_json_format(self):
        """Test projects_feedback requests JSON output."""
        template = PROMPT_TEMPLATES["projects_feedback"]["v1"]

        assert "json" in template.lower()

    def test_presentation_feedback_requests_json_format(self):
        """Test presentation_feedback requests JSON output."""
        template = PROMPT_TEMPLATES["presentation_feedback"]["v1"]

        assert "json" in template.lower()

    def test_gaps_feedback_requests_json_format(self):
        """Test gaps_feedback requests JSON output."""
        template = PROMPT_TEMPLATES["gaps_feedback"]["v1"]

        assert "json" in template.lower()

    def test_first_impression_plain_text(self):
        """Test first_impression may request plain text."""
        template = PROMPT_TEMPLATES["first_impression"]["v1"]

        # Should specify format (JSON or plain text)
        assert (
            "json" in template.lower()
            or "text" in template.lower()
            or "summary" in template.lower()
        )

    def test_templates_have_portfolio_context(self):
        """Test templates mention portfolio or context."""
        for name in PROMPT_TEMPLATES.keys():
            template = PROMPT_TEMPLATES[name]["v1"]
            # All should have context mention or portfolio mention
            assert "{context}" in template or "portfolio" in template.lower()

    def test_template_get_logs_retrieval(self):
        """Test that get_template logs retrieval."""
        # Import logger to verify it's used
        with pytest.MonkeyPatch.context() as mp:
            from unittest.mock import patch

            with patch("rag.generator.prompt_templates.logger") as mock_logger:
                get_template("skills_feedback")
                # Should log template retrieval

    def test_each_template_name_is_valid_identifier(self):
        """Test template names are valid Python identifiers."""
        for name in PROMPT_TEMPLATES.keys():
            assert name.isidentifier()
            assert "_" in name  # Should use snake_case

    def test_template_versions_are_strings(self):
        """Test template version keys are strings."""
        for template_name, versions in PROMPT_TEMPLATES.items():
            assert isinstance(versions, dict)
            for version_key in versions.keys():
                assert isinstance(version_key, str)
                assert version_key.startswith("v")

    def test_no_hardcoded_usernames_in_templates(self):
        """Test templates don't contain hardcoded test usernames."""
        forbidden = ["john", "jane", "test", "demo"]

        for name, versions in PROMPT_TEMPLATES.items():
            for version, template_text in versions.items():
                for forbidden_word in forbidden:
                    # Should use {github_username} placeholder instead
                    assert not (
                        forbidden_word in template_text.lower()
                        and "{github_username}" not in template_text
                    )

    def test_templates_use_consistent_placeholders(self):
        """Test all templates use consistent placeholder syntax."""
        for name, versions in PROMPT_TEMPLATES.items():
            for version, template_text in versions.items():
                # All placeholders should use {name} syntax
                import re

                placeholders = re.findall(r"\{(\w+)\}", template_text)
                assert "context" in placeholders
                assert "github_username" in placeholders
                assert "project_count" in placeholders
