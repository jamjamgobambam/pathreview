## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [`8fa4eee - docs(safety): add planning framework for fixing issue`](https://github.com/ru1nw/pathreview/commit/8fa4eee5f6b1579ffdc0055453c7c5cb49fe297a)

**Reproduction summary:**

I reproduced the issue using the unit test file, since the scrubber isn't
actually used in the project just yet.

Calling `pytest tests/unit/test_pii_scrubber.py` revealed that 4 of the test
cases related to scrubbing US phone numbers weren't passing, and the failing
formats all included the parenthesized format.

After using Claude Code to understand the issue more, the issue turned out to
be caused by the regex pattern not matching spaces in phone numbers, which the
parenthesized format used.

**PLAN.md link:** [`PLAN.md` in fork](https://github.com/ru1nw/pathreview/blob/fix/146-pii-not-scrub-phone/PLAN.md)

**Walkthrough video (recommended):** none

**Blockers or open questions:**

If there's more time, I might include more formats and test cases to cover more
bases.

---

## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/146](https://github.com/ascherj/pathreview/issues/146)

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers #146

**Tier:** [✓] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

The PII scrubber class in `safety/pii_scrubber.py` is not scrubbing phone
numbers when they are not in an expected format, namely when the area code is in
parentheses instead of followed by a hyphen. So `555-123-4567` is correctly
redacted, but `(555) 123-4567` is not. This issue might be caused by the regex
pattern `PIIScrubber.PII_PATTERNS["phone_us"]` not correctly matching
parentheses, causing the `PIIScrubber.scrub()` class method to fail. 4 related
unit tests in `test_pii_scrubber.py` fails.

**Branch name:** `fix/146-pii-not-scrub-phone`

**Setup confirmation:** [✓] App runs locally at `localhost:5173`

**Cohort ledger:** [✓] Issue added to cohort ledger

**Is This Issue Right for Me? checklist**

Part 1 — Understanding the Issue

- [x] I can explain the problem and the expected behavior in 2–3 sentences
without reading the issue.
- [x] I've located the relevant files and confirmed they exist in the codebase.
- [x] I can describe a concrete before-and-after: what the user sees before the
fix and what they see after.

Part 2 — Tier Fit

- [x] If this is my first open source contribution: I'm choosing Tier 1.
- [ ] If I've contributed to large codebases before: Tier 2 or 3 is fair game.
- [ ] I'm not choosing a Tier 3 issue to "challenge myself" if I haven't
completed a Tier 1 or 2 first — scope surprises in Week 9 don't have a safety
net.

Part 3 — Codebase Readiness

- [x] I've found and read the specific code the issue references (not just the
file — the function or section).
- [x] I've read enough surrounding context that I can write a rough plan for the
fix without looking anything up.
- [x] I've found the test file for my module and read at least one test
end-to-end.

Part 4 — Scope and Time

- [x] I've checked the issue comments and the ledger's Claims count, and I'm
fine with how many others are on this issue.
- [x] I've estimated the time this will take and I'm confident I can complete it
before the Week 9 deadline.
- [x] This issue has no open blockers or dependencies on other unresolved
issues.
