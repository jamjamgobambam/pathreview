"""Reproduction script for issue #152.

Faithfulness checker can never mark short claims as supported.

Run:  python repro_152.py
"""

from rag.evaluator.faithfulness_checker import FaithfulnessChecker

checker = FaithfulnessChecker()

STOP_WORDS = {
    "a",
    "an",
    "the",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "and",
    "or",
    "but",
    "in",
    "of",
    "to",
    "for",
    "that",
}

CASES = [
    (
        "A. short claim, context uses punctuation after the keyword",
        "Knows Python",
        "The candidate knows Python.",
    ),
    (
        "B. short claim, context paraphrases the verb",
        "Knows Python",
        "The candidate is proficient in Python and ships production services.",
    ),
    (
        "C. short claim, single meaningful token after stop-word filtering",
        "The project is documented",
        "The project is thoroughly documented in the README.",
    ),
    (
        "D. short claim below the 10-char extraction floor",
        "Uses Rust",
        "The candidate uses Rust for systems work.",
    ),
    (
        "E. short claim, both tokens verbatim in context (happy path)",
        "Knows Python",
        "The candidate knows Python and has built several backend services.",
    ),
    (
        "CONTROL: long supported claim (must stay 1.0)",
        "The developer has strong Python skills and experience with Django.",
        "The portfolio shows Python expertise and Django framework experience.",
    ),
    (
        "CONTROL: unsupported claim (must stay 0.0)",
        "This developer is an expert in Rust systems programming.",
        "The developer has Python and JavaScript experience.",
    ),
]

print(f"{'score':>6}  {'claims':>6}  label")
print("-" * 78)
for label, feedback, context in CASES:
    chunks = [{"text": context}]
    claims = checker._extract_claims(feedback)
    score = checker.check(feedback, chunks)
    print(f"{score:>6.2f}  {len(claims):>6}  {label}")
    print(f"          context={context!r}")
    for claim in claims:
        claim_tokens = set(claim.lower().split())
        context_tokens = set(context.lower().split())
        meaningful = (claim_tokens & context_tokens) - STOP_WORDS
        print(
            f"          meaningful_overlap={sorted(meaningful)} " f"(n={len(meaningful)}, need >=2)"
        )
    if not claims:
        print("          (no claims extracted -> neutral 0.5 default)")
    print()
print("-" * 78)
print("Expected: rows A-E all score 1.0 - the context plainly supports each claim.")
print("Actual:   A, B, C score 0.0 and D falls back to 0.5.")
