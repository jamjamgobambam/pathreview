# Reproduction — Issue #72: no bias audit over stored reviews

**Issue:** [#72 — Add a bias audit report that runs over a sample of stored reviews](https://github.com/ascherj/pathreview/issues/72)

## How I reproduced it

Because this is a "missing capability" issue, reproduction means demonstrating the
gap concretely rather than triggering a crash. I ran the existing detector the way
an audit would — over stored-review text — using a throwaway script,
[scripts/repro_bias_audit.py](../scripts/repro_bias_audit.py):

```
python scripts/repro_bias_audit.py
```

It feeds `safety.bias_detector.BiasDetector.detect_bias` two sets of strings:

- **Benign** snippets copied verbatim from real seeded reviews in
  [scripts/seed_db.py](../scripts/seed_db.py) (should NOT be flagged).
- **Crafted** biased phrasings about self-taught/bootcamp background and age
  (should be flagged).

## What I observed

```
== Benign seeded review text (want 0 flags) ==   -> 0 flagged  (correct)
== Crafted biased text (want all flags) ==       -> 0 flagged  (WRONG)

Samples checked      : 6
False positives      : 0 / 3 benign
False negatives      : 3 / 3 biased  <-- missed by regex
Demographic breakdown: UNAVAILABLE (Profile model has no demographic fields)
```

Three concrete confirmations of the issue:

1. **No audit exists.** There is no `scripts/audit_bias.py`, and nothing measures
   false-positive / false-negative rates or emits a report. The only way to learn
   anything about detector accuracy today is an ad-hoc script like this one.
2. **The detector is not even wired in.** `detect_bias` is never called in the
   generation pipeline — [core/services/review_service.py:366](../core/services/review_service.py#L366)
   only has a `# 3. Check for bias in recommendations` comment.
3. **Blind spots are real.** The narrow regex patterns missed all three plausibly
   biased strings (3/3 false negatives) — exactly the kind of blind spot the
   requested audit is meant to surface and quantify.

## Note carried into planning

The issue asks for a breakdown "by demographic signal," but the `Profile` model has
no demographic fields. The audit will have to derive signals from review text (or a
labeled fixture set) rather than from profile attributes — captured in
[PLAN.md](../PLAN.md) under Risks & unknowns.
