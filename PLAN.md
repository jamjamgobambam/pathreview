## Solution plan

**Issue:** [Add snapshot tests for prompt templates to catch accidental changes](https://github.com/ascherj/pathreview/issues/37)

### Understand
The `rag/generator/prompt_templates.py` module stores versioned prompt
templates (a dict of `name -> version -> template string`). The intent
is that if a template's content changes, the version key should be
bumped (e.g. `v1` -> `v2`) so historical behavior is preserved and
reviewable in code. However, nothing currently enforces this contract.
A developer can silently edit the content of `v1` and no test will fail.

The existing `test_template_snapshot_content_hash` test in
`tests/unit/test_prompt_templates.py` looks like a snapshot test but
only asserts that an MD5 hex digest is 32 characters long — a
tautology that holds for any string content. Expected behavior: the
test suite should fail when a registered template version's content
changes without a corresponding new version being added.

### Map
Files involved:
- `tests/unit/test_prompt_templates.py` — where the fix lives. Remove
  the placeholder `test_template_snapshot_content_hash` and add real
  snapshot tests.
- `rag/generator/prompt_templates.py` — no changes needed. This is
  the module being pinned by the snapshots.

### Plan
1. Delete `test_template_snapshot_content_hash` (the placeholder).
2. Add an `EXPECTED_TEMPLATE_SNAPSHOTS` class attribute on
   `TestPromptTemplates` — a dict keyed by `(template_name, version)`
   mapping to the SHA-256 hex digest of the template's content.
3. Add `test_template_content_matches_snapshot`: iterate over
   `EXPECTED_TEMPLATE_SNAPSHOTS`, compute the current SHA-256 of each
   template version, and assert equality. On mismatch, raise a clear
   error telling the developer to add a NEW version (e.g. `v2`)
   rather than update the existing hash.
4. Add `test_every_template_version_has_a_snapshot`: iterate over
   `PROMPT_TEMPLATES` and assert every `(name, version)` pair has a
   registered snapshot. This catches the reverse mistake of adding a
   new template without pinning it.
5. Verify: run the full file's test suite, then manually edit a
   template and confirm the snapshot test fails with the right error.

### Inputs & outputs
- Input: current contents of `PROMPT_TEMPLATES` in
  `rag/generator/prompt_templates.py`.
- Output: two new pytest tests that fail on unregistered template
  drift and pass otherwise. No runtime behavior of the app changes.

### Risks & unknowns
- **Hash collisions:** SHA-256 collisions are astronomically unlikely
  for text of this size, so not a real risk. Chose SHA-256 over MD5
  because MD5 is deprecated for content integrity even in
  non-cryptographic uses.
- **Pre-existing lint/type errors in the file:** the file has ruff
  and mypy violations on tests that existed before this change (missing
  return annotations, `key in dict.keys()`, unused loop vars). Fixing
  them balloons the diff. Plan: leave them, note in the PR, offer a
  follow-up.
- **What if a developer legitimately wants to update `v1`?** They
  can't silently — they must either add `v2` or, if truly deleting
  `v1` behavior, also update `EXPECTED_TEMPLATE_SNAPSHOTS`. This is
  intentional friction, which is the whole point of the issue.

### Edge cases
- Template added but no snapshot registered →
  `test_every_template_version_has_a_snapshot` fails with a clear
  "add the hash to EXPECTED_TEMPLATE_SNAPSHOTS" message.
- Snapshot registered but the template was deleted from
  `PROMPT_TEMPLATES` → `test_template_content_matches_snapshot` fails
  with a "template missing but has a snapshot" message.
- Template content change without a version bump →
  `test_template_content_matches_snapshot` fails with expected vs.
  actual hash and instructions to add a new version.