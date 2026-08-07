## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The PII scrubber's phone number detection, located in pii_scrubber.py, uses a
regex pattern that only matches dashed phone formats like 555-123-4567. It
does not account for the parenthesized format (555) 123-4567, which is one
of the most common ways US phone numbers are written. As a result, scrub()
lets these numbers pass through unredacted and detect() fails to flag them
as PII at all. A successful fix will update the phone-matching pattern to
also catch parenthesized formats, closing this gap in the safety layer, and
get the related unit tests passing (test_us_phone_number_redaction,
test_us_phone_formats, test_detect_phone_pii, test_phone_at_start_of_text).

**Branch name:** fix/146-pii-scrubber-parenthesized-phone

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 reproduction notes

Ran python -m pytest tests/unit/test_pii_scrubber.py -v on branch fix/146-pii-scrubber-parenthesized-phone. Confirmed issue #146: 5 tests fail, all related to parenthesized phone format (555) 123-4567 not being detected or redacted by PIIScrubber.detect()/scrub(). Dashed and dotted formats pass; parenthesized format returns 0 detections.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/grcyaa0-eng/pathreview/commit/e74d09925d39898676ee941823aa7fbff5f6c42d

**Reproduction summary:**
Ran the existing test suite for the PII scrubber and confirmed 5 tests fail,
all related to the parenthesized US phone format (555) 123-4567 not being
detected or redacted. Traced the cause to the phone_us regex in
pii_scrubber.py, which only allows a hyphen or period as a separator after
the closing parenthesis, not a space.

**PLAN.md link:** https://github.com/grcyaa0-eng/pathreview/blob/fix/146-pii-scrubber-parenthesized-phone/PLAN.md

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
Noticed a separate, likely unrelated bug in test_mixed_pii_and_text where
part of the word "Python" gets redacted along with nearby PII. Flagged it
in PLAN.md as a risk to watch for but it's not in scope for issue #146.

## Reproduction — Issue #146

Ran `python -m pytest tests/unit/test_pii_scrubber.py -v` on branch `fix/146-pii-scrubber-parenthesized-phone`.

**Result:** 5 failed, 20 passed.

**Failures directly related to Issue #146 (parenthesized phone numbers not detected):**
- `test_us_phone_number_redaction` — `(555) 123-4567` not redacted
- `test_us_phone_formats` — parenthesized format `(555) 123-4567` not redacted (other formats pass)
- `test_detect_phone_pii` — `detect()` returns 0 phone matches for `(555) 123-4567`
- `test_phone_at_start_of_text` — `(555) 123-4567` at start of string not redacted

**Root cause:** In `safety/pii_scrubber.py`, the `phone_us` regex (line 15) opens with `\b(?:\+?1[-.]?)?\(?`. Since `\b` requires a word-boundary transition and `(` is a non-word character, `\b` fails to match immediately before a literal `(`. Additionally, `[-.]?` after the closing `)?` does not account for a space, which is the standard separator in `(555) 123-4567`.

**Unrelated pre-existing failure (not in scope for #146):**
- `test_mixed_pii_and_text` fails because the `street_address` pattern's `Pl` (Place) alternative case-insensitively matches inside "a**pl**ications", greedily consuming text back to a preceding digit. This is a separate bug in the `street_address` pattern, not the phone regex, and is not part of Issue #146. Documenting here per pre-existing-failure policy; will note in PR description that this fix does not affect it.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix for Issue #146: updated the `phone_us` regex in `safety/pii_scrubber.py` (line 15) to accept whitespace as a separator after the closing parenthesis, in addition to hyphen and period. Ran the existing test suite and confirmed the four previously-failing phone tests now pass (`test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`, `test_phone_at_start_of_text`). Ran `mypy`, `ruff check`, and `black --check` on the modified file; `mypy` passes clean, and the `ruff`/`black` findings are all on pre-existing lines unrelated to this change. Opened draft PR #827 on ascherj/pathreview.

**Next steps:**
Request peer or mentor feedback on the draft PR in Slack. Address any feedback received, then mark the PR ready for review, add Check-in 2 with the final PR link, and submit the branch URL via the course portal.

**Blockers:**
None currently.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/827

**Branch:** fix/146-pii-scrubber-parenthesized-phone

**What you built:**
Fixed the `phone_us` regex in `safety/pii_scrubber.py` to accept whitespace as a separator after the closing parenthesis, in addition to hyphen and period, so parenthesized US phone numbers like "(555) 123-4567" are now correctly detected and redacted.

**Tests added or updated:**
No new test files added; the existing tests in `tests/unit/test_pii_scrubber.py` already covered this case (`test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`, `test_phone_at_start_of_text`) and now pass with the fix.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Note: `mypy` passes clean; `ruff`/`black` flag pre-existing style issues on unmodified lines, documented in PR description. No new failures introduced by this change; one pre-existing unrelated failure, `test_mixed_pii_and_text`, documented in PR description.)

**Draft PR feedback received from:** none — requested in Slack, no response received by submission deadline

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in during the module. (Per the Su26 course note, reviewer feedback isn't a feature this term, so this is expected rather than a sign the PR was overlooked.)

**How you responded:**
N/A — no changes were needed since no feedback arrived.

---

### Reflection

**What was harder than you expected?**
Getting my local environment working was the biggest obstacle, not the actual bug fix. Working in Git Bash on Windows without `make` or Docker meant I had to manually replicate what the project's tooling would normally automate, running `ruff`, `black`, and `mypy` by hand instead of a single command. The regex fix itself for parenthesized US phone numbers was the easy part once I'd reproduced the bug with pytest.

**What did you learn about working in a large codebase?**
Reproducing the bug first, before touching any code, made the actual fix almost trivial by comparison. Writing PLAN.md before implementing forced me to think through edge cases (like parenthesized area codes) that I might have missed if I'd jumped straight to editing the regex. I also learned how much of "contributing" is process — journaling, planning, documenting — rather than just writing code.

**How did AI tools help — and where did they fall short?**
AI was most useful for explaining unfamiliar regex patterns and helping me think through test cases for the PII scrubber. It fell short when it came to environment-specific issues, like Windows file save quirks in my editor; I ended up relying on heredoc/`printf` commands in the terminal since AI suggestions assumed a Mac/Linux setup with tools I didn't have.

**What would you do differently if you started over?**
I'd set up my environment checks (confirming `make`, Docker, and other tooling availability) before selecting an issue, so I could plan around those constraints from the start instead of discovering them mid-task.

**What are you most proud of from this module?**
Getting the full PR — regex fix, reproduction notes, PLAN.md, and journal entries — submitted and passing lint/format/typecheck manually, without any of the automation the project assumes you have.
