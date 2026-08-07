"""Reproduction for issue #153: Faithfulness checker crashes on text:None.

https://github.com/ascherj/pathreview/issues/153

Run:
    .venv/bin/python scripts/repro_issue_153.py

Expected (buggy) behavior: raises
    TypeError: sequence item 0: expected str instance, NoneType found
from rag/evaluator/faithfulness_checker.py, where the context text is built
with `chunk.get("text", "")`. The `.get(..., "")` default only applies when
the "text" key is absent; when a chunk has an explicit `"text": None`, `.get`
returns None and `" ".join([...])` raises TypeError.

After the fix (coerce None to "" via `chunk.get("text") or ""`) this script
prints a float score in [0.0, 1.0] instead of crashing.
"""

from rag.evaluator.faithfulness_checker import FaithfulnessChecker


def main() -> None:
    checker = FaithfulnessChecker()
    feedback = "The developer has strong Python skills and Django experience."
    # A chunk whose text failed to extract during ingestion -> explicit None.
    context_chunks = [{"text": None}]

    score = checker.check(feedback, context_chunks)
    print(f"faithfulness score: {score}")


if __name__ == "__main__":
    main()
