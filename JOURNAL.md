## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The PII scrubber's phone-number regex in `safety/pii_scrubber.py` matches
dashed formats like `555-123-4567` but misses parenthesized formats like
`(555) 123-4567`, because the pattern allows an optional closing paren but
no whitespace after it before the next digit group. As a result, `scrub()`
leaves parenthesized phone numbers in the output unredacted and `detect()`
fails to flag them as PII at all — a real privacy gap since parenthesized
format is one of the most common ways US phone numbers are written. A
correct fix updates the `phone_us` pattern to tolerate the space (or other
separator) after the area code parenthesis, and should be validated against
the existing `test_us_phone_number_redaction` test.

**Branch name:** fix/146-pii-scrubber-parenthesized-phone

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/bimalitani100/pathreview/commit/106cb12df5fcac6fe088e5a16514e3df1d177f95

**Reproduction summary:** Ran the scrub()/detect() snippets from issue #146 locally — confirmed `(555) 123-4567` passes through scrub() unredacted while `555-123-4567` in the same string is correctly redacted, and detect() returns [] for the parenthesized number. Confirmed via pytest that 4 of 6 phone-related tests fail (test_us_phone_number_redaction, test_us_phone_formats, test_detect_phone_pii, test_phone_at_start_of_text); the other 2 (international, phone-at-end) pass.

**PLAN.md link:** https://github.com/bimalitani100/pathreview/blob/fix/146-pii-scrubber-parenthesized-phone/PLAN.md

**Walkthrough video (recommended):** [optional]

**Blockers or open questions:**
Unclear whether "+1 555 123 4567" (space-separated international-style format) needs a separate fix beyond the parenthesis issue — will check when implementing next week.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix for issue #146: updated the `phone_us` regex in `safety/pii_scrubber.py` (changed leading `\b` to `(?<!\d)`, added whitespace to the separator classes). All 4 previously-failing phone tests now pass, plus a new test covering additional parenthesized-format edge cases. Ran `make check` and `make test-unit` — confirmed my change introduces no new failures; pre-existing failures exist in bias_detector, review_service, resume_parser, and other files I didn't touch, plus pre-existing lint/type errors unrelated to my change.

**Next steps:**
Finalize PR description documenting the pre-existing failures, open the PR for peer/mentor review.

**Blockers:**
None.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/872

**Branch:** fix/146-pii-scrubber-parenthesized-phone

**What you built:**
Fixed the phone_us regex in safety/pii_scrubber.py so parenthesized US phone numbers (e.g. (555) 123-4567) are correctly redacted and detected, matching the behavior already working for dashed formats.

**Tests added or updated:**
tests/unit/test_pii_scrubber.py — added test_parenthesized_phone_edge_cases covering no-space and dash-after-paren variants; confirmed the 4 previously-failing tests now pass.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(no new failures introduced — pre-existing failures documented in PR description)

**Draft PR feedback received from:** None

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback was provided — per the Summer 2026 course note, reviewer feedback is not a feature this term.

**How you responded:**
N/A — no feedback to respond to this term.

---

### Reflection

**What was harder than you expected?**
The actual regex fix was one line and took very little time. What was harder was everything around it: confirming that failing tests and lint errors were pre-existing rather than caused by my change (I had to stash my fix and re-run tests against the original code to prove it), and getting comfortable with pre-commit hooks — I once interrupted a slow mypy run mid-commit with Ctrl+C, which cancelled the commit entirely without me realizing it at first. None of that was code — it was process and verification, and it took more time than the fix itself.

**What did you learn about working in a large codebase?**
The codebase already had ~180 pre-existing lint errors and ~49 pre-existing failing tests across modules I never touched, spanning bias detection, review services, resume parsing, and more. Contributing to it meant learning to isolate my change's blast radius precisely — proving what my one-line edit did and didn't affect — rather than assuming a clean slate like a solo project. I also had to work through project-specific setup (activating a `.venv`, understanding `make check` and `make test-unit` targets) that a from-scratch project wouldn't require.

**How did AI tools help — and where did they fall short?**
AI was most useful for quickly diagnosing the two separate regex bugs stacked in one pattern (the `\b` boundary issue and the missing whitespace in separator classes) once I had the actual line of code and failing test output in front of it. It was also useful for explaining git/pre-commit behavior when I hit the interrupted-commit issue. Where it fell short: it couldn't fetch or read the actual source file from GitHub directly, so I had to run `grep` locally and paste the regex back for diagnosis — meaning I still needed to drive the terminal work myself throughout.

**What would you do differently if you started over?**
I'd activate the `.venv` and get oriented in the Makefile targets (`make check`, `make test-unit`) before writing any reproduction code, since I hit the same "wrong environment" error twice. I'd also run the full pre-existing test suite once, up front, right after cloning — so I'd have a baseline to compare against from day one instead of discovering pre-existing failures reactively while debugging my own change.

**What are you most proud of from this module?**
Verifying, rather than assuming, that my change didn't introduce regressions — actually stashing my fix and re-running tests against the original code to prove which failures were pre-existing before writing that into the PR description. That felt like the most "real engineering" part of the whole module.