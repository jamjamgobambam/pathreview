"""Reproduce PathReview issue #152.

The faithfulness checker incorrectly marks short supported claims as
unsupported because each claim contains only one meaningful overlapping token.
"""

from rag.evaluator.faithfulness_checker import FaithfulnessChecker


def main() -> None:
    """Run the minimal reproduction for issue #152."""
    checker = FaithfulnessChecker()

    contexts = [
        {"text": "python expert"},
        {"text": "sql expert"},
    ]

    score = checker.check("Knows Python. Knows SQL.", contexts)

    print("Claims: Knows Python. Knows SQL.")
    print("Contexts: python expert | sql expert")
    print("Expected: both claims should be supported")
    print(f"Actual faithfulness score: {score}")


if __name__ == "__main__":
    main()