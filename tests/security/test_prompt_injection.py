"""Red-team suite for safety/prompt_defense.py.

Loads the curated attack corpus under tests/fixtures/injection_attempts/ and
asserts PromptDefense behaves as documented per fixture. See PLAN.md for the
corpus design, the sourcing methods used, and the known_gaps rationale.
"""

import json
from pathlib import Path

import pytest

from safety.prompt_defense import PromptDefense

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "injection_attempts"


def _load_fixtures() -> list[tuple[str, dict]]:
    """Load (payload, metadata) pairs from the injection_attempts corpus.

    Returns:
        A list of (payload, metadata) tuples, sorted by fixture path so
        collection order is deterministic across runs.
    """
    fixtures = []
    for json_path in sorted(FIXTURES_DIR.glob("*/*.json")):
        txt_path = json_path.with_suffix(".txt")
        meta = json.loads(json_path.read_text())
        payload = txt_path.read_text()
        fixtures.append((payload, meta))
    return fixtures


_ALL_FIXTURES = _load_fixtures()

DETECT_FIXTURES = [
    pytest.param(payload, meta, id=f"{meta['category']}/{meta['id']}")
    for payload, meta in _ALL_FIXTURES
    if meta["mechanism"] == "detect"
]

SANITIZE_FIXTURES = [
    pytest.param(payload, meta, id=f"{meta['category']}/{meta['id']}")
    for payload, meta in _ALL_FIXTURES
    if meta["mechanism"] == "sanitize"
]

# Markers sanitize() is designed to strip. A "blocked" sanitize fixture means
# none of these remain in the output.
SANITIZE_MARKERS = ("{{", "}}", "{%", "%}", "<", ">")


@pytest.mark.security
class TestPromptInjectionRedTeam:
    """Curated red-team suite sourced from tests/fixtures/injection_attempts/."""

    def test_fixture_corpus_is_loaded(self) -> None:
        """Sanity check that the fixture corpus is discovered, not silently empty."""
        assert len(_ALL_FIXTURES) > 0
        assert len(DETECT_FIXTURES) > 0
        assert len(SANITIZE_FIXTURES) > 0

    @pytest.mark.parametrize("payload,meta", DETECT_FIXTURES)
    def test_detect_fixture(self, payload: str, meta: dict) -> None:
        """is_injection_attempt() matches the expected outcome for each detect fixture."""
        detected = PromptDefense.is_injection_attempt(payload)
        assert detected == meta["expected_blocked"], meta["note"]

    @pytest.mark.parametrize("payload,meta", SANITIZE_FIXTURES)
    def test_sanitize_fixture(self, payload: str, meta: dict) -> None:
        """sanitize() removes the raw injection marker for each sanitize fixture."""
        sanitized = PromptDefense.sanitize(payload)
        marker_present = any(marker in sanitized for marker in SANITIZE_MARKERS)
        assert (not marker_present) == meta["expected_blocked"], meta["note"]
