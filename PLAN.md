## Solution plan

**Issue:** Issue  #37: Add snapshot tests for prompt templates to catch accidental changes



### Understand
The existing `test_template_snapshot_content_hash` test computed a
combined MD5 hash of all prompt template content but never compared it
against a fixed baseline — it only asserted the hash was a 32-character
string. Since prompt templates directly shape review quality, this meant
a developer could silently edit a template's wording and CI would still
pass, with no signal that review-affecting content changed without a
conscious version bump. Expected behavior: editing a template's text
without adding a new version key should fail tests. Actual behavior
(before fix): any edit passed silently.

### Map
- `rag/generator/prompt_templates.py` — source of truth, contains
  `PROMPT_TEMPLATES` dict and `get_template()`. Not modified, only read.
- `tests/unit/test_prompt_templates.py` — removed the no-op hash test,
  added a new `TestPromptTemplateSnapshots` class.
- `tests/unit/prompt_template_snapshots.py` (new) — checked-in baseline
  of per-version SHA-256 hashes.
- `tests/unit/generate_prompt_snapshots.py` (new) — script to regenerate
  the baseline when a version is intentionally added or changed.

### Plan
1. Add a baseline snapshot file storing one hash per (template_name, version).
2. Add a generator script that computes hashes from `PROMPT_TEMPLATES`
   and writes the baseline file.
3. Replace the old no-op snapshot test with a parametrized test that
   compares each live template's hash against its recorded baseline hash.
4. Add coverage for drift in the other direction: a template/version
   with no snapshot recorded, and a snapshot with no matching template
   left in code.
5. Run the generator once to populate real baseline hashes, verify all
   tests pass, then verify the guard actually fails when template text
   changes without a version bump.

### Inputs & outputs
- Input: `PROMPT_TEMPLATES` dict (name -> version -> template string) in
  `prompt_templates.py`.
- Output: a pass/fail test result. Failing output includes a message
  telling the developer to add a new version key rather than edit the
  existing one in place, plus the exact regeneration command to run
  once that's done.

### Risks & unknowns
- This is a soft guard: a developer could regenerate the baseline
  without actually bumping the version key, defeating the purpose.
  Real enforcement depends on a reviewer noticing a
  `prompt_template_snapshots.py` diff without a corresponding new
  version key in `prompt_templates.py` — I should call this out in the
  PR description in Week 9.
- Encoding: `Path.write_text()` defaults to the OS locale encoding on
  Windows, which broke on an em-dash in my docstring. Fixed by passing
  `encoding="utf-8"` explicitly — worth double-checking other file-write
  calls in the codebase for the same issue if I touch them later.
- Uncertain whether the maintainer wants MD5 or SHA-256 for the hash —
  I used SHA-256 since it's the modern default, but the original test
  used MD5, so this might get flagged in review.

### Edge cases
- A template name exists in code but has no snapshot recorded (new
  template added) — caught by `test_no_untracked_template_versions`.
- A snapshot exists for a template/version that's been removed from
  code (stale entry) — caught by `test_no_orphaned_snapshots`.
- A version's text changes without a version bump — caught by
  `test_template_content_matches_snapshot`.
- Multiple versions of the same template (e.g. v1 and v2 coexisting) —
  each gets its own independent hash entry, so old versions keep
  working even after a new one is added.