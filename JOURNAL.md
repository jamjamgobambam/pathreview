# Contribution Journal - PathReview

## Week 7 - Issue Selection & Problem Understanding

### Issue Selected

- **Issue:** [#146 - PII scrubber fails to redact parenthesized US phone numbers](https://github.com/ascherj/pathreview/issues/146)
- **Tier:** Tier 1, labeled `good first issue`
- **Labels:** `bug`, `safety`, `tier-1`, `good first issue`
- **Subsystem:** Safety layer
- **Primary file:** `safety/pii_scrubber.py`
- **Test file:** `tests/unit/test_pii_scrubber.py`
- **Branch name:** `fix/146-pii-parenthesized-phone`

### Problem Summary

PathReview has a safety component called `PIIScrubber` that is supposed to redact personally identifiable information from text. The bug I chose is that the scrubber catches some US phone-number formats, such as `555-123-4567`, but misses the very common parenthesized format `(555) 123-4567`. That means `scrub()` can return text that still contains a phone number, and `detect()` can report no PII even though a phone number is present. A successful fix should make parenthesized US phone numbers redact and detect consistently without breaking already-supported phone formats or causing false positives on unrelated numbers.

### Why This Issue Is a Good Fit

This is a good Tier 1 issue because it is important but tightly scoped. The bug affects privacy/safety behavior, so the outcome matters, but the likely implementation is contained to one regex in `safety/pii_scrubber.py` plus focused tests in `tests/unit/test_pii_scrubber.py`. The issue also has a clear reproduction and objective success criteria: the existing phone tests should pass after the fix.

### Setup Confirmation

- Forked repository: [somtizle/pathreview](https://github.com/somtizle/pathreview)
- Working branch: `fix/146-pii-parenthesized-phone`
- Local environment: repository cloned and Python test environment available
- Setup evidence: the focused PII scrubber tests were run locally and their failing output was committed in `docs/repro-146.txt`

## Week 8 - Reproduction & Solution Planning

**Reproduction commit link:** [14e5fb0 - test: capture failing phone-redaction tests reproducing #146](https://github.com/somtizle/pathreview/commit/14e5fb0ee94ba2621dee5d5ed2c952c8643957d4)

**Reproduction summary:** I reproduced the issue by running the phone-related tests in `tests/unit/test_pii_scrubber.py`. The local run confirms four failures: parenthesized numbers such as `(555) 123-4567` are not redacted by `scrub()`, and `detect()` returns no phone detection for that format.

**PLAN.md link:** [PLAN.md on the working branch](https://github.com/somtizle/pathreview/blob/fix/146-pii-parenthesized-phone/PLAN.md)

**Walkthrough video (recommended):** Not recorded yet. The graded deliverables are the reproduction commit, `PLAN.md`, and this Week 8 journal update.

**Blockers or open questions:** No major blockers. The main implementation risk for Week 9 is widening the US phone regex enough to catch whitespace and parenthesized formats without over-matching SSNs, version numbers, or long digit identifiers.

## Week 9 - Solution Building & PR Submission

### Check-in 1 (mid-week)

**Current progress:** I completed the main implementation tasks from `PLAN.md`: I updated the `phone_us` pattern in `safety/pii_scrubber.py` so parenthesized US phone numbers and whitespace-separated US formats are detected, and I kept the pattern bounded so it does not match inside longer word or digit strings. I also updated `tests/unit/test_pii_scrubber.py` to cover the new phone-number formats, full `detect()` values, detection positions, and false-positive guard cases for SSNs, version numbers, and long tracking IDs.

**Next steps:** I need to finish the final self-review, push the implementation branch, open the upstream pull request, and paste the live PR link into Check-in 2. I also need to document the project-wide `make check` and `make test-unit` results honestly because the focused PII scrubber tests pass, but the broader repository currently has unrelated baseline failures outside this fix.

**Blockers:** No code blockers. The only workflow blocker is GitHub authentication/permissions for creating the upstream PR from this environment, so the PR may need to be opened manually from the GitHub compare page.

---

### Check-in 2 (end of week)

**PR link:** Pending live PR URL. Open it from this compare page, then replace this line with the created PR link: https://github.com/ascherj/pathreview/compare/main...somtizle:pathreview:fix/146-pii-parenthesized-phone?expand=1

**Branch:** `fix/146-pii-parenthesized-phone`

**What you built:** I fixed the PII scrubber so common US phone numbers like `(555) 123-4567`, `(555)123-4567`, and `+1 (555) 123-4567` are redacted and detected as `phone_us`. The fix broadens the US phone regex to allow whitespace and balanced parenthesized area codes while preserving boundaries that avoid partial matches inside longer strings.

**Tests added or updated:** I updated `tests/unit/test_pii_scrubber.py`. The tests now cover parenthesized phone-number redaction, no-space parenthesized phone numbers, `+1` plus parenthesized area codes, full detected phone values and positions from `detect()`, and false-positive protection for version numbers, SSNs, and long tracking identifiers.

**Self-review confirmation:** [x] make check passes for changed files; full repo `make check` was run and fails on unrelated pre-existing lint issues outside this PR. [x] make test-unit passes for the changed PII scrubber test file; full repo `make test-unit` was run and fails on unrelated pre-existing unit-test failures outside this PR.

**Draft PR feedback received from:** none
