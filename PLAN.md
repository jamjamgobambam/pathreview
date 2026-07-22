## Solution plan

**Issue:** Add snapshot tests for prompt templates to catch accidental changes — https://github.com/ascherj/pathreview/issues/37

### Understand
`tests/unit/test_prompt_templates.py::test_template_snapshot_content_hash` computes an MD5 hash of all concatenated template content but only asserts it's a 32-character string — it never compares against a fixed expected value. Expected behavior: editing any template's text under `PROMPT_TEMPLATES` without adding a new version key should cause a test failure. Actual behavior: the test passes regardless of content changes, confirmed via reproduction in Week 8.

### Map
- `rag/generator/prompt_templates.py` — source of truth, `PROMPT_TEMPLATES` dict (5 templates, each currently only `v1`) and `get_template()`.
- `tests/unit/test_prompt_templates.py` — will add/replace the snapshot test here (existing broken test at lines 175–188).

### Plan
1. Compute and hardcode the real expected MD5 hash for each of the 5 templates individually (per-template snapshot instead of one combined hash, so a failure points to exactly which template changed).
2. Replace `test_template_snapshot_content_hash` with a parametrized test (or 5 explicit tests) asserting each template's current hash equals its stored expected hash.
3. Add a clear failure message pointing to updating the hash *and* bumping the version key when a change is intentional.
4. Add a short comment/docstring in the test explaining the intended developer workflow (edit template → bump version → update snapshot).
5. Run `make check` (lint/format/type-check) and `make test-unit` to confirm nothing else breaks.

### Inputs & outputs
Input: the `PROMPT_TEMPLATES` dict content at test time. Output: pass/fail signal — test fails if any template's current hash doesn't match its recorded expected hash.

### Risks & unknowns
- Whole-file combined hash (current design) vs. per-template hashes — per-template is more diagnostic but is a bigger delta from the existing test; noting this as a design decision to explain in the PR description.
- Need to confirm hardcoded hashes are computed from the *current* template text, not accidentally computed after an unintended edit.
- Full `make test-unit` run has ~53 pre-existing unrelated failures in the sandbox (bias_detector, review_service, etc.) — need to scope verification to `test_prompt_templates.py` specifically so those don't create false signal.

### Edge cases
- A template gaining a new version (e.g. `v2` added) shouldn't break the `v1` snapshot.
- Empty or missing template version should still raise `ValueError` via `get_template()` — not something this test should affect, but worth confirming test additions don't accidentally change that behavior.