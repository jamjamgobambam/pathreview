## Solution plan

**Issue:** Add snapshot tests for prompt templates to catch accidental changes. https://github.com/ascherj/pathreview/issues/37

### Understand
The prompt templates in the review generation flow are stored as plain strings in [rag/generator/prompt_templates.py](rag/generator/prompt_templates.py). Today, the test suite checks that templates exist and contain expected placeholders, but it does not lock the full prompt text. That means a small wording change can slip into production without being noticed, which could subtly change review quality or output structure.

Expected behavior: each template version should be covered by a regression test that asserts the exact prompt content, so any accidental edit fails loudly unless it is intentionally approved.

### Map
Files and modules involved:
- [rag/generator/prompt_templates.py](rag/generator/prompt_templates.py) — source of the prompt template definitions and retrieval helper.
- [tests/unit/test_prompt_templates.py](tests/unit/test_prompt_templates.py) — existing unit tests that should be expanded with snapshot-style coverage.
- [rag/generator/review_generator.py](rag/generator/review_generator.py) — downstream consumer of the templates, useful to confirm the change is scoped to prompt content rather than generation behavior.

### Plan
1. Review the current prompt templates and choose the canonical versions to lock down for regression testing.
2. Add snapshot-style assertions for each template name/version in [tests/unit/test_prompt_templates.py](tests/unit/test_prompt_templates.py), using a structure that clearly shows diffs when content changes.
3. Keep the tests focused on exact prompt text while preserving the existing checks for placeholders, version presence, and retrieval behavior.
4. Run the relevant unit tests and verify that intentional template edits require an explicit snapshot update.
5. Document the expectation that prompt rewrites should be reviewed carefully and updated only when the wording change is intentional.

### Inputs & outputs
Inputs:
- The current prompt template dictionary and template names/versions from [rag/generator/prompt_templates.py](rag/generator/prompt_templates.py).
- Existing unit test expectations in [tests/unit/test_prompt_templates.py](tests/unit/test_prompt_templates.py).

Outputs:
- A regression test suite that fails when a prompt template changes unexpectedly.
- Clear, reviewable snapshot output for each prompt template version so future edits are explicit.

### Risks & unknowns
- **Whitespace noise in the template bodies.** The templates in [rag/generator/prompt_templates.py](rag/generator/prompt_templates.py) are triple-quoted strings with leading indentation and trailing newlines, so a raw exact-string snapshot could fail on invisible edits. Risk: brittle, hard-to-review diffs. Mitigation/investigation: decide up front whether to snapshot the templates verbatim or after a documented normalization (e.g. `textwrap.dedent` / `.strip()`), and lock that choice in the test.
- **No snapshot plugin may be installed.** Investigation path: check [pyproject.toml](pyproject.toml) and any `pytest.ini`/`setup.cfg` for `syrupy` or `pytest-snapshot` before writing the tests. If absent, prefer a lightweight in-repo approach (assert against stored expected strings / a committed expected-hash constant) rather than adding a dependency.
- **The existing `test_template_snapshot_content_hash` is a false-positive test.** In [tests/unit/test_prompt_templates.py](tests/unit/test_prompt_templates.py#L175-L188) it computes an MD5 but only asserts `len(...) == 32`, so it never locks content. Risk: changing it alters an existing test's contract; I must decide whether to fix it in place (compare against a committed expected hash) or replace it with per-template snapshots, and update the docstring accordingly.
- **Intentional template edits must stay explicit.** When a template in `prompt_templates.py` is deliberately changed, the corresponding snapshot/expected value must be updated deliberately (with a documented update step), not silently — otherwise the guard erodes over time.

### Edge cases
- Missing or renamed template versions should fail clearly.
- Placeholder changes such as removing {context} or {github_username} should be caught by the snapshot coverage.
- New template versions should be added intentionally and must include explicit test coverage.
- Very small wording changes should be visible in the snapshot diff so they are easy to review.