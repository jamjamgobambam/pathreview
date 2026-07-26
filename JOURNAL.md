## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/37

**Issue title:** Add snapshot tests for prompt templates to catch accidental changes

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `rag/generator/prompt_templates.py` module holds versioned prompt templates used by the review generator, but nothing currently enforces that changes to a template are accompanied by a version bump. A developer can silently edit the text of `v1` (or any existing version) and the app will keep running, quietly shipping different LLM behavior. The existing `tests/unit/test_prompt_templates.py` has a placeholder "snapshot" test that only checks the length of a hash string, so it does not actually catch content changes. A successful fix adds real per-template hash snapshots so that any modification to an existing version fails the test suite, forcing developers to add a new version (e.g., `v2`) instead of silently mutating `v1`.

**Branch name:** feat/37-prompt-template-snapshots

**"Is this right for me?" reasoning:**
Scope matches the Tier 1 estimate (3–5 hours) — I finished in ~4 hours.
Skills align well: I already work with LLM prompt templates and
evaluation in my own research, so understanding what "silent template
drift" means and why version pinning matters was intuitive. No new
libraries needed — the fix uses stdlib `hashlib` and existing `pytest`,
so I didn't need to learn a snapshot testing framework from scratch.
The blast radius is contained to one test file, which makes it low-risk
for a first contribution.

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger