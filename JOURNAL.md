## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/91

**Issue title:** Review page shows a blank section when the confidence field is below 0.3 instead of a warning badge

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The ReviewSection component is supposed to display a "Low confidence" badge whenever a review's confidence score falls below 0.3, warning users that the result may be unreliable. At some point the conditional logic that renders this badge was removed, so instead of a warning, the component renders an empty div — the section just looks broken or missing. A successful fix restores the conditional rendering in ReviewSection.tsx so the badge appears correctly whenever confidence is below the threshold, and the section renders normally otherwise.

**Branch name:** fix/91-review-section-confidence-badge

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger — link not yet located; posted in Slack asking for it

**Note:** Issue #91 was later closed/removed by instructor feedback. Pivoted to a new issue (#159) starting Week 8 — see below.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/saharii27/pathreview/commit/c64f2f5

**Reproduction summary:**
Ran `.venv/bin/pytest tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty -q` and confirmed the failure: the warning log "Empty chunks list provided to BatchEmbeddingProcessor" is clearly printed to stdout, but `caplog.text` is empty, causing the assertion to fail. This confirms structlog output isn't propagating into Python's standard `logging` module, which is what pytest's `caplog` fixture reads from.

**PLAN.md link:** https://github.com/saharii27/pathreview/blob/fix/159-structlog-caplog-pytest/PLAN.md

**Walkthrough video (recommended):** [not recorded — optional, not graded]

**Blockers or open questions:**
Need to determine the cleanest way to configure structlog to propagate to stdlib logging in tests/conftest.py — likely via structlog.stdlib processors or the capture_logs context manager.
