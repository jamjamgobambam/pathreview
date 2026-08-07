## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1

**Problem summary:**
The safety layer’s phone-number pattern in `safety/pii_scrubber.py` redacts dashed US phone formats, but the parenthesized format `(555) 123-4567` slips through both `scrub()` and `detect()`. That means a common phone-number form can remain visible in user-facing output and escape PII detection entirely. A correct fix should expand the phone regex so the parenthesized format is matched and redacted consistently without breaking the existing phone redaction cases.

**Branch name:** fix/146-parenthesized-us-phone-numbers

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Selection notes:**
I can explain the issue in my own words without rereading the tracker: the scrubber misses a very common US phone format, so one PII path is inconsistent between detection and redaction. The relevant code is localized to `safety/pii_scrubber.py`, and the existing tests in `tests/unit/test_pii_scrubber.py` already cover the affected behavior, so this is a realistic Tier 1 fix. I also confirmed there are no blockers or dependencies listed on the issue.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [docs: add week 8 reproduction and plan](https://github.com/rafayet-git/pathreview/commit/2ae2318fb2fde17045085ff51d23cd4220f40327)

**Reproduction summary:**
I ran `pytest tests/unit/test_pii_scrubber.py -q` and confirmed that `(555) 123-4567` is not redacted by `scrub()` and is not detected by `detect()`. The focused test run failed in the expected phone-number cases, which shows the bug is real and isolated to the phone regex in `safety/pii_scrubber.py`.

**PLAN.md link:** [PLAN.md](PLAN.md)

**Blockers or open questions:** Wondering if other formats can/should also be redacted by these functions. 

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the regex fix in `safety/pii_scrubber.py` so parenthesized US phone numbers are now redacted and detected, and I added a regression assertion in `tests/unit/test_pii_scrubber.py` to lock that behavior in. I also ran the focused pii scrubber tests to confirm the phone-related cases pass; the only remaining `make check` failures are unrelated pre-existing issues elsewhere in the repo.

**Next steps:**
I’m ready to open the PR, gather any review feedback, and update the journal with the final PR link once it is submitted.

**Blockers:** None

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/394

**Branch:** fix/146-parenthesized-us-phone-numbers

**What you built:**
I updated the US phone-number regex in `safety/pii_scrubber.py` so parenthesized numbers like `(555) 123-4567` are now detected and redacted consistently. I kept the change scoped to the phone pattern and added a regression assertion in `tests/unit/test_pii_scrubber.py` to make sure the parenthesized format stays covered.

**Tests added or updated:**
I updated `tests/unit/test_pii_scrubber.py` to assert that the parenthesized phone format is detected exactly, and I verified the affected phone-related tests with the focused pii scrubber test slice. The broader repo still has unrelated pre-existing lint and typecheck issues outside the files I touched.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes (test cases related to the issue all pass, but pre-existing issues remain.)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — no review came in by submission time

**Summary of feedback:**
No reviewer or maintainer feedback arrived before the deadline.

**How you responded:**
I did not need to make follow-up changes or post a response because there was no review feedback to address.

---

### Reflection

**What was harder than you expected?**
The hardest part was separating the real bug from unrelated noise in the repo. The PII fix itself was small, but validation turned up pre-existing failures in lint, typecheck, and one mixed-content unit test that were unrelated to the phone regex. That made it important to document exactly which failures were baseline issues and which ones are the actual issues I needed to address.

**What did you learn about working in a large codebase?**
I learned that in a larger codebase, scope control matters as much as the code change itself. Even a targeted regex fix needs context from the surrounding tests, project setup, and contribution workflow, and you have to prove the issue with a focused reproduction before changing anything. I also had to be careful not to “fix” unrelated problems just because they were visible during testing.

**How did AI tools help — and where did they fall short?**
AI tools were most useful for quickly locating the relevant files, summarizing the issue, and drafting the journal/plan structure. They were less useful for judging whether a failure was actually related to my issue, because that required reading the tests, running focused commands, and comparing the output against the specific regex change. I still had to validate the behavior myself instead of trusting the first plausible explanation.

**What would you do differently if you started over?**
I would spend less time on broad checks early and go straight to the narrow failing test that matched the issue. I’d also record the exact reproduction and validation commands in my notes sooner, because that made it much easier to explain the fix later and to separate issue-related failures from repo-wide baseline issues.

**What are you most proud of from this module?**
I’m most proud that I kept the fix small, test-backed, and easy to review. The regex change solved the reported bug without widening the scope of the safety layer, and the journal now shows a complete paper trail from issue selection through reproduction, planning, implementation, and reflection.
