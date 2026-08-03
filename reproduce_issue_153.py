"""Reproduction script for issue #153.

Run this against main (before the fix) to observe the TypeError.
Run it on this branch (with the fix applied) to see it return a valid score.
"""

from rag.evaluator.faithfulness_checker import FaithfulnessChecker

checker = FaithfulnessChecker()

feedback = "Knows Python."
context_chunks = [{"text": None}]

print("Testing FaithfulnessChecker.check() with a None context chunk text...")
score = checker.check(feedback, context_chunks)
print(f"Success — no crash. Score returned: {score}")
