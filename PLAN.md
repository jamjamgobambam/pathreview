## Solution plan

**Issue:** #37 — Add snapshot tests for prompt templates to catch accidental changes
(https://github.com/ascherj/pathreview/issues/37)

### Understand
PathReview generates portfolio reviews from five versioned prompt templates defined in
`rag/generator/prompt_templates.py` (`PROMPT_TEMPLATES`, a `{name: {version: text}}` dict).
The wording of these templates directly shapes AI output, so an accidental one-word edit can
silently change every review with no test failure and no signal in code review.

The repo *appears* to already guard this: `tests/unit/test_prompt_templates.py` has a test
named `test_template_snapshot_content_hash`. But that test is a no-op — it computes an MD5 of
the concatenated templates and then only asserts `isinstance(content_hash, str)` and
`len(content_hash) == 32`. It never compares the hash against a stored/expected value, so the
assertion is true for *any* template content.

**Root cause:** The existing "snapshot" test never pins the template content to a stored
baseline. There is no per-template expected hash and no mechanism tying a content change to a
version bump. Editing a template does not fail any test.

**Expected vs. actual:**
- *Expected:* editing a template's text without adding a new version entry (e.g. `v2`) fails a
  test with a clear message telling the developer to either revert or version the change.
- *Actual (reproduced 2026-07-27):* rewriting the `skills_feedback` template left all 37 tests
  in the file green. See the reproduction comment in `test_prompt_templates.py`.

### Map
Files I expect to touch:
- `tests/unit/test_prompt_templates.py` — replace the no-op `test_template_snapshot_content_hash`
  with real snapshot tests. This is the primary change and matches the issue's stated scope
  (single test file). I'll follow the existing `@pytest.mark.unit` class-based style already in
  this file.
- `rag/generator/prompt_templates.py` — **read-only for the fix itself.** This is the source of
  truth for template content and the `get_template(name, version="v1")` accessor
  (lines 8–141). I do not plan to change production code; if the reviewer prefers the snapshot
  baseline to live next to the templates, I may add a small `EXPECTED_TEMPLATE_HASHES` constant
  here instead of in the test — noted as an open decision below.

Reference points (no changes expected):
- `rag/generator/review_generator.py:52` — `get_template(section_name)` is the sole caller,
  confirming these five templates are the live prompts.
- Existing sibling tests (`test_output_parser.py`, `test_faithfulness_checker.py`) — to mirror
  assertion/message style and marker usage.

Current baseline values (captured 2026-07-27, five templates, all `v1`):
- concatenated MD5: `3e79f974f8c1b6d8d1481dfc42e949ca`
- per-template sha256[:16]: `skills_feedback a24d6d717d4f365c`,
  `projects_feedback 7e53575582f45389`, `presentation_feedback 87230b7045d66a1f`,
  `gaps_feedback b2673a1a1f018f2f`, `first_impression 9e7697ff3efd892c`

### Plan
1. Run `make test-unit` to confirm the current suite passes before I change anything (baseline).
2. Add a module-level `EXPECTED_SNAPSHOTS` map of `template_name -> {version: sha256_hash}` in
   the test file, seeded with the captured baseline hashes above. Prefer sha256 over MD5 and
   hash each `(name, version)` individually so a failure names the exact template.
3. Replace `test_template_snapshot_content_hash` with:
   - `test_every_template_version_matches_snapshot` — iterate `PROMPT_TEMPLATES`, hash each
     `(name, version)` text, assert it equals the stored snapshot, with a message that says
     "Template '{name}' {version} changed. If intentional, add a new version and update the
     snapshot; do not edit an existing version in place."
   - `test_no_untracked_template_versions` — assert the set of `(name, version)` keys equals the
     set of keys in `EXPECTED_SNAPSHOTS`, so a newly *added* template/version must be registered
     (catches additions, not just edits).
4. Run `make test-unit` to confirm the new tests pass against the current templates.
5. Re-run the reproduction (edit one template's wording) to confirm the new test now FAILS with
   the intended message, then revert the edit.
6. Run `make check` (ruff + black + mypy) to confirm lint/format/types are clean.

### Inputs & outputs
**What the fix consumes:** the live `PROMPT_TEMPLATES` dict from
`rag/generator/prompt_templates.py` and a stored `EXPECTED_SNAPSHOTS` baseline in the test module.

**What it produces/changes:** no runtime/production behavior change — only test behavior.

- *Happy path:* templates unchanged → snapshot tests pass.
- *Accidental edit:* an existing version's text changes → `test_every_template_version_matches_snapshot`
  fails naming the exact template and instructing a version bump.
- *New version added deliberately:* developer adds `skills_feedback["v2"]` and a matching entry
  in `EXPECTED_SNAPSHOTS` → tests pass. Adding the version without registering it → 
  `test_no_untracked_template_versions` fails.

**Test I'll write (shape):**
```python
EXPECTED_SNAPSHOTS = {
    "skills_feedback": {"v1": "a24d6d71...full sha256..."},
    # ...remaining four templates
}

def test_every_template_version_matches_snapshot(self):
    for name, versions in PROMPT_TEMPLATES.items():
        for version, text in versions.items():
            digest = hashlib.sha256(text.encode()).hexdigest()
            assert digest == EXPECTED_SNAPSHOTS[name][version], (
                f"Template '{name}' {version} changed. If intentional, add a new "
                f"version entry and update EXPECTED_SNAPSHOTS; do not edit v1 in place."
            )
```
I'll follow the existing `@pytest.mark.unit` `TestPromptTemplates` class layout in the file.

### Risks & unknowns
1. **Newline / whitespace sensitivity.** These are triple-quoted strings with trailing newlines;
   a hash pins every byte, including trailing whitespace an editor might touch. That strictness
   is the point, but I'll confirm `black` doesn't reformat the strings (it shouldn't touch string
   *contents*) so the baseline stays stable — flagged for step 6.
2. **Where the baseline should live.** Storing hashes in the test file keeps the change to one
   file (matches issue scope); storing them next to the templates couples the snapshot to the
   source. I'll default to the test file and ask the reviewer in the PR if they prefer otherwise.
3. **sha256 vs the existing MD5.** The current test used MD5. I plan to switch to sha256 for the
   real assertion; if the reviewer wants to preserve MD5 for consistency I can switch back — it's
   a one-line change and doesn't affect behavior.
4. **Interaction with other tests.** Other tests in this file already assert placeholder presence
   and JSON hints; my snapshot tests are additive and shouldn't conflict, but I'll run the whole
   file (step 4) to be sure I didn't rename/remove a test something else depends on.

### Edge cases
- **Whitespace-only edit** (extra trailing space in a template): must fail the snapshot — a hash
  catches this where a substring check wouldn't.
- **Adding a brand-new template** (sixth entry): `test_no_untracked_template_versions` must fail
  until the author registers it in `EXPECTED_SNAPSHOTS`.
- **Adding a new version to an existing template** (`v2`) with `v1` untouched: should pass once
  the new version's hash is registered; `v1` must still match its stored hash.
- **Reordering keys in `PROMPT_TEMPLATES`**: must NOT fail — I hash per `(name, version)` rather
  than the concatenation, so dict ordering is irrelevant.
- **Unicode / non-ASCII characters in a future template**: `.encode()` defaults to UTF-8, so the
  hash stays stable and deterministic across platforms; I'll keep encoding explicit.
