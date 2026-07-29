# Reproduction for issue #152: Faithfulness checker can never mark short claims as supported
# Run: python3 repro_152.py
# Expected (buggy) output: 0.0
# Both claims ARE supported by context, but score comes back as unsupported
# because _is_supported() requires 2+ overlapping non-stopword tokens,
# and these short claims only share 1 token with their supporting context.

from rag.evaluator.faithfulness_checker import FaithfulnessChecker

f = FaithfulnessChecker()
result = f.check("Knows Python. Knows SQL.", [{"text": "python expert"}, {"text": "sql expert"}])
print(f"Faithfulness score: {result}")
assert result == 0.0, "Bug not reproduced -- score changed, check if already fixed"
print("Bug reproduced: short supported claims scored as 0.0 (should be higher)")
