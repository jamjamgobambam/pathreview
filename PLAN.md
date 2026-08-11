# Solution plan

**Issue:** [Add snapshot tests for prompt templates to catch accidental changes](https://github.com/ascherj/pathreview/issues/37)

## Understand

**Root cause:** Prompt templates in `rag/generator/prompt_templates.py` are versioned dictionaries (`PROMPT_TEMPLATES`), but the test suite does not lock in their full text content. The existing `test_template_snapshot_content_hash` in `tests/unit/test_prompt_templates.py` computes an MD5 hash of all templates yet only asserts that the result is a 32-character string — it never compares against a known expected value.

**Expected behavior:** If a developer edits a template's `v1` text in place (typo fix, wording tweak, new instruction), unit tests should **fail** and force them to either revert the change or add a new version key (e.g. `v2`) and update the snapshot deliberately.

**Actual behavior:** A one-word change to any `v1` template (e.g. `"Analyze"` → `"Analyse"`) changes the content hash but all 37 existing prompt-template tests still pass. Template content can drift silently, which may change LLM review quality without anyone noticing in CI.

**Reproduction (Week 8):** See `tests/unit/test_issue_37_snapshot_reproduction.py` — demonstrates that original and mutated template content both satisfy the stub snapshot assertions.

## Map

| File | Role |
|------|------|
| `rag/generator/prompt_templates.py` | Source of truth for template text (read-only for this issue) |
| `tests/unit/test_prompt_templates.py` | Primary test file named in the issue; hosts existing template tests and stub snapshot test |
| `tests/unit/test_issue_37_snapshot_reproduction.py` | Week 8 reproduction tests documenting the gap (keep; may fold assertions into main file in Week 9) |
| `tests/fixtures/prompt_template_snapshots.json` *(new)* | Optional golden-file store for per-template SHA-256 hashes |

**Functions involved:**
- `PROMPT_TEMPLATES` dict — template storage
- `get_template(name, version)` — retrieval helper (unchanged)
- `test_template_snapshot_content_hash()` — stub to replace/strengthen

## Plan

1. **Define snapshot constants** — ✅ Done
   - Computed SHA-256 hash for each `(template_name, version)` pair in `PROMPT_TEMPLATES` (5 templates × `v1` today).
   - Chose **Python constants** over a JSON fixture (resolves the Week 8 open question) — no new file I/O, matches existing test style in this repo.
   - `EXPECTED_TEMPLATE_HASHES` dict + `EXPECTED_COMBINED_TEMPLATE_HASH` added at the top of `test_prompt_templates.py`, with a module docstring documenting the version-bump workflow.

2. **Add per-template snapshot assertions** — ✅ Done
   - Added `test_each_template_matches_snapshot_hash()` — iterates all templates and asserts `sha256(text) == expected[name][version]`, with an assertion message naming the exact template/version that drifted.
   - Strengthened `test_template_snapshot_content_hash` to assert the combined hash equals `EXPECTED_COMBINED_TEMPLATE_HASH` (previously only checked hash format).
   - Added `test_snapshot_hashes_cover_every_template_version()` — catches both a new template/version added without a snapshot entry, and a stale snapshot left behind after removal.

3. **Add a regression test for the failure mode** — ✅ Done
   - Added `test_snapshot_detects_unversioned_content_edit()` — mutates `skills_feedback` v1 text in-memory and asserts the mutated hash no longer matches the expected snapshot, proving the guardrail would catch this exact failure mode.
   - Manually verified end-to-end: temporarily edited `rag/generator/prompt_templates.py` (`"Analyze"` → `"Analyse"`), confirmed 3 tests failed with a clear diff, then reverted the edit and confirmed all 40 tests passed again.

4. **Verify CI compatibility and document update workflow** — ✅ Done
   - Ran `make test-unit`; all prompt template tests pass with current snapshots (40/40).
   - Documented the workflow in the module docstring: add a new version key (e.g. `v2`) instead of editing an existing version in place, then add its hash to `EXPECTED_TEMPLATE_HASHES`.

5. **Clean up reproduction file** — ✅ Done (removed, not merged)
   - Deleted `tests/unit/test_issue_37_snapshot_reproduction.py`. Once real snapshots existed, one of its assertions (`test_no_expected_snapshot_values_are_asserted_anywhere`) started failing because it explicitly checked that no `EXPECTED_*` constants existed — the fix landing made that check obsolete rather than useful. History is preserved in the Week 8 `JOURNAL.md` entry and commit `ebcece3`.

## Inputs & outputs

**Inputs:**
- Current `PROMPT_TEMPLATES` dict from `rag/generator/prompt_templates.py`
- Template name + version keys (e.g. `"skills_feedback"`, `"v1"`)

**Outputs / changes:**
- New expected hash constants or JSON fixture file
- Strengthened tests in `tests/unit/test_prompt_templates.py` that fail on unversioned content edits
- Passing `make test-unit` with snapshots matching current template content
- Failing tests if someone edits `v1` text without updating snapshots or adding `v2`

## Risks & unknowns

| Risk | Mitigation |
|------|------------|
| **Hash algorithm choice** — MD5 vs SHA-256 | Use SHA-256 for new snapshots (stronger, clearer intent); keep reproduction MD5 logic separate if needed |
| **False positives on whitespace/line-ending changes** | Normalize template strings (strip trailing whitespace) before hashing, or store full exact text snapshots to avoid ambiguity |
| **Legitimate template updates blocked** | Document clearly that edits require a new version key (`v2`) + new snapshot entry, not in-place `v1` edits |
| **Multiple students working same issue** | Snapshot values are deterministic from template text; merge conflicts only if someone changes templates on main simultaneously |
| **`get_template()` default version behavior** | Confirm default is `"v1"` so snapshot coverage matches what production code uses — already tested by `test_get_template_default_version` |

**Open question:** Store hashes in Python constants vs JSON fixture?
- **Constants** — simpler, no file I/O, matches existing test style in this repo
- **JSON fixture** — easier to diff in PR review when snapshots update
- **Leaning toward:** Python constants in `test_prompt_templates.py` for simplicity (no new dependencies)

## Edge cases

1. **New template added to `PROMPT_TEMPLATES`** — snapshot test should fail until a new expected hash entry is added (desired behavior).
2. **New version key added (e.g. `v2`)** — test must iterate all version keys dynamically, not hardcode only `v1`.
3. **Empty or missing template text** — existing `test_templates_are_strings` covers non-empty; snapshot test should skip or fail loudly on empty strings.
4. **Placeholder syntax unchanged but surrounding text edited** — snapshot catches this (expected — that's the point of the issue).
5. **Intentional `v1` retirement** — if a version key is removed entirely, snapshot dict entry should be removed in the same PR; test loop over live keys prevents stale entries.
6. **Unicode or special characters in templates** — hash UTF-8 encoded strings consistently (`text.encode("utf-8")`).

---

*Living document — will update in Week 9 as implementation proceeds.*
