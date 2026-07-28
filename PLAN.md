# PLAN.md (rough draft)

## Solution plan

**Issue:** [Add snapshot tests for prompt templates to catch accidental changes (#37)](https://github.com/ascherj/pathreview/issues/37)

### Understand
`tests/unit/test_prompt_templates.py` already contains a test called `test_template_snapshot_content_hash`
that computes an MD5 hash of all template content in `PROMPT_TEMPLATES`. The root cause is that this
test never compares that hash against a fixed expected value - it only asserts generic things
(`isinstance(hash, str)`, `len(hash) == 32`), so it passes regardless of what the hash actually is.

Expected behavior: if any template's text changes without a version bump, the test suite should fail.
Actual behavior: template text can be edited freely and every test (including the "snapshot" one)
stays green, since nothing is pinned to a known-good value. Confirmed this in Week 8 by reproducing
against a monkeypatched copy of `PROMPT_TEMPLATES` - the hash changed as expected, but the test's
actual assertions still passed.

### Map
- `rag/generator/prompt_templates.py` - defines `PROMPT_TEMPLATES` (5 templates x versioned dict,
  currently all at `"v1"`) and `get_template()`. Not expected to change, aside from a test-only
  version bump while validating the fix.
- `tests/unit/test_prompt_templates.py` - primary file to change; contains
  `test_template_snapshot_content_hash` and the rest of the template test suite.
- Possibly a new snapshot/fixture file if expected hashes end up stored separately rather than
  inline in the test (e.g. `tests/unit/__snapshots__/prompt_templates.json`) - TBD.

### Plan
1. Check whether the repo already uses a snapshot-testing convention or library elsewhere
   (e.g. `syrupy`, `pytest-snapshot`) before hand-rolling anything new.
2. Decide between a single combined hash (matches current style, simplest) vs. per-template
   per-version expected hashes (more setup, but pinpoints exactly which template changed on
   failure). Leaning toward per-template for clearer failure messages.
3. Generate and record baseline expected hash(es) for the current template content.
4. Rewrite `test_template_snapshot_content_hash` to assert live hash(es) against the recorded
   expected hash(es), with a failure message identifying which template/version drifted.
5. Verify the fix actually works: confirm unmodified templates pass, then temporarily edit a
   template's wording (revert after) and confirm the test now fails as expected.

### Inputs & outputs
- **Input:** the live `PROMPT_TEMPLATES` dict (name -> version -> template string) at test-run time.
- **Output:** a pass/fail signal - test passes only when every template/version's content hash
  matches its recorded expected hash; fails with a clear message naming the template/version whose
  content drifted, prompting a deliberate version bump + hash update.

### Risks & unknowns
- Unclear if there's a preferred snapshot-testing pattern already used elsewhere in this codebase -
  need to check before committing to a hand-rolled hash approach.
- Per-template hashing adds more to maintain than a single combined hash; still deciding if the
  extra clarity is worth it.
- Not sure whether MD5 should be kept (already in use, just unenforced) or swapped for something
  like sha256 - probably no strong reason to change it.
- Unclear how version bumps are meant to work in practice (all templates are currently only at
  "v1") - want to confirm the intended workflow before assuming the test should compare across
  version keys automatically vs. per-fixed-version.

### Edge cases
- A brand-new template added to `PROMPT_TEMPLATES` with no recorded expected hash yet - test should
  fail clearly (not silently skip) so the new template's hash gets deliberately recorded.
- A template gets a genuinely new version key added (e.g. `"v2"`) alongside `"v1"` - test should
  still validate both versions' content against their own expected hashes.
- Whitespace-only or formatting-only edits to a template - these should still be treated as content
  changes and fail the test, since even minor wording/formatting shifts can affect model output.
