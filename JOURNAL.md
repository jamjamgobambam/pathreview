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