"""Loader for the prompt-injection red-team corpus.

Reads curated attack payloads (grouped by category) and a benign control set
from ``tests/fixtures/injection_attempts/`` so the security suite can be
parametrized over a growing corpus without editing test code. Add a new payload
by appending a line to the relevant fixture file — no code change required.
"""

from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "injection_attempts"

# Fixture files whose every payload MUST be flagged as an injection attempt.
ATTACK_FILES = (
    "role_switching.txt",
    "instruction_override.txt",
    "template_injection.txt",
    "code_execution.txt",
    "separator.txt",
)

# Fixture file whose every payload MUST NOT be flagged (false-positive guard).
BENIGN_FILE = "benign.txt"


def _load_payloads(filename: str) -> list[str]:
    """Read one payload per non-empty, non-comment line from a fixture file.

    Args:
        filename: Name of a file inside ``fixtures/injection_attempts/``.

    Returns:
        The payload strings, stripped, in file order.
    """
    path = FIXTURES_DIR / filename
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line for line in (raw.strip() for raw in lines) if line and not line.startswith("#")]


def load_attack_payloads() -> list[tuple[str, str]]:
    """Load every attack payload tagged with its category.

    Returns:
        ``(category, payload)`` tuples across all attack fixture files, where
        ``category`` is the fixture filename without its ``.txt`` suffix.
    """
    payloads: list[tuple[str, str]] = []
    for filename in ATTACK_FILES:
        category = filename.removesuffix(".txt")
        payloads.extend((category, payload) for payload in _load_payloads(filename))
    return payloads


def load_benign_payloads() -> list[str]:
    """Load the benign control payloads.

    Returns:
        Benign strings that must not be flagged as injection attempts.
    """
    return _load_payloads(BENIGN_FILE)
