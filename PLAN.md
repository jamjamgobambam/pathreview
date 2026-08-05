# Solution plan

**Issue:** [Add a bias audit report that runs over a sample of stored reviews (#72)](https://github.com/ascherj/pathreview/issues/72)

### Understand

**Root cause.** PathReview ships a bias detector (`safety/bias_detector.py`) but
has no way to measure how well it performs on real data. There is no script that
samples stored reviews, runs them through the detector, and reports where it
misfires. As the Week 8 reproduction showed, the detector's narrow regexes miss
plausibly-biased phrasing (3/3 crafted biased strings went unflagged), and nobody
would know because nothing measures it.

**Expected vs. actual.**
- *Expected:* a maintainer can run one offline command over a sample of stored
  reviews and get a report of false-positive / false-negative rates, broken down
  by demographic signal, with per-review detail for spot-checking.
- *Actual:* no such tool exists; `detect_bias` is not even called in the pipeline
  ([review_service.py:366](core/services/review_service.py#L366) has only a TODO
  comment), so its real-world behavior is completely unmeasured.

### Map

Files I expect to touch or add:

- **`scripts/audit_bias.py`** *(new)* — the audit entry point: sample reviews,
  run the detector, score against labels, emit a report.
- **`tests/fixtures/bias_audit_labels.*`** *(new)* — a small labeled fixture set
  (review text + expected `is_biased` + demographic-signal tag) so FP/FN rates are
  measurable without hand-labeling the live DB.
- **`tests/unit/test_audit_bias.py`** *(new)* — unit tests for the scoring/report
  logic.
- **`safety/bias_detector.py`** *(read-only for now)* — the component under audit;
  no behavior change in this issue.
- **`core/models/review.py`, `core/models/profile.py`, `scripts/seed_db.py`**
  *(read-only)* — to understand the `sections` JSON shape and confirm there are no
  demographic fields to group by.

### Plan

1. **Extract auditable text.** Helper that pulls the text to check out of a
   review's `sections` JSON (`content` + `suggestions`), tolerant of `sections`
   being `None` (failed reviews) or malformed.
2. **Build a labeled sample source.** Load a labeled fixture set of review texts
   (biased / not, with a demographic-signal tag). Support sampling ~100 items;
   fall back to the fixtures when the DB is empty so the script runs anywhere.
3. **Score the detector.** Run `detect_bias` over each sample and tally TP/FP/TN/FN
   overall and per demographic signal, computing precision/recall and FP/FN rates.
4. **Emit the report.** Print a human-readable summary and write a machine-readable
   `bias_audit_report.json`, including per-review detail (text, expected, predicted,
   reason) for spot-checking.
5. **Test it.** Unit-test the scoring math and the report shape on a tiny fixture
   with a known mix of TP/FP/FN so the metrics are deterministic.

### Inputs & outputs

- **Input:** a sample of stored reviews (or the labeled fixture set), a sample-size
  argument (default ~100), and an optional random seed for reproducibility.
- **Output:** (a) a printed summary of FP/FN rates overall and by demographic
  signal; (b) `bias_audit_report.json` with the aggregate metrics plus per-review
  detail. No changes to production behavior or stored data — the audit is read-only.

### Risks & unknowns

- **No demographic fields exist.** `Profile` has no age/background/education data,
  so "breakdown by demographic signal" must come from a *label/tag on the fixture
  text*, not from profile attributes. I'll document this as an explicit design
  choice rather than inventing demographic inference over user data.
- **Ground truth.** FP/FN rates require labeled data; the seeded reviews are all
  benign. A hand-labeled fixture set is the pragmatic source — its size and
  representativeness bound how meaningful the rates are; I'll state that in the
  report rather than overclaiming.
- **DB availability.** The audit should not require a running Postgres to be useful;
  fixture fallback keeps it runnable in CI and by graders.
- **Scope creep.** Tempting to *fix* the detector's misses; this issue is about
  *measuring* them. I'll keep detector logic unchanged and only report.

### Edge cases

- Reviews with `sections = None` or `status = "failed"` → skipped, counted as
  skipped in the report (not silently dropped).
- Empty / whitespace-only review text → treated as not-biased, still counted.
- Sample size larger than available reviews → audit all available and note the
  actual N (no crash, no silent truncation).
- Empty label set / empty DB → exit cleanly with a clear message, non-zero status.
- A demographic-signal tag with zero samples → omitted from per-signal breakdown
  rather than dividing by zero.
