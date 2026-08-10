"""Reproduction script for issue #153.

Faithfulness checker crashes when a context chunk has `text: None`.
https://github.com/ascherj/pathreview/issues/153

Run with:
    python scripts/repro_issue_153.py

Expected (buggy) result: a TypeError is raised and printed below, because
`chunk.get("text", "")` only falls back to "" when the "text" key is
missing -- not when it is present with a None value. `" ".join(...)` then
tries to join a None into the context string and blows up.

Once fixed, this script should print a faithfulness score instead of a
traceback.
"""

from rag.evaluator.faithfulness_checker import FaithfulnessChecker


def main() -> None:
    checker = FaithfulnessChecker()
    feedback = "Has Python skills"
    context_chunks = [{"text": None}]

    print(f"feedback: {feedback!r}")
    print(f"context_chunks: {context_chunks!r}")
    print("Calling checker.check(feedback, context_chunks)...\n")

    try:
        score = checker.check(feedback, context_chunks)
    except TypeError as exc:
        print(f"REPRODUCED BUG: TypeError raised as expected -> {exc}")
        raise
    else:
        print(f"No crash -- faithfulness score: {score}")


if __name__ == "__main__":
    main()
