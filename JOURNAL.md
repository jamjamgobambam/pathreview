# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/37

**Issue title:** Add snapshot tests for prompt templates to catch accidental changes

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The RAG prompt generator (`rag/generator/prompt_templates.py`) stores five versioned templates used to generate portfolio feedback. `tests/unit/test_prompt_templates.py` already has a test named `test_template_snapshot_content_hash` that looks like a snapshot test, but it only checks that the computed MD5 hash is a 32-character string — it never compares it to a stored expected value, so it passes regardless of what the templates say. This means a developer can silently edit prompt wording (which directly changes review quality) with no automated signal, and no test enforces the intended practice of bumping the version key when content changes. A successful fix adds real per-template snapshot tests with fixed expected hashes (or literal expected strings) that fail loudly when template text changes, forcing a conscious version bump.

**Branch name:** test/37-prompt-template-snapshot-tests

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


**"Is this right for me?" checklist reasoning:**
- Understanding: I can explain the issue without re-reading it — `test_template_snapshot_content_hash` computes a hash but never asserts it against a fixed expected value, so it can't catch template edits. Relevant files confirmed: `rag/generator/prompt_templates.py`, `tests/unit/test_prompt_templates.py`.
- Done looks like: editing any template's text without bumping its version key causes a test to fail.
- Tier fit: Tier 1, appropriate as my first contribution to this codebase.
- Codebase readiness: read `get_template()` and the existing ~30 tests end-to-end; the module is self-contained (a dict + one accessor), so I can predict the blast radius of my change.
- Scope/time: checked the ledger claims count and issue comments — comfortable with how many others are on this issue. 3–5 hr estimate fits within Weeks 8–9. No blockers or dependencies listed on the issue.

All boxes checked — proceeding with this issue.