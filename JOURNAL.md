## Week 7 — Issue selection

**Issue link:** [[paste link here]](https://github.com/ascherj/pathreview/issues/88)

**Issue title:** POST /reviews endpoint has no test for when the profile has no ingested documents #88

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The /reviews endpoint currently assumes a profile will already have some documents ingested before a review is requested, and that assumption is never checked in the test suite. If someone triggers a review for a profile that exists but hasn't had anything ingested yet, it's unclear whether the endpoint fails gracefully or throws an unhandled exception, since no test exists to pin down the expected behavior. This is a gap in edge-case coverage rather than a confirmed bug — the fix is really about writing a regression test that calls the endpoint under this specific condition and asserts a clean, well-formed error response (e.g. a 4xx with a descriptive message) instead of a server crash. A successful fix gives the team confidence that this edge case is handled predictably and prevents future changes from silently reintroducing a crash for profiles with no ingested content.

**Branch name:** test/88-review-endpoint-test

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger