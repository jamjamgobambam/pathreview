"""Red-team test suite for the prompt-injection defense (issue #71).

Feeds a curated corpus of known injection payloads through
``PromptDefense.is_injection_attempt`` and asserts every one is blocked, plus a
benign control set that must not be flagged. Payloads live in
``tests/fixtures/injection_attempts/`` and are loaded by ``injection_corpus`` so
the corpus can grow without editing this file.

Run with:

    pytest tests/security -m security -v
"""

import pytest

from safety.prompt_defense import PromptDefense
from tests.security.injection_corpus import load_attack_payloads, load_benign_payloads

ATTACK_PAYLOADS = load_attack_payloads()
BENIGN_PAYLOADS = load_benign_payloads()


@pytest.mark.security
class TestPromptInjectionRedTeam:
    """Assert the injection defense blocks known attacks and allows benign input."""

    @pytest.mark.parametrize(
        ("category", "payload"),
        ATTACK_PAYLOADS,
        ids=[f"{category}::{payload[:40]}" for category, payload in ATTACK_PAYLOADS],
    )
    def test_attack_payload_is_blocked(self, category: str, payload: str) -> None:
        """Every curated attack payload must be detected as an injection attempt."""
        assert (
            PromptDefense.is_injection_attempt(payload) is True
        ), f"[{category}] payload was NOT blocked: {payload!r}"

    @pytest.mark.parametrize("payload", BENIGN_PAYLOADS)
    def test_benign_payload_is_allowed(self, payload: str) -> None:
        """Benign portfolio-review input must not be flagged (false-positive guard)."""
        assert (
            PromptDefense.is_injection_attempt(payload) is False
        ), f"benign payload was incorrectly blocked: {payload!r}"

    def test_corpus_is_non_empty(self) -> None:
        """Guard against a silent fixture-loading failure yielding an empty suite.

        Without this, a bad path or empty fixture directory would make the
        parametrized tests collect zero cases and the suite would pass vacuously.
        """
        assert len(ATTACK_PAYLOADS) >= 15, "attack corpus unexpectedly small — check fixtures"
        assert len(BENIGN_PAYLOADS) >= 5, "benign corpus unexpectedly small — check fixtures"
