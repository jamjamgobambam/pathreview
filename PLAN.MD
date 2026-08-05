## Solution plan

**Issue:** #37 — Add snapshot tests that fail when a prompt template's content changes without a version bump (`tests/unit/test_prompt_templates.py`)

### Understand
Prompt templates directly affect review quality, so a silent edit to a template can degrade every review the app produces without anyone noticing. The issue asks for a snapshot test that **fails** whenever a template's text changes, forcing the developer to consciously version the template instead of editing it silently.

A snapshot test that appears to do this already exists — `test_template_snapshot_content_hash` in `tests/unit/test_prompt_templates.py` — but it is hollow:

- **Expected behavior:** editing a template's text should make the snapshot test fail, with a message telling the developer to bump the version.
- **Actual behavior:** the test computes an MD5 hash of all template content, then only asserts `isinstance(content_hash, str)` and `len(content_hash) == 32`. Both are *always* true regardless of template content, so the computed hash is never compared to a stored baseline. Any template change passes silently.

**Root cause:** the test never compares the freshly computed hash against a stored expected hash (baseline). The one value that would reveal a change — the hash itself — is discarded.

### Map
Files involved:

- **`tests/unit/test_prompt_templates.py`** — where the fix lives. The target is `test_template_snapshot_content_hash` (~lines 175–188). This is the only file that needs changing for the core fix.
- **`rag/generator/prompt_templates.py`** — the file being *guarded* (not edited as part of the fix). Holds `PROMPT_TEMPLATES` (5 templates: `skills_feedback`, `projects_feedback`, `presentation_feedback`, `gaps_feedback`, `first_impression`, each at version `v1`) and `get_template(name, version="v1")`. The test reads template content from here.

### Plan
1. **Capture the baseline hash.** Compute the current MD5 hash of the concatenated, sorted template content (reusing the existing hashing logic) and store it as an expected constant the test can compare against — e.g. a per-template mapping or a single combined hash, documented as the intentional snapshot.
2. **Make the assertion real.** Replace the two meaningless assertions with an equality check comparing the freshly computed hash to the stored baseline.
3. **Write a helpful failure message.** On mismatch, the assertion message should tell the developer: the template content changed; if intentional, bump the template version and update the stored hash.
4. **Prove it works both ways.** Confirm the test passes on unchanged templates, then temporarily edit a template and confirm it now fails (the reproduction from earlier, now caught). Revert the edit.
5. **Verify the whole file still passes** and the new behavior reads clearly for the next contributor.

### Inputs & outputs
- **Input:** the current content of all templates in `PROMPT_TEMPLATES`, plus a stored expected hash (the baseline snapshot).
- **Output:** a test that **passes** when template content matches the baseline and **fails** with a clear "bump the version and update the hash" message when it doesn't. No production/runtime code changes — this is a test-only guardrail that runs locally and in CI.

### Risks & unknowns
- **Hash granularity:** one combined hash for all templates is simplest but a failure won't say *which* template changed; a per-template hash gives clearer failures at the cost of more bookkeeping. Decide which the issue intends.
- **MD5 choice:** the existing code uses MD5. It's fine for change-detection (not security), so keeping it is reasonable and consistent — but worth a conscious note.
- **Baseline drift:** every intentional template edit now requires updating the stored hash. This is the *intended* friction, but the failure message must make that obvious or it will confuse contributors.
- **Ordering stability:** the hash depends on iterating templates/versions in a stable (sorted) order; non-deterministic ordering would cause false failures.

### Edge cases
- **New template added** or **new version added** (e.g. `v2`) — the baseline should account for it deliberately, not break unexpectedly.
- **Whitespace-only edits** (a trailing space, reflow) — these *do* change the hash and *should* fail; that's correct behavior (whitespace can affect model output).
- **Reordering templates** without changing text — sorted iteration should keep the hash stable so this doesn't cause a false failure.
- **Intentional change flow** — after a real edit, updating the stored hash must make the test green again, confirming the "bump + update" path works end to end.
