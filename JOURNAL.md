# Module 3 Journal

## Week 7

- Issue selected: #111 — Add property-based tests for the PII scrubber
- Issue link: https://github.com/amulya-asu/pathreview/issues/111
- Tier: Tier 1
- Reason for selection: this issue is a small, focused privacy/test improvement that fits the repo scope and enables a concrete code/test fix without broad refactoring.
- Summary: I worked on improving the PII scrubber by tightening its phone and address detection logic and adding Hypothesis-based property tests to cover valid PII redaction behavior.
- Branch: `issue-111-pii-scrubber-tests`
- Validation: Ran `C:/Python313/python.exe -m pytest tests/unit/test_pii_scrubber.py -q` and got `27 passed`.
- Notes: The work focused on making the scrubber more reliable for common phone formats and on adding property-based coverage for non-PII preservation and PII redaction.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/amulya-asu/pathreview/commit/01501ab

**Reproduction summary:** Reproduced the issue by running the PII scrubber unit tests and observing that US phone and street address patterns were not being consistently redacted.

**PLAN.md link:** https://github.com/amulya-asu/pathreview/blob/issue-111-pii-scrubber-tests/PLAN.md

**Walkthrough video:** https://www.loom.com/share/f8fd846991ae41f8a55242c415eb5397

**Blockers or open questions:** None at the moment.

## Week 9

- Branch: `issue-111-pii-scrubber-tests`
- Repo/branch link: https://github.com/amulya-asu/pathreview/tree/issue-111-pii-scrubber-tests
- PR status: submitted and ready for review
- PR link: https://github.com/amulya-asu/pathreview/pull/1
- PR summary: Fix PII scrubber regexes, add Hypothesis property-based tests, and document the issue plan and journal entries.
- Tests run: `C:/Python313/python.exe -m pytest tests/unit/test_pii_scrubber.py -q`
- Additional validation: `make check && make test-unit`
- Self-review checklist:
  - [x] Branch name follows assignment convention
  - [x] Repository/branch link provided
  - [x] PR link added after opening PR
  - [x] Test command documented
  - [x] Journal and plan documents updated

## Week 10 — Iteration & reflection

- Submission branch: https://github.com/amulya-asu/pathreview/tree/issue-111-pii-scrubber-tests

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No external reviewer feedback has been received yet. I completed the issue work and made the branch available for review, but the course does not provide reviewer comments in Summer 2026.

**How you responded:**
No reviewer comments to respond to yet.

---

### Reflection

**What was harder than you expected?**
Working in an unfamiliar codebase made it harder to understand the existing PII detection patterns and regex behavior. I also underestimated the effort required to make Hypothesis property-based tests both precise and stable, especially when the generator needed to produce valid, redacted inputs.

**What did you learn about working in a large codebase?**
Contributing to someone else’s project requires extra care around conventions, branch naming, and documentation. I learned that small changes must be validated with tests and that reading docs like `CONTRIBUTING.md` and the repo structure is essential before editing.

**How did AI tools help — and where did they fall short?**
AI was useful for drafting the Loom script, suggesting regex improvements, and helping me write the journal entries. It fell short when I needed exact repo-specific behavior and environment debugging, so I had to verify every change manually and fix the property-based test logic myself.

**What would you do differently if you started over?**
I would begin by reproducing the issue and validating the test environment before making code changes. I would also open the PR earlier, so I could use reviewer feedback sooner rather than later.

**What are you most proud of from this module?**
I’m most proud of adding robust property-based coverage for the PII scrubber and making the branch ready for review with a complete journal, plan, and Loom walkthrough.
