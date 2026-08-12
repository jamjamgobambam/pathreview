# Written by Kevin Balbuena Montes

"""Red-team tests for PathReview's prompt injection defense."""

import json
from pathlib import Path
from typing import Any

import pytest

from safety.prompt_defense import PromptDefense

FIXTURE_DIRECTORY = Path(__file__).resolve().parents[1] / "fixtures" / "injection_attempts"


def load_fixture_cases(filename: str) -> list[dict[str, Any]]:
    """Load prompt-injection test cases from a JSON fixture file.

    Args:
        filename: Name of the JSON fixture file inside the injection fixture
            directory.

    Returns:
        A list of dictionaries containing the fixture cases.
    """
    fixture_path = FIXTURE_DIRECTORY / filename

    with fixture_path.open(encoding="utf-8-sig") as fixture_file:
        cases = json.load(fixture_file)

    if not isinstance(cases, list):
        raise TypeError(f"Fixture file {filename} must contain a JSON list")

    return cases


ATTACK_CASES = load_fixture_cases("attacks.json")
BENIGN_CASES = load_fixture_cases("benign.json")
KNOWN_BYPASS_CASES = load_fixture_cases("known_bypasses.json")


@pytest.mark.security
class TestPromptInjectionRedTeam:
    """Verify known attacks are blocked and legitimate prompts are allowed."""

    @pytest.mark.parametrize(
        "case",
        ATTACK_CASES,
        ids=[case["id"] for case in ATTACK_CASES],
    )
    def test_known_attack_is_detected(self, case: dict[str, Any]) -> None:
        """Known prompt injection attacks should be detected."""
        actual = PromptDefense.is_injection_attempt(case["payload"])

        assert actual is case["expected_detected"], (
            f"Attack case '{case['id']}' was not detected. "
            f"Category: {case['category']}. "
            f"Description: {case['description']}"
        )

    @pytest.mark.parametrize(
        "case",
        BENIGN_CASES,
        ids=[case["id"] for case in BENIGN_CASES],
    )
    def test_benign_input_is_not_flagged(self, case: dict[str, Any]) -> None:
        """Legitimate prompts should not be classified as injection attempts."""
        actual = PromptDefense.is_injection_attempt(case["payload"])

        assert actual is case["expected_detected"], (
            f"Benign case '{case['id']}' was incorrectly classified. "
            f"Category: {case['category']}. "
            f"Description: {case['description']}"
        )


@pytest.mark.security
class TestPromptInjectionKnownBypasses:
    """Document prompt injection attacks the current defense does not yet block."""

    @pytest.mark.xfail(
        strict=False,
        reason="Known prompt injection bypasses documented by Issue #71.",
    )
    @pytest.mark.parametrize(
        "case",
        KNOWN_BYPASS_CASES,
        ids=[case["id"] for case in KNOWN_BYPASS_CASES],
    )
    def test_known_bypass_should_be_detected(self, case: dict[str, Any]) -> None:
        """Known bypasses should eventually be detected by PromptDefense."""
        actual = PromptDefense.is_injection_attempt(case["payload"])

        assert actual is case["expected_detected"], (
            f"Known bypass '{case['id']}' remains undetected. " f"Reason: {case['reason']}"
        )
