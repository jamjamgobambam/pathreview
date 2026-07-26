"""Reproduction script for issue #153.

Faithfulness checker crashes when a context chunk has `text: None`.

This script demonstrates:
1. The original buggy behavior (using `dict.get("text", "")` which returns
   `None` when the key exists but its value is `None`).
2. That the fix (using `chunk.get("text") or ""`) handles it gracefully.

Run with:  uv run --extra dev python reproduce_issue_153.py
"""

from rag.evaluator.faithfulness_checker import FaithfulnessChecker


def simulate_original_bug() -> bool:
    """Reproduce the original TypeError from the pre-fix code path.

    The original line was:
        context_text = " ".join([chunk.get("text", "") for chunk in context_chunks])

    When a chunk has {"text": None}, `dict.get("text", "")` returns `None`
    (not `""`), because the default only applies when the key is *missing*.
    Passing `None` to `str.join()` raises `TypeError`.
    """
    context_chunks = [{"text": None}]
    try:
        # Simulate the original buggy expression
        # noqa: E501 — intentionally reproduces the bug; type ignore for mypy
        context_text = " ".join(
            [chunk.get("text", "") for chunk in context_chunks]  # type: ignore[misc]
        )
        print(f"  No error — context_text = {context_text!r}")
    except TypeError as exc:
        print(f"  TypeError reproduced: {exc}")
        return True
    return False


def demonstrate_fix() -> None:
    """Show that the fixed code path handles None gracefully."""
    checker = FaithfulnessChecker()
    feedback = "Has Python skills"
    context_chunks = [{"text": None}]

    score = checker.check(feedback, context_chunks)
    print(f"  FaithfulnessChecker.check() returned score = {score}")
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
    print("  Fix confirmed: no crash, valid score returned.")


if __name__ == "__main__":
    print("=" * 60)
    print("Issue #153 Reproduction: Faithfulness checker crashes on text: None")
    print("=" * 60)

    print("\n[1] Simulating original buggy code path:")
    bug_reproduced = simulate_original_bug()

    print("\n[2] Running fixed FaithfulnessChecker.check():")
    demonstrate_fix()

    print("\n" + "=" * 60)
    if bug_reproduced:
        print("Result: Bug reproduced successfully; fix verified working.")
    else:
        print("Result: Bug not reproduced (unexpected).")
    print("=" * 60)
