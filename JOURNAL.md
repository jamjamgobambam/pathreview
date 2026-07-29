## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Why this tier:** Chose Tier 1 as my first contribution to a large codebase — the fix is contained to one regex in one file with pre-written tests, a realistic scope for a two-week window.

**Problem summary:**
The PII scrubber in `safety/pii_scrubber.py` uses one regex to find phone numbers, but it only allows dashes or dots between digit groups so parenthesized numbers like (555) 123-4567 don't match and slip through un-redacted, with `detect()` reporting no PII. A successful fix widens the pattern to catch parenthesized and space-separated formats without breaking the dashed/dotted ones already handled, making the four failing tests in `tests/unit/test_pii_scrubber.py` pass.

**Branch name:** fix/146-parenthesized-phone-number-error

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/soccerjonj/pathreview/commit/447244e702bc3be4794dcd632922aa98392c274d

**Reproduction summary:**
I ran the pytest `pytest tests/unit/test_pii_scrubber.py -v` and observed 20 passes and 5 failures. The tests that failed were: `test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`, `test_phone_at_start_of_text`, and lastly a test that surfaced a second bug, `test_mixed_pii_and_text`. Line 15 is where my reported bug occurs. The `phone_us` regex logic currently doesn't work for parenthesized and space-separated numbers. Line 18 is where the second bug I found is. The second bug has to do with the `street_address` regex pattern. This is out of scope for me but noted. 

**PLAN.md link:** https://github.com/soccerjonj/pathreview/blob/fix/146-parenthesized-phone-number-error/PLAN.md

**Blockers or open questions:**
I'm not sure whether the `street_address` false-positive bug I found in `test_mixed_pii_and_text` should get its own GitHub issue filed against upstream, or if noting it here is sufficient for this assignment. I'm also unsure whether reviewers will want the regex to handle repeated/multiple separator characters (e.g. double spaces) or if treating that as out of scope is the right call.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented and committed both sub-tasks from `PLAN.md`: widened the `phone_us` regex in `safety/pii_scrubber.py` to accept a space as a separator (commit `3acc732`), and added a no-space parenthesized edge case (`"(555)123-4567"`) to `test_us_phone_formats` (commit `aad7a64`). All 4 originally-failing phone tests now pass, plus the new edge case. Also, cleaned up four pre-existing lint issues across both touched files (`E501`, `B007` in `pii_scrubber.py`; two `F841`s in `test_pii_scrubber.py`).

**Next steps:**
Run the full `make test-unit` and `make check` suite to confirm no new regressions beyond the documented pre-existing failures, then open the PR against `ascherj/pathreview` following the `CONTRIBUTING.md` template.

**Blockers:**
One open judgment call, carried from Week 8: whether the `street_address` false-positive bug (`test_mixed_pii_and_text`) needs its own filed issue. Also had to skip the `mypy` pre-commit hook (`SKIP=mypy`) for the test-file commit since all 409 test functions repo-wide lack return-type annotations (a pre-existing repo-wide gap that `make check`'s `typecheck` target already excludes via not passing `tests/` to mypy), so this isn't something introduced by this change. I'm documenting it here and will note it in the PR description too.