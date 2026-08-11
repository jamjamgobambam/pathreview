# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/111

**Issue title:** No property-based tests for the PII scrubber

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The PII scrubber supports five categories of personal information, but its unit tests used only a
small number of hard-coded examples. Issue #111 asks for Hypothesis strategies that generate
randomized supported PII and verify that the scrubber reliably removes it. A successful solution
adds meaningful randomized coverage without duplicating implementation regexes or changing the
production scrubbing API.

**Branch name:** `test/111-pii-scrubber-property-tests`

**Setup confirmation:** [x] Python test environment is available and focused unit tests run locally

**Cohort ledger:** [ ] Issue added to cohort ledger

### “Is this right for me?” checklist reasoning

- The issue is labeled Tier 2 and has an estimated effort of 4–6 hours.
- The requested change is focused on one existing unit-test file.
- The current scrubber implementation and example tests clearly identify the behavior to test.
- Hypothesis is already available in the development dependency group.
- The change can be verified locally without network access or running the application stack.
- The main risk is accidentally generating unsupported formats or writing generators that simply
  reproduce the implementation regexes.

### Setup notes

- Used the existing fork with `origin` pointing to `menukaghalan/pathreview` and `upstream`
  pointing to `ascherj/pathreview`.
- Created `test/111-pii-scrubber-property-tests` from the upstream `main` branch.
- Repaired stale Windows virtual-environment launchers so pytest and pre-commit could run locally.
- Verified that Hypothesis was already declared in `pyproject.toml`.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** No separate reproduction commit was created. The missing Hypothesis
coverage was confirmed by inspecting the original `tests/unit/test_pii_scrubber.py`; the completed
test implementation is commit
https://github.com/menukaghalan/pathreview/commit/3a51568d63684b8a4c14ca6f3d9a6da6fcf48460.

**Reproduction summary:**
I inspected `tests/unit/test_pii_scrubber.py` and confirmed that it contained example-based tests but
no Hypothesis imports, strategies, or `@given` tests. I then inspected `safety/pii_scrubber.py` and
identified five supported categories: email, US phone, international phone, SSN, and street address.

**PLAN.md link:**
https://github.com/menukaghalan/pathreview/blob/test/111-pii-scrubber-property-tests/PLAN.md

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**
The repository already had failing PII scrubber examples and existing lint/type-check findings.
These were documented separately so the test-only change would not expand into production regex
work.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I inspected the implementation, existing tests, testing configuration, and development dependencies.
I defined independent bounded strategies for all five supported PII categories and added primary
redaction properties.

**Next steps:**
Run Hypothesis, inspect minimized failures, tighten any generator assumptions, add secondary
idempotence and robustness properties, and prepare a draft pull request.

**Blockers:**
The Windows virtual environment contained stale executable launchers, and the repository had
pre-existing PII test, Ruff, and mypy failures.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/843

**Branch:** `test/111-pii-scrubber-property-tests`

**What you built:**
I added bounded Hypothesis strategies and property-based tests for every PII category currently
supported by the scrubber. The properties verify complete redaction, preservation of safe context,
idempotence, and robustness against bounded arbitrary Unicode input.

**Tests added or updated:**
Updated `tests/unit/test_pii_scrubber.py` with seven property-based tests covering emails, US and
international phone numbers, SSNs, street addresses, idempotence, and arbitrary-text robustness.
The focused run completed with 7 passed and 25 deselected.

**Self-review confirmation:** [ ] `make check` passes  [ ] `make test-unit` passes

The new focused tests pass, Black passes, and `git diff --check` passes. The boxes remain unchecked
because repository-wide checks have documented pre-existing failures: five existing PII examples
fail against current production regex behavior, Ruff reports two existing unused assignments in the
test file, and pre-commit mypy reports missing annotations throughout the existing test file.

**Draft PR feedback received from:** none — still awaiting review

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**

No reviewer feedback has been received. The Summer 2026 course instructions note that reviewer feedback is not provided this term, and pull request #843 currently has no review submissions or review comments.

**How you responded:**

Because no reviewer feedback was available, no reviewer-directed changes were necessary. I used the week to complete a detailed self-review, rerun the focused property-based tests, review the final diff, and document the repository's pre-existing test, lint, and type-check failures in the pull request.

---

### Reflection

**What was harder than you expected?**

The hardest part was separating problems introduced by my work from problems that already existed in the repository. The focused property tests passed, but the complete PII scrubber test file contained failures caused by existing phone-number and street-address regex behavior. The quality checks also reported existing lint and type-annotation problems in the test file. Understanding which failures actually belonged to issue #111 required inspecting the implementation, reviewing the full diff, and running progressively narrower checks.

Hypothesis also exposed a subtle testing problem: simply checking that the original PII value disappeared was not strong enough, because a partial redaction could satisfy that assertion without fully removing the sensitive value.

**What did you learn about working in a large codebase?**

I learned that contributing to an existing codebase requires understanding its current contract and baseline before making changes. A test should verify behavior the application actually claims to support rather than silently expanding that behavior.

I also learned the importance of preserving unrelated work, following repository conventions, checking whether failures reproduce before my changes, and keeping a pull request focused even when nearby defects are discovered. In my own project I could immediately change both the tests and implementation, but in a shared production codebase those changes may belong to separate issues and need to be justified independently.

**How did AI tools help — and where did they fall short?**

AI tools helped me explore the repository, locate the PII implementation, understand its regular expressions, design Hypothesis strategies, review the diff, and interpret minimized failing examples. They were especially useful for identifying partial-redaction cases that simple example-based tests could miss and for quickly comparing generated inputs with the scrubber's supported behavior.

AI assistance fell short when it initially suggested repository-wide commands without accounting for my Windows environment and the repository's stale virtual-environment launchers. It also could not replace the judgment needed to distinguish a genuine scrubber defect from an invalid generator assumption or decide whether a discovered problem belonged in this pull request. I still needed to inspect the actual output, verify commands locally, compare against the baseline, and make the final scope decisions myself.

**What would you do differently if you started over?**

I would first create the correct issue branch from the latest `main`, then run and save the baseline focused tests, relevant unit tests, lint checks, and type checks before editing. I would also verify the local development tools and virtual environment before reaching the commit stage.

During implementation, I would begin with strict properties that verify the complete scrubbed output rather than only checking that the original PII value disappeared. That would make it easier to identify partial-redaction behavior earlier and distinguish implementation limitations from generator mistakes.

**What are you most proud of from this module?**

I am most proud of creating property-based strategies that are independent from the production regular expressions. Instead of copying the implementation with `st.from_regex()`, the tests construct realistic emails, phone numbers, Social Security numbers, and street addresses from meaningful components.

This makes the tests more valuable for detecting future regressions rather than simply reproducing the implementation's assumptions, and it helped expose subtle partial-redaction behavior that fixed examples could easily miss.
