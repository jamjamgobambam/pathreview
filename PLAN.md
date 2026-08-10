## Solution plan

**Issue:** Add snapshot tests for prompt templates to catch accidental changes — https://github.com/ascherj/pathreview/issues/37

### Understand

**Root cause.** PathReview generates every review from the five prompt templates in
[rag/generator/prompt_templates.py](rag/generator/prompt_templates.py). The suite that is
supposed to guard them, [tests/unit/test_prompt_templates.py](tests/unit/test_prompt_templates.py),
has a test named `test_template_snapshot_content_hash` that *looks* like a snapshot test but
is a no-op. It builds an MD5 hash of all template content and then asserts only:

```python
assert isinstance(content_hash, str)   # always true
assert len(content_hash) == 32         # always true for any MD5
```

Neither assertion depends on the template text. The comment even says
"Expected hash - update if templates intentionally change" but no expected hash is ever
compared. Every other test checks for the *presence* of placeholders / keywords, not the
*exact wording*, so nothing detects a reworded template.

**Expected vs. actual.**
- Expected: editing a template's text without bumping its version fails the suite, forcing
  a deliberate version bump + snapshot update.
- Actual: any wording change ships silently — reproduced locally by editing the
  `skills_feedback` text and watching all 37 tests still pass.

### Map

Files/functions involved:
- [rag/generator/prompt_templates.py](rag/generator/prompt_templates.py) — `PROMPT_TEMPLATES`
  (nested dict: name → version → text) and `get_template(name, version="v1")`. Source of truth;
  I do **not** intend to change the template text here.
- [tests/unit/test_prompt_templates.py](tests/unit/test_prompt_templates.py) — the guard.
  `test_template_snapshot_content_hash` (the no-op) is the primary thing I'll replace/augment.
- **New:** `tests/unit/snapshots/prompt_template_hashes.json` (or an inline constant in the test
  module) — the stored expected per-template hashes that the snapshot test asserts against.

### Plan

1. **Add a stored snapshot of expected hashes.** Compute a per-template (name + version) hash
   and store the expected values in a committed `EXPECTED_TEMPLATE_HASHES` mapping (inline dict
   or a small JSON file loaded by the test). Baseline values are already captured:
   combined MD5 `3e79f974f8c1b6d8d1481dfc42e949ca`; per template e.g.
   `skills_feedback/v1: f93103d823482a2e65decc6653e4ee5c`.
2. **Rewrite `test_template_snapshot_content_hash` into a real assertion.** For each template,
   assert its current hash equals the stored expected hash, with a failure message that tells
   the developer to bump the version and update the snapshot if the change was intentional.
3. **Add a "no orphan / no missing snapshot" check.** Assert the set of templates in
   `PROMPT_TEMPLATES` exactly matches the set of keys in the stored snapshot, so adding or
   removing a template (or version) without updating snapshots also fails.
4. **Document the escape hatch.** A short docstring / comment describing the deliberate workflow:
   change template → test fails → bump version key (e.g. add `"v2"`) and add its hash to the snapshot.
5. **Verify.** Run `make test-unit` clean, then re-run the reproduction edit to confirm the test
   now **fails**, then revert.

### Inputs & outputs

- **Input:** the contents of `PROMPT_TEMPLATES` (each template's text, keyed by name and version)
  and the stored `EXPECTED_TEMPLATE_HASHES` snapshot.
- **Output/change:** a passing snapshot test on unchanged templates, and a failing test the moment
  any template text changes without a corresponding snapshot/version update. No production behavior
  changes — this is test-only plus a snapshot data file.

### Risks & unknowns

- **MD5 choice.** MD5 is fine for change-detection (not security); keep it to match the existing
  code, but note it in a comment so a reviewer doesn't flag it as a security concern.
- **Snapshot location.** Inline dict in the test is simplest and reviewable in the same diff;
  a separate JSON is cleaner but adds a file to load. Leaning inline dict unless mentors prefer a file.
- **Whitespace sensitivity.** Hashing raw template strings means trailing-whitespace/newline edits
  also trip the test. That is the intended strictness, but I need to confirm maintainers want *exact*
  matching rather than normalized text.
- **CI / pre-commit reformatting.** `black`/`ruff` run in `make check`; I must make sure the stored
  hashes reflect the post-format template text so the snapshot doesn't drift on the formatter's pass.
- **Unknown:** whether maintainers expect this generalized to future versions (`v2`, `v3`) — the
  set-equality check in step 3 covers that, but I'll confirm the desired granularity on the issue thread.

### Edge cases

- A template's text changes but its version key does **not** → must FAIL (core requirement).
- A new template is added to `PROMPT_TEMPLATES` with no snapshot entry → must FAIL.
- A template is removed → the snapshot has an orphan entry → must FAIL.
- A new version (`v2`) is added deliberately with its hash → must PASS.
- Empty/whitespace-only edit (e.g. trailing newline) → must FAIL (intended strictness).
- Reordering the dict keys without changing text → must still PASS (hash per template, sorted keys).
