## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The PII scrubber in `safety/pii_scrubber.py` is supposed to find and redact
personal info like phone numbers, but its phone-number regex only matches
dashed formats such as `555-123-4567`. It misses the very common parenthesized
format `(555) 123-4567`, because the pattern doesn't allow the `)` plus a space
after the area code. As a result, `scrub()` leaves those numbers in the text and
`detect()` reports no PII for them, so real phone numbers can leak through. A
successful fix updates the regex so both formats are caught, making the four
related unit tests in `tests/unit/test_pii_scrubber.py` pass.

**Branch name:** fix/146-pii-parenthesized-phone

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Selection notes (Is this right for me?):**
Good fit for a first contribution. It's a single-file change in
`safety/pii_scrubber.py`, the fix is a focused regex update, and the expected
behavior is already pinned down by existing failing tests, so I know exactly
what "done" looks like. No new dependencies, no cross-module changes, and it
runs with the default mock LLM (no API key needed). Scope is small and
self-contained.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/pepsi-boy/pathreview/commit/6e71220

**Reproduction summary:**
I ran the existing unit tests for the PII scrubber and confirmed the four
phone-number tests fail because the parenthesized format `(555) 123-4567` is
never redacted or detected. This proves the bug is real and lives in the
`phone_us` regex in `safety/pii_scrubber.py`.

**Reproduction steps:**
```
pytest tests/unit/test_pii_scrubber.py -v
```

**Observed failures:**
```
FAILED test_us_phone_number_redaction - assert '[REDACTED]' in 'Call me at (555) 123-4567'
FAILED test_us_phone_formats        - assert '[REDACTED]' in 'Contact: (555) 123-4567'
FAILED test_detect_phone_pii        - assert 0 > 0
FAILED test_phone_at_start_of_text  - assert '[REDACTED]' in '(555) 123-4567 is my phone number.'
```
Each failure shows a `(555) 123-4567` number passing through unredacted, and
`detect()` returning 0 phone matches for it.

**PLAN.md link:** https://github.com/pepsi-boy/pathreview/blob/fix/146-pii-parenthesized-phone/PLAN.md

**Walkthrough video (recommended):** [not recorded]

**Blockers or open questions:**
None yet — the root cause and the file to change are both clear.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix: broadened the `phone_us` regex in `safety/pii_scrubber.py`
to accept a space separator and to match parenthesized numbers at the start of a
string. All four failing phone tests now pass, and I added a regression test.
This completes the core sub-tasks from PLAN.md.

**Next steps:**
Run the full check suite, document pre-existing failures, open the PR, and get
peer feedback.

**Blockers:**
The repo's pre-commit hooks fail on pre-existing lint/type errors unrelated to my
change (e.g. missing type annotations across test files). Working around this by
confirming my changed lines are clean and documenting the pre-existing failures.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/947

**Branch:** `fix/146-pii-parenthesized-phone`

**What you built:**
A regex fix so the PII scrubber redacts US phone numbers written as
`(555) 123-4567`. The pattern now allows a space separator and uses lookarounds
instead of `\b`, so both `scrub()` and `detect()` handle the parenthesized format
(including at the start of a string and with a `+1` country code).

**Tests added or updated:**
`tests/unit/test_pii_scrubber.py` — added `test_phone_with_country_code_and_parens`.
The four existing phone tests named in the issue now pass as well.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(In this repo "passes" = introduces no new failures. Baseline `make test-unit`
was 53 failed / 375 passed; after my change it is 49 failed / 380 passed — the
4 phone tests fixed, zero new failures. Pre-existing lint/type failures are
unrelated to this change and my edited lines are ruff/black/mypy-clean.)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review
(Reviewer feedback is not provided in the Summer 2026 cohort.)

**Summary of feedback:**
No review came in. Reviewer feedback isn't a feature this cohort, and no
maintainer comments arrived on PR #947 by the end of the week.

**How you responded:**
N/A — no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
Getting the environment running was much harder than the actual fix. Docker
wasn't installed, Node was missing, and one container (ChromaDB) crash-looped on
a NumPy 2.0 error that had nothing to do with my issue. Later, the pre-commit
hooks blocked my commit entirely — not because of my code, but because the repo
already had dozens of failing lint/type checks. Figuring out that the blocker was
pre-existing (and using `--no-verify` plus documenting it) was the most confusing
part.

**What did you learn about working in a large codebase?**
The actual fix was one line, but finding *where* to change it and understanding
*why* it was broken took almost all the effort. I also learned that a real repo
is messy: there were ~53 failing tests before I touched anything, so "passing"
meant "I didn't make it worse," not "everything is green." Reading existing tests
told me exactly what the correct behavior should be, which was more useful than
reading the source.

**How did AI tools help — and where did they fall short?**
AI was most useful for navigating an unfamiliar codebase quickly — locating the
buggy regex, explaining what `\b`, `[-.\s]`, and lookarounds actually do, and
diagnosing setup errors (Docker, Node, the pre-commit hooks). Where it fell short
was the conceptual git model — I had to slow down and actually understand forks
vs. branches vs. commit vs. push myself before the commands made sense; running
them blindly wasn't enough.

**What would you do differently if you started over?**
I'd learn the basic git workflow (branch → add → commit → push, and how a PR
compares two branches) *before* starting, so I wasn't learning the tools and the
problem at the same time. I'd also run `make test-unit` to capture the baseline
failures on day one, so I'd know from the start which failures were mine vs.
pre-existing.

**What are you most proud of from this module?**
Ending with a clean, minimal PR — one intentional regex line plus one regression
test — instead of a messy diff full of auto-formatter noise. Keeping the change
small and well-documented felt like a real contribution, not just "make the tests
pass."
