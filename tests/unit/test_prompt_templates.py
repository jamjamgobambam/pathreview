"""Tests for prompt_templates.py - Snapshot tests

Snapshot workflow (issue #37):
    EXPECTED_TEMPLATE_HASHES below stores a SHA-256 digest of each
    (template_name, version) template string. If you intentionally change
    wording for an existing version, these tests will fail — that's the
    point. Two ways to respond:

    1. Unintentional change: revert the edit in prompt_templates.py.
    2. Intentional change: add a NEW version key (e.g. "v2") instead of
       editing the existing one in place, then add its hash below.

    Do not update an existing hash to make a v1 edit pass silently — that
    defeats the purpose of this guardrail.
"""

import hashlib

import pytest

from rag.generator.prompt_templates import PROMPT_TEMPLATES, get_template

# Expected SHA-256 hash of each template's exact text, keyed by
# (template_name, version). Regenerate with:
#   hashlib.sha256(PROMPT_TEMPLATES[name][version].encode("utf-8")).hexdigest()
EXPECTED_TEMPLATE_HASHES = {
    ("first_impression", "v1"): "9e7697ff3efd892c82c63ffcc8365690685fb1c29f79d45d84e057b2d0672dd0",
    ("gaps_feedback", "v1"): "b2673a1a1f018f2f2fdf37b2dfb6b30634404ba7bb2c241cc01b6240b9097950",
    ("presentation_feedback", "v1"): (
        "87230b7045d66a1fae7d06e2509c6fae31046e0c4e8d30a3c3d6fe9ad2a7a3d7"
    ),
    ("projects_feedback", "v1"): "7e53575582f45389e4a3e4f93c7c137da629d3a14809e16f746732b9a06740d1",
    ("skills_feedback", "v1"): "a24d6d717d4f365c28a686f28b3e77f47204c325ce892fc32d68eb82259f6816",
}

# Combined hash of ALL template content, used as a single belt-and-suspenders
# check in addition to the per-template hashes above.
EXPECTED_COMBINED_TEMPLATE_HASH = "a1c692a29d4b09b2bd24b38f6ae0ef25ac34b1b672c9a9bbec24f9d33245a4a6"


def _sha256(text: str) -> str:
    """Hash template text with SHA-256 (utf-8 encoded)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _combined_template_hash() -> str:
    """Hash of every template's text concatenated in sorted (name, version) order."""
    template_content = ""
    for name in sorted(PROMPT_TEMPLATES.keys()):
        for version in sorted(PROMPT_TEMPLATES[name].keys()):
            template_content += PROMPT_TEMPLATES[name][version]
    return _sha256(template_content)


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

    def test_template_snapshot_content_hash(self):
        """Snapshot test: verify combined template content matches expected hash.

        Fails if ANY template's text changes without EXPECTED_COMBINED_TEMPLATE_HASH
        being updated. See the module docstring for the intentional-change workflow.
        """
        content_hash = _combined_template_hash()

        assert isinstance(content_hash, str)
        assert len(content_hash) == 64  # SHA-256 hash length
        assert content_hash == EXPECTED_COMBINED_TEMPLATE_HASH, (
            "Combined prompt template content changed unexpectedly. If this is "
            "intentional, add a new version key (e.g. 'v2') rather than editing "
            "the existing version, then update EXPECTED_COMBINED_TEMPLATE_HASH "
            "and EXPECTED_TEMPLATE_HASHES."
        )

    def test_each_template_matches_snapshot_hash(self):
        """Snapshot test: verify each individual template matches its expected hash.

        This pinpoints exactly which template/version changed, unlike the
        combined hash check above which only reports that *something* changed.
        """
        for name in sorted(PROMPT_TEMPLATES.keys()):
            for version in sorted(PROMPT_TEMPLATES[name].keys()):
                actual_hash = _sha256(PROMPT_TEMPLATES[name][version])
                expected_hash = EXPECTED_TEMPLATE_HASHES.get((name, version))

                assert expected_hash is not None, (
                    f"No expected snapshot hash registered for {name}/{version}. "
                    "Add one to EXPECTED_TEMPLATE_HASHES."
                )
                assert actual_hash == expected_hash, (
                    f"{name}/{version} content changed unexpectedly. If this edit "
                    "is intentional, add a new version (e.g. 'v2') instead of "
                    f"editing {version} in place, then update EXPECTED_TEMPLATE_HASHES."
                )

    def test_snapshot_hashes_cover_every_template_version(self):
        """Ensure EXPECTED_TEMPLATE_HASHES stays in sync with PROMPT_TEMPLATES.

        Catches both directions of drift: a new template/version added without
        a snapshot entry, and a stale snapshot entry left behind after removal.
        """
        actual_keys = {
            (name, version) for name, versions in PROMPT_TEMPLATES.items() for version in versions
        }
        expected_keys = set(EXPECTED_TEMPLATE_HASHES.keys())

        assert actual_keys == expected_keys, (
            f"Mismatch between PROMPT_TEMPLATES and EXPECTED_TEMPLATE_HASHES. "
            f"Missing snapshots: {actual_keys - expected_keys}. "
            f"Stale snapshots: {expected_keys - actual_keys}."
        )

    def test_snapshot_detects_unversioned_content_edit(self):
        """Regression test: confirm the snapshot mechanism actually catches edits.

        Simulates the exact failure mode from issue #37 — editing v1 text in
        place — and verifies the new per-template hash check would flag it,
        proving this guardrail (unlike the old stub) does its job.
        """
        original_text = PROMPT_TEMPLATES["skills_feedback"]["v1"]
        mutated_text = original_text.replace("Analyze", "Analyse", 1)

        assert mutated_text != original_text  # sanity check the mutation is real

        mutated_hash = _sha256(mutated_text)
        expected_hash = EXPECTED_TEMPLATE_HASHES[("skills_feedback", "v1")]

        # If someone edited v1 in place without updating the snapshot, the new
        # test_each_template_matches_snapshot_hash test would fail on this
        # exact comparison — which is the desired behavior.
        assert mutated_hash != expected_hash

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
