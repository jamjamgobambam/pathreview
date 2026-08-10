"""Red-team suite: verifies safety/prompt_defense.py blocks a curated set of
known prompt injection attacks.

Attack payloads live in tests/fixtures/injection_attempts/ as individual .txt
files, one attack per file, so the corpus can grow without touching this file.
See docs/PROMPT_INJECTION_RESEARCH.md for the technique research behind this
corpus and its known gaps.
"""

from pathlib import Path

import pytest

from safety.prompt_defense import PromptDefense

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "injection_attempts"

# If this drops, either fixtures were deleted or the path is wrong - either
# way we want a loud failure instead of a suite that silently runs 0 cases.
MIN_EXPECTED_PAYLOADS = 10


def _load_payloads() -> list[Path]:
    """Load attack payload files from the fixture corpus.

    Returns:
        Sorted list of paths to .txt payload files in FIXTURES_DIR
    """
    return sorted(FIXTURES_DIR.glob("*.txt"))


PAYLOAD_FILES = _load_payloads()


@pytest.mark.security
class TestPromptInjectionRedTeam:
    """Every payload in the corpus must be detected as an injection attempt."""

    def test_corpus_meets_minimum_size(self) -> None:
        """Guard against the corpus being silently emptied or misconfigured.

        A PR that deletes fixture files would otherwise make the parametrized
        test below pass vacuously (zero cases collected = zero failures).
        """
        assert len(PAYLOAD_FILES) >= MIN_EXPECTED_PAYLOADS, (
            f"Expected at least {MIN_EXPECTED_PAYLOADS} attack payloads in "
            f"{FIXTURES_DIR}, found {len(PAYLOAD_FILES)}. Fixtures may have "
            "been deleted or the corpus path may be wrong."
        )

    @pytest.mark.parametrize("payload_file", PAYLOAD_FILES, ids=[f.stem for f in PAYLOAD_FILES])
    def test_known_attack_is_blocked(self, payload_file: Path) -> None:
        """Each curated attack payload must be flagged as an injection attempt."""
        attack_text = payload_file.read_text()

        is_injection = PromptDefense.is_injection_attempt(attack_text)

        assert is_injection is True, (
            f"Attack payload '{payload_file.name}' was NOT detected as a "
            "prompt injection attempt. This is a regression in "
            "safety/prompt_defense.py."
        )
