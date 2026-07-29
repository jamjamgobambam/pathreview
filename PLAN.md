## Solution plan

**Issue:** [Add snapshot tests for prompt templates to catch accidental changes](https://github.com/ascherj/pathreview/issues/37)

### Understand

`PROMPT_TEMPLATES` stores prompt text in a nested mapping keyed first by template name and then by version, such as `PROMPT_TEMPLATES["skills_feedback"]["v1"]`. The current `TestPromptTemplates.test_template_snapshot_content_hash` test concatenates every prompt, computes an MD5 digest, and only asserts that the digest is a 32-character string. Because every MD5 digest has that shape, the assertion still passes after an existing prompt version is edited.

The expected behavior is for the test to compare every `(template name, version)` pair with a reviewed, deterministic snapshot. An accidental edit to an existing version must fail, while an intentional prompt change must be represented by an explicit new version and a corresponding reviewed snapshot update.

### Map

- `tests/unit/test_prompt_templates.py`
  - Replace the ineffective `test_template_snapshot_content_hash` assertion.
  - Add a small helper that produces a stable SHA-256 digest for each `(template name, version)` pair.
  - Store the expected version-keyed hashes close to the test so changes are visible in code review.
  - Add focused regression coverage for content and inventory changes.
- `rag/generator/prompt_templates.py`
  - Read the `PROMPT_TEMPLATES` structure and `get_template()` behavior as the source of truth.
  - No production change is expected; this file should only change in a separate, intentional prompt-version update.
- `JOURNAL.md`
  - Preserve the Week 8 reproduction evidence and link to this plan and the reproduction commit.

### Plan

1. Add an `EXPECTED_TEMPLATE_HASHES` mapping in `tests/unit/test_prompt_templates.py`, keyed by `(template_name, version)`, with a SHA-256 digest for each of the five current `v1` prompts.
2. Add a helper that accepts a nested prompt mapping and returns the same version-keyed digest mapping using each raw UTF-8 prompt string. Keeping snapshots separate avoids aggregate-hash ambiguity and makes failures identify the exact prompt version that changed.
3. Replace `test_template_snapshot_content_hash` with assertions that first compare the actual and expected key inventories and then compare each digest. Include failure messages that name the affected template/version and explain that an intentional content change needs a new version and reviewed snapshot.
4. Add regression tests using a copied prompt mapping to prove that a same-version content mutation fails without modifying the module-level `PROMPT_TEMPLATES`. Also cover a newly added version so an unreviewed inventory change cannot pass silently.
5. Run the complete prompt-template unit-test module and the repository's standard formatting/type/test checks. Review the diff to ensure the production prompts are unchanged and snapshot values are deterministic across repeated runs.

### Inputs & outputs

**Input:** The nested `PROMPT_TEMPLATES` mapping from `rag/generator/prompt_templates.py`, where each leaf is the exact prompt string for one `(template name, version)` key.

**Transformation:** Encode each prompt string as UTF-8 and calculate its SHA-256 digest independently. Compare the resulting key set and digests with the checked-in `EXPECTED_TEMPLATE_HASHES` mapping.

**Output:** Passing unit tests when both the prompt-version inventory and every current prompt string match their reviewed snapshots. A changed, removed, or newly added prompt version produces a focused assertion failure identifying the affected key. Runtime prompt lookup and generated review behavior remain unchanged.

### Risks & unknowns

- A contributor could update an expected hash while editing `rag/generator/prompt_templates.py` without adding a version. Tests cannot infer intent, so the failure message and code review must reinforce the version-bump rule.
- Hashing the raw prompt text intentionally treats whitespace and line-ending edits as content changes. This is desirable for strict snapshots, but the test message must make that sensitivity clear so the failure is not mistaken for nondeterminism.
- An aggregate digest would hide which prompt changed and could depend on iteration order. The implementation should use a key-to-digest mapping and compare the key inventory separately.
- When a legitimate `v2` is added, the old `v1` snapshot should remain unless that version is deliberately removed. The tests must not assume that every template will always have only one version.
- The initial expected digests must be generated from the unmodified upstream prompts and reviewed before being committed; generating them after an accidental local edit would bless the wrong baseline.

### Edge cases

- Existing content changes while its key remains `("skills_feedback", "v1")`; the digest comparison must fail.
- A new version such as `("skills_feedback", "v2")` is added without an expected snapshot; the inventory comparison must fail and name the unexpected key.
- A template or version is removed; the inventory comparison must report the missing expected key.
- Dictionary insertion order changes while names, versions, and content stay identical; version-keyed comparisons must continue to pass.
- A whitespace-only or newline-only edit occurs inside a prompt; the raw-content digest must treat it as a change.
- Two different template names contain identical prompt text; each key must still have its own independently checked snapshot entry.
