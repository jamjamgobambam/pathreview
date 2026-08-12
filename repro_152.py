# Reproduction for issue #152: Faithfulness checker can never mark short claims as supported
# Run: python3 repro_152.py
#
# BEFORE FIX: score was 0.0 (bug) -- both claims are supported by context,
# but _is_supported() required 2+ overlapping non-stopword tokens, which
# short claims like "Knows Python" could never satisfy against a 1-token
# match in context.
#
# AFTER FIX: score is > 0.0, correctly reflecting that the claim is
# supported by the context.

from rag.evaluator.faithfulness_checker import FaithfulnessChecker

f = FaithfulnessChecker()
result = f.check(
    'Knows Python. Knows SQL.',
    [{'text': 'python expert'}, {'text': 'sql expert'}]
)
print(f"Faithfulness score: {result}")
assert result > 0.0, "Fix regressed -- short supported claim scored as 0.0 again"
print("Fix confirmed: short supported claim now scores above 0.0")
