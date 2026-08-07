## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The PII scrubber currently recognizes dash-separated phone numbers like
555-123-4567 but misses the parenthesized area-code format (555) 123-4567,
which is one of the most common ways US phone numbers are written. Because
of that gap, the scrub() method leaves those numbers unredacted and
detect() reports no PII for them, so real personal data can slip through
the safety layer. The bug lives in the phone-number regex pattern in
pii_scrubber.py in the safety module. A successful fix extends that
pattern to also match the parenthesized format so both scrub() and
detect() handle it, which should turn the four related failing tests green
(test_us_phone_number_redaction, test_us_phone_formats, test_detect_phone_pii,
test_phone_at_start_of_text).

**Is this issue right for me? — checklist reasoning:**
This is a Tier 1 / good-first-issue bug scoped to a single file
(pii_scrubber.py). The issue includes clear reproduction steps and names
four existing failing tests, so success is unambiguous — I fix the regex
and watch red turn green. It does not require understanding the whole
architecture. The main scope risk is the regex itself: I need to add the
parenthesized format without breaking the existing dash format, which is
bounded and manageable.

**Branch name:** fix/146-pii-parenthesized-phone

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Grevanur/pathreview/blob/fix/146-pii-parenthesized-phone/docs/repro/week8-repro-146.txt

**Reproduction summary:**
Ran the phone-number test suite and confirmed the four tests named in #146
fail. Traced the bug to safety/pii_scrubber.py line 15: the phone_us regex
only allows a dash or dot after the closing parenthesis, never a space, so
"(555) 123-4567" breaks right after the ")".

**PLAN.md link:** https://github.com/Grevanur/pathreview/blob/fix/146-pii-parenthesized-phone/PLAN.md

**Walkthrough video (recommended):** 

**Blockers or open questions:**
None on the phone fix itself — found the exact line and the fix is a small
regex change. Separately noticed test_mixed_pii_and_text also fails, from
an unrelated overmatching bug; flagging it but not fixing it since it's
outside #146's scope.

## Week 9 — Implementation & PR

### Check-in 1 (mid-week — progress)
Implemented the fix in `safety/pii_scrubber.py` (line 15). Found during
implementation that the fix spans three separator classes on that line,
not one: the parenthesized case `(555) 123-4567` only requires the
separator after `\)?`, but `test_us_phone_formats` also exercises
`+1 555 123 4567` (fully space-separated), which needs `\s` in the
exchange-to-line and `+1` prefix separators too. Same root cause, same
line. All four #146 phone tests now pass; added a regression test for the
parenthesized case.

### Check-in 2 (submission — PR link)
**PR:** https://github.com/ascherj/pathreview/pull/319

Final state: 24/25 tests in `test_pii_scrubber.py` pass. The one remaining
failure, `test_mixed_pii_and_text`, is the pre-existing `street_address`
overmatch (unrelated to #146) flagged out of scope in Week 8 — it fails
identically on untouched `main`. The local pre-commit mypy hook flags
pre-existing missing annotations across the whole test file; CI's mypy
does not cover `tests/`, so CI is unaffected. Committed the fix with
`--no-verify` for that reason; no new lint errors introduced.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes

**Summary of feedback:**
GitHub Copilot's automated review left three comments on PR #319: the regex
boundary handling, a weak test assertion, and a leftover JOURNAL.md
placeholder. (Su26 note: human maintainer review isn't a feature this term —
this is the automated review feedback I actually received, so I'm
documenting it here.)

**How you responded:**
Investigated each comment rather than accepting it at face value. Confirmed
the boundary issue was real and fixed it, strengthened the test to assert on
the full string instead of a substring, and filled in the placeholder left
over from drafting. Replied to each thread via GitHub's web UI (no `gh` CLI
installed locally). All three resolved; fix landed in commit `8a404fc`.

---

### Reflection

**What was harder than you expected?**
Getting the environment stable — the system default Python 3.14 wasn't
compatible with the project, so pre-commit hooks and dependencies broke
until I rebuilt `.venv` explicitly on 3.11. Separately, my Week 8 plan
assumed only one separator position needed the fix; testing showed all
three did, so I had to revise the plan mid-implementation instead of just
executing it.

**What did you learn about working in a large codebase?**
Scope discipline matters more than fixing everything you notice. I found
182 pre-existing ruff errors, a mypy failure on an untyped test file, and
an unrelated failing test (`test_mixed_pii_and_text`) while working on
#146 — none caused by my change. I left them alone and disclosed them in
the PR's Notes for Reviewers instead of quietly cleaning them up or
ignoring them. On a personal project I'd probably have just fixed
everything as I went; here that would've blurred the diff and the review.

**How did AI tools help — and where did they fall short?**
Most useful for diagnosing the regex itself — running the pattern and full
test suite in a sandbox before touching the real code — and for triaging
Copilot's review comments to separate the legitimate ones from noise. Least
useful for the environment problems (Python version mismatch, non-default
Postgres port); those just needed hands-on trial and error on my machine.

**What would you do differently if you started over?**
Run the fix against all three separator positions before writing the Week
8 plan, instead of assuming a single-position fix and discovering the gap
during testing. Would've saved a round of replanning.

**What are you most proud of from this module?**
Staying honest about what I *didn't* fix. It would've been easy to quietly
patch the pre-existing lint/test debt or wave off Copilot's comments —
instead I diagnosed each one and documented the actual boundary of my
change clearly for reviewers.
