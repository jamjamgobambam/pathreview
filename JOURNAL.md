# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/37  
**Issue title:** Add snapshot tests for prompt templates to catch accidental changes  
**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3  

**Problem summary:** PathReview's prompt templates directly shape the feedback produced by the review pipeline, but the existing test only checks that a generated MD5 value has the right type and length. That assertion still passes when template wording changes, so accidental edits can silently alter review behavior without requiring a new template version. The work is localized to `tests/unit/test_prompt_templates.py` and the versioned templates in `rag/generator/prompt_templates.py`. A successful change will store deterministic expectations for each named template version and fail when an existing version's content changes, making intentional prompt changes require an explicit version bump and reviewed snapshot update.

**Branch name:** `test/37-prompt-template-snapshots`  
**Setup confirmation:** [x] App runs locally at localhost:5173  
**Cohort ledger:** [x] Issue added to cohort ledger (Section 1B, row 33)

### "Is this right for me?" selection notes

#### Part 1 — Understanding the issue

- [x] I can explain the problem and expected behavior: the current hash test does not compare against a saved value, so it cannot detect prompt changes; version-keyed snapshots should make same-version edits fail.
- [x] I located the affected files: `tests/unit/test_prompt_templates.py` contains the ineffective snapshot assertion, and `rag/generator/prompt_templates.py` contains the versioned prompt strings.
- [x] I understand what done looks like: tests pass for the current templates, fail if any existing version is edited, and make an intentional prompt change visible as a new version and snapshot.

#### Part 2 — Tier fit

- [x] Issue #37 is labeled Tier 1 and is a realistic fit because the change is self-contained in the prompt-template unit tests, with at most a small supporting snapshot fixture.
- [x] The task does not require a cross-module feature, database change, API change, or redesign of the RAG pipeline.

#### Part 3 — Codebase readiness

- [x] I read the relevant implementation, including the nested `PROMPT_TEMPLATES` name/version mapping and `get_template()` lookup behavior.
- [x] I read `tests/unit/test_prompt_templates.py` end-to-end and confirmed the current `test_template_snapshot_content_hash` assertion cannot catch content changes.
- [x] My implementation plan is to create deterministic, version-keyed snapshots, compare the current template/version inventory and content against those snapshots, and add a regression test that demonstrates a same-version mutation is rejected.

#### Part 4 — Scope and time

- [x] I reviewed the issue comments and understand that claims are non-exclusive; multiple students may work on the same issue.
- [x] The issue estimate is 3–5 hours, which is realistic within the Week 8–9 implementation window.
- [x] The issue lists no blockers or dependencies on unresolved work.

**Verdict:** Issue #37 is well understood, appropriately scoped, and ready for implementation on this branch.
