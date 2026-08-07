## Week 7 — Issue selection

**Student:** Ruikang Wang
**GitHub username:** Thankyou-Cheems
**Section:** 2a

**Issue link:** https://github.com/ascherj/pathreview/issues/111

**Issue title:** No property-based tests for the PII scrubber

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**

Issue #111 concerns the test coverage of PathReview's PII scrubber in the safety layer. The existing unit suite checks a fixed set of email, phone-number, SSN, and street-address examples, but it does not exercise randomized inputs. Format variations could therefore pass the fixed examples while escaping coverage from the test suite. The planned follow-up is to add Hypothesis-based property tests that generate supported PII patterns and verify that the scrubbed output does not retain the generated values; that implementation work is intentionally left for the later module weeks.

**Branch name:** `test/111-pii-scrubber-hypothesis`

**Setup confirmation:** [ ] App runs locally at `localhost:5173` (not yet; Docker Desktop's Linux engine did not start)

**Setup attempt:** The initial `make setup` steps completed the virtual environment, project/development dependency installation (including Hypothesis), and pre-commit hook installation. The command then stopped at `alembic upgrade head` because PostgreSQL at `localhost:5433` refused the connection while Docker Desktop's engine was unavailable. I am not claiming an app URL or a running environment without that verification.

**Cohort ledger:** [x] Issue added to cohort ledger — Section 2a, Issue #111

### Selection notes

- **Scope:** This is a focused tests/enhancement task. The Week 7 scope is issue selection, environment setup, and a journal entry; it does not change the scrubber implementation or add the property tests yet.
- **Current behavior:** `PIIScrubber.scrub()` applies the regexes in `PIIScrubber.PII_PATTERNS`, and the current unit tests use hand-written examples. The missing coverage is randomized/property-based testing across supported PII formats.
- **Relevant code:** `safety/pii_scrubber.py` contains the scrubber and pattern definitions; `tests/unit/test_pii_scrubber.py` contains the existing unit coverage; `pyproject.toml` already declares the Hypothesis development dependency.
- **Tier reasoning:** The issue is labeled Tier 2, `enhancement`, and `tests`. It requires understanding the safety implementation and designing safe Hypothesis strategies, but the expected change is localized to the test layer.
- **Success criteria:** In the later implementation weeks, add deterministic/reproducible Hypothesis properties for the supported PII types, assert that generated values are removed or masked, and keep the existing PII scrubber unit tests passing.

### Week 7 status

- GitHub claim comment: https://github.com/ascherj/pathreview/issues/111#issuecomment-4998092019
- The issue had earlier public interest comments; the formal course-ledger entry for Section 2a is the basis for this assignment claim.
- No implementation or pull request has been completed in Week 7; those are intentionally deferred to the later module weeks.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Thankyou-Cheems/pathreview/commit/d9aeb8a9bb514613c1bb9e5e6a2f50f3c046cdf8

**Reproduction summary:** From the Week 7 branch, `pytest --collect-only -q tests/unit/test_pii_scrubber.py` collected 25 tests, all named fixed-example tests in `tests/unit/test_pii_scrubber.py`; searching that file for `hypothesis`, `@given`, `strateg`, or `property` returned no matches. This reproduces the Issue #111 gap: the scrubber has deterministic examples but no property-based coverage for randomized supported PII formats.

**Baseline test result:** Running `pytest -q tests/unit/test_pii_scrubber.py` produced `20 passed, 5 failed`; the failures are existing phone/address matching expectations and are recorded as a separate baseline blocker rather than changed in Week 8.

**PLAN.md link:** https://github.com/Thankyou-Cheems/pathreview/blob/test/111-pii-scrubber-hypothesis/PLAN.md

**Walkthrough video (recommended):** Not recorded; this is optional and not graded.

**Blockers or open questions:** Docker Desktop/PostgreSQL remains unavailable for the full application environment. The later property-test implementation must decide how to handle regex overlap, especially street-address matches in ordinary prose and the overlap between US and international phone patterns. No production implementation or pull request is included in Week 8.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:** Implemented the first vertical slice for Issue #111. Added bounded Hypothesis strategies and properties for email, US/international phone, SSN, and street-address values; strengthened fixed address and non-PII assertions; and corrected existing phone/address regex boundary issues exposed by the examples. The focused PII suite now passes all 28 tests.

**Next steps:** Run the repository quality checks, self-review the diff, open a ready-for-review PR, and record the final submission state.

**Blockers:** The repository has pre-existing failures outside the PII scrubber: full unit tests report 48 unrelated failures, while full-repository Ruff and mypy checks also report unrelated baseline errors. The focused PII tests, touched-file checks, and commit hooks pass.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/750

**Branch:** `test/111-pii-scrubber-hypothesis`

**What you built:** Added bounded Hypothesis properties that verify generated supported PII is redacted, detected with accurate source spans, and idempotent on repeated scrubbing. Also fixed phone-format boundaries and street-address suffix boundaries so the existing fixed tests and generated examples agree with the privacy contract.

**Tests added or updated:** `tests/unit/test_pii_scrubber.py` — three Hypothesis properties plus stronger address and non-PII assertions; focused result: `28 passed`. The touched-file Ruff, Black, and mypy checks and the commit hooks all pass.

**Self-review confirmation:** [ ] `make check` passes (blocked by pre-existing full-repository Ruff/type errors) [ ] `make test-unit` passes (blocked by 48 pre-existing failures outside `safety/pii_scrubber.py`)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — reviewer feedback is not provided for Summer 2026.

**Summary of feedback:** PR #750 is open and currently has no reviewer comments or review submissions. The Week 10 course page also notes that reviewer feedback is not a Summer 2026 feature.

**How you responded:** No reviewer response or follow-up code change was needed. I kept the PR open and documented the current state instead of implying that the PR had been reviewed or merged.

---

### Reflection

**What was harder than you expected?**

At first, Issue #111 looked like a small testing task: add property-based tests for the PII scrubber. The harder part was discovering that some existing phone and street-address examples already exposed matching problems. I had to decide which small implementation fixes were necessary for the issue and where to stop so that I did not turn a Tier 2 test task into a broad rewrite. It was also harder than expected to separate failures caused by the existing repository from failures caused by my changes.

**What did you learn about working in a large codebase?**

I learned that the issue description is only the starting point. I needed to read the existing tests, the implementation, the project configuration, the contribution guide, and the course requirements before choosing a change. In someone else's codebase, a small diff with focused evidence is usually safer than fixing every problem that appears during a full-repository run. The existing failures, unavailable Docker/PostgreSQL environment, and strict pre-commit checks all made that boundary visible.

**How did AI tools help — and where did they fall short?**

I mainly used AI tools to look up the relevant project materials and milestone requirements, locate the right files and test seams, and help explore possible Hypothesis strategies. They also helped me organize the testing and submission checklist. They could not decide whether the scrubber's regex behavior matched the project's actual contract, whether an unrelated full-suite failure was in scope, or whether a timed-out browser action had succeeded. I had to inspect the failing examples, review the diff, run the tests, and verify the final GitHub and course-portal state myself.

**What would you do differently if you started over?**

I would run the baseline focused tests, the full unit command, and the repository checks earlier, before writing the property tests. I would also write down the supported phone and address formats and their boundary cases before changing the regexes. Finally, I would open the PR earlier and keep a shorter running record of decisions, so the final journal entry would require less reconstruction.

**What are you most proud of from this module?**

I am most proud that the property tests did more than increase a coverage number: they exposed real phone and address matching issues and helped turn the scrubber behavior into clearer, repeatable checks. I kept the change focused, documented the unrelated repository failures honestly, created a ready-for-review PR, and completed the branch submission without claiming that the PR had been merged or reviewed.
