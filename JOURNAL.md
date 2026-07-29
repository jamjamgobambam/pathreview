# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** README scorer test fixture is too short for its own word-count assertion

**Tier:** ☑ Tier 1  ☐ Tier 2  ☐ Tier 3

**Problem summary:**

The README scorer test expected the README fixture to be categorized as "comprehensive," but the fixture itself did not contain enough words to meet the scorer's threshold. As a result, the test failed even though the scorer's implementation was working correctly. The fix was to update the test fixture so that it satisfied the expected word count while preserving the existing README quality signals, allowing the test to accurately validate the scorer's behavior.

**Branch name:**

`fix/readme-scorer-fixture-156`

**Setup confirmation:**

☑ App runs locally at localhost:5173

**Cohort ledger:**

☐ Issue added to cohort ledger *(Update to ☑ after you add your entry.)*

---

### Selection notes ("Is this right for me?" checklist)

I selected this issue because it is a Tier 1 issue and focuses on understanding an existing test rather than implementing a new feature. I was able to reproduce the failure locally, identify the root cause by reading the test and the README scoring logic, and make a targeted change without modifying production code. The scope was well-defined and appropriate for my first open-source contribution to this project.

### Reproduction

Running:

python -m pytest tests/unit/test_readme_scorer.py -q

initially produced:

AssertionError:
expected "comprehensive"
received "adequate"

The README fixture contained only 251 words, while the scorer classifies
README files with more than 500 words as comprehensive.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:**

(To be added after committing.)

**Reproduction summary:**

I reproduced the issue by running the README scorer unit tests. The test
expected the README fixture to be categorized as "comprehensive," but it only
contained enough words to be classified as "adequate," causing the assertion
to fail.

**PLAN.md link:**

(To be added after pushing.)

**Walkthrough video (recommended):**

Not recorded.

**Blockers or open questions:**

None at this time.