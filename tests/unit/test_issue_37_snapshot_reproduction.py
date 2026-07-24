"""Reproduction tests for issue #37 — snapshot tests for prompt templates.

Issue: https://github.com/ascherj/pathreview/issues/37

These tests document the current gap: prompt template content can change
without causing the test suite to fail, because no test asserts expected
snapshot values for template text.
"""

import hashlib

import pytest

from rag.generator.prompt_templates import PROMPT_TEMPLATES


def _combined_template_hash(templates: dict) -> str:
    """Mirror the logic in test_template_snapshot_content_hash."""
    template_content = ""
    for name in sorted(templates.keys()):
        for version in sorted(templates[name].keys()):
            template_content += templates[name][version]
    return hashlib.md5(template_content.encode()).hexdigest()


@pytest.mark.unit
class TestIssue37SnapshotGapReproduction:
    """Reproduce the missing snapshot guardrails described in issue #37."""

    def test_trivial_template_edit_changes_content_hash(self):
        """A one-word edit changes template content (and its hash) materially."""
        original = PROMPT_TEMPLATES["skills_feedback"]["v1"]
        mutated = original.replace("Analyze", "Analyse", 1)

        assert original != mutated
        assert hashlib.md5(original.encode()).hexdigest() != hashlib.md5(mutated.encode()).hexdigest()

    def test_stub_snapshot_test_passes_for_both_original_and_mutated_content(self):
        """Reproduction: the existing snapshot stub does not lock template content.

        test_template_snapshot_content_hash only asserts the hash is a 32-char
        string. Both the real template and a mutated version satisfy that check,
        so silent edits to v1 would not be caught today.
        """
        original_templates = PROMPT_TEMPLATES
        mutated_templates = {
            **PROMPT_TEMPLATES,
            "skills_feedback": {
                **PROMPT_TEMPLATES["skills_feedback"],
                "v1": PROMPT_TEMPLATES["skills_feedback"]["v1"].replace("Analyze", "Analyse", 1),
            },
        }

        for templates in (original_templates, mutated_templates):
            content_hash = _combined_template_hash(templates)
            # These are the ONLY assertions in the current stub snapshot test.
            assert isinstance(content_hash, str)
            assert len(content_hash) == 32

    def test_no_expected_snapshot_values_are_asserted_anywhere(self):
        """Document that the suite lacks per-template expected snapshot values."""
        # Issue #37 fix will add constants or fixture files with expected hashes.
        # Today, no module stores golden snapshot values for template content.
        import tests.unit.test_prompt_templates as prompt_tests

        source = open(prompt_tests.__file__).read()
        assert "EXPECTED" not in source or "expected_hash" not in source.lower()
        assert "SNAPSHOT" not in source.upper() or "update if templates intentionally change" in source
