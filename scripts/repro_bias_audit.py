"""Reproduction for issue #72 — no bias audit exists over stored reviews.

Run:  python scripts/repro_bias_audit.py

This throwaway script documents the *current* state before the fix. It runs the
existing ``safety.bias_detector.BiasDetector`` over representative stored-review
text (copied from ``scripts/seed_db.py``) plus a few crafted biased strings, and
shows what an audit would need to report but cannot today:

  * There is no ``scripts/audit_bias.py`` and no report of FP/FN rates.
  * ``detect_bias`` is never called in the generation pipeline
    (``core/services/review_service.py`` only has a TODO comment for it).
  * The detector's narrow regexes silently miss plausibly-biased phrasing.
"""

from safety.bias_detector import BiasDetector

# Benign, real seeded-review snippets (expected: NOT biased).
BENIGN = [
    "Your GitHub profile shows strong proficiency in Python and JavaScript.",
    "Your weather app and todo list are common beginner exercises that won't "
    "differentiate you from other candidates at your level.",
    "None of your current projects demonstrate end-to-end thinking.",
]

# Phrasings a reviewer would want flagged (crafted; expected: biased).
SHOULD_FLAG = [
    "As a self-taught developer you probably lack the fundamentals a CS degree gives.",
    "Older developers tend to struggle with modern frameworks like React.",
    "Bootcamp grads rarely have the depth needed for senior roles.",
]


def _run(label: str, samples: list[str]) -> tuple[int, int]:
    print(f"\n== {label} ==")
    flagged = 0
    for s in samples:
        is_biased, reason = BiasDetector.detect_bias(s)
        flagged += is_biased
        print(f"  [{'FLAG' if is_biased else '    '}] {reason or '-':40s} | {s[:60]}")
    return flagged, len(samples)


def main() -> None:
    fp, n_benign = _run("Benign seeded review text (want 0 flags)", BENIGN)
    hit, n_biased = _run("Crafted biased text (want all flags)", SHOULD_FLAG)

    print("\n== What an audit would report (but cannot today) ==")
    print(f"  Samples checked      : {n_benign + n_biased}")
    print(f"  False positives      : {fp} / {n_benign} benign")
    print(f"  False negatives      : {n_biased - hit} / {n_biased} biased  <-- missed by regex")
    print("  Demographic breakdown: UNAVAILABLE (Profile model has no demographic fields)")
    print("\n  No scripts/audit_bias.py exists; detect_bias is never called in the pipeline.")


if __name__ == "__main__":
    main()
