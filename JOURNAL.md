# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The safety layer's PII scrubber (`safety/pii_scrubber.py`) is supposed to catch
and redact personal information, including US phone numbers, before text is
stored or displayed. Its `phone_us` regex only allows `-` or `.` between the
number groups, so a common format like `(555) 123-4567` — where a space follows
the closing parenthesis — is never matched and passes through unredacted. This
is a real privacy leak, since a phone number a user expects to be hidden stays
visible. A successful fix updates the regex to also accept a space (and the
parenthesized area-code form) as a valid separator, adds a test covering that
format, and leaves the existing phone/email/SSN cases still passing.

**Branch name:** fix/146-parenthesized-phone-redaction

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/yenscastro/pathreview/commit/e901ce4

**Reproduction summary:**
I ran the phone tests in `tests/unit/test_pii_scrubber.py` and added a dedicated
failing test (`test_repro_issue_146_parenthesized_phone`). Running
`pytest tests/unit/test_pii_scrubber.py -k phone` shows 4 tests failing, and
`scrub("Call me at (555) 123-4567 or 555-123-4567")` returns
`"Call me at (555) 123-4567 or [REDACTED]"` — the dashed number is redacted but
the parenthesized `(555) 123-4567` leaks through, confirming the bug.

**PLAN.md link:** https://github.com/yenscastro/pathreview/blob/fix/146-parenthesized-phone-redaction/PLAN.md

**Walkthrough video (recommended):** [add Loom link here if you record one]

**Blockers or open questions:**
Main open question is how loose to make the regex without introducing false
positives (e.g. version numbers like `1.2.3` or spaced digit runs in prose). I
need to confirm the guard tests `test_text_with_no_pii` and
`test_detect_no_false_positives` still pass after widening the separator.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md. Widened the `phone_us` regex separator in
`safety/pii_scrubber.py` from `[-.]?` (dash/dot only) to `[-. ]?` (dash, dot, or
a single literal space). PLAN sub-tasks 1–4 are done: separator widened,
parenthesized branch re-checked, phone tests pass, and the guard tests
(`test_text_with_no_pii`, `test_detect_no_false_positives`) still pass — the
scrubber test file went from 6 failing to 1 failing, and that remaining failure
(`test_mixed_pii_and_text`) is a pre-existing, unrelated `street_address` bug
that also failed before my change.

**Next steps:**
Run `make check` and `make test-unit` in a full dev environment, open a draft PR
early for peer/mentor feedback, then fill in the PR template and mark it ready.

**Blockers:**
None on the fix itself. Still need to run the full `make check` / `make test-unit`
in a complete environment (my local venv only has the deps needed for the safety
module).

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/757

**Branch:** `fix/146-parenthesized-phone-redaction`

**What you built:**
Fixed a PII-redaction bug where the US phone-number regex only allowed dashes or
dots between number groups, so space-separated and parenthesized formats like
`(555) 123-4567` and `+1 555 123 4567` were never redacted. Widening the three
separators to also accept a single literal space fixes both `scrub()` and
`detect()`, since they share the same pattern.

**Tests added or updated:**
`tests/unit/test_pii_scrubber.py` — added `test_repro_issue_146_parenthesized_phone`
(Week 8) which now passes and acts as the regression test. The four existing
phone tests (`test_us_phone_number_redaction`, `test_us_phone_formats`,
`test_detect_phone_pii`, `test_phone_at_start_of_text`) now pass as well.

**Self-review confirmation:** [] make check passes  [] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
No formal review has come in yet. In my PR I left an open question for reviewers:
whether they prefer one broadened `phone_us` pattern or a separate explicit
pattern for the parenthesized form. (Update this section if a reviewer responds.)

**How you responded:**
N/A — no feedback to address yet. If a reviewer asks for changes, I'll note the
change and the commit that addressed it here.

---

### Reflection

**What was harder than you expected?**
The environment, not the code. The actual fix was a one-line regex change, but
getting to the point where I could run it took the most effort: a broken
virtualenv and pip, Docker not running, `make` expecting bash instead of
PowerShell, and even discovering I had two copies of the repo in different
folders. Untangling which test failures were mine versus already broken was also
harder than expected — the suite had 48 pre-existing failures from other issues.

**What did you learn about working in a large codebase?**
That you have to understand the blast radius of a change before you make it. I
confirmed the PII scrubber isn't even wired into the running app yet and that
nothing else imports it, so my one-line change couldn't break other modules —
that scoping gave me confidence. I also learned to respect the boundaries of my
issue: there was a second, unrelated bug (the `street_address` regex) right next
to mine, and the right move was to document it for reviewers, not "fix
everything." Matching the project's conventions — branch naming, Conventional
Commits, the PR template, Google-style docstrings — mattered as much as the code.

**How did AI tools help — and where did they fall short?**
AI tooling was most useful for navigating an unfamiliar codebase quickly:
locating where the regex lived, tracing who consumed it, reasoning about regex
behavior and edge cases, and drafting tests and the PR description. Where it fell
short: it couldn't stand in for actually running things in my environment — I had
to install dependencies, run the full test suite, and verify the results myself.
It also couldn't make judgment calls for me, like the eligibility/scope decisions
or choosing a literal space over `\s` to avoid matching across newlines. I treated
AI output as a draft to verify against the project's conventions, not as final.

**What would you do differently if you started over?**
Set the environment up and get it fully green *before* touching any code, and pick
a single folder for the repo so I'm never working out of the wrong copy. I'd also
open a draft PR earlier in the week to leave more room for peer feedback instead
of finishing most of the work first.

**What are you most proud of from this module?**
Keeping the fix minimal and honest. It would have been tempting to over-claim
"all tests pass" or to fix the adjacent bug too, but instead I scoped the change
tightly, wrote a regression test, and clearly documented the pre-existing failures
so a reviewer knows exactly what my change does and doesn't affect.
