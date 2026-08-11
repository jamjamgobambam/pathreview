# Solution plan

**Issue:** [Add snapshot tests for prompt templates to catch accidental changes (Issue #37)](https://github.com/ascherj/pathreview/issues/37)

### Understand
* **Root cause:** The unit test `test_template_snapshot_content_hash` in [test_prompt_templates.py](file:///Users/leminhhieu/github/pathreview/tests/unit/test_prompt_templates.py) is a placeholder. It calculates the MD5 hash of the prompt templates but only asserts that the hash is a 32-character string, instead of asserting it against an expected reference value.
* **Expected behavior:** Any change to the content of an existing prompt template version (e.g. modifying `v1` of `skills_feedback`) should cause the test suite to fail. Developers must consciously bump versions (e.g., introduce `v2`) or explicitly update snapshots when prompt changes are intended.
* **Actual behavior:** Developers can silently modify the contents of any prompt template version without any test failures.

### Map
* **Files involved:**
  * [rag/generator/prompt_templates.py](file:///Users/leminhhieu/github/pathreview/rag/generator/prompt_templates.py): Defines the versioned templates in `PROMPT_TEMPLATES`.
  * [tests/unit/test_prompt_templates.py](file:///Users/leminhhieu/github/pathreview/tests/unit/test_prompt_templates.py): Location of the test suite where the snapshot verification needs to be implemented.
  * Optionally, new file(s) under `tests/snapshots/` if we choose filesystem-based snapshot files for greater transparency.

### Plan
1. **Design Snapshot Strategy:** Decide between using a hardcoded dictionary of MD5 hashes per template version in the test file versus filesystem-based snapshot files (e.g. `tests/snapshots/{template_name}_{version}.txt`).
   * *Choice:* Filesystem-based snapshot files are preferred because a `git diff` shows the exact text changes in prompt templates.
2. **Implement Snapshot Generation/Assertion Logic:** Write logic to read snapshots from `tests/snapshots/` and assert they match the current `PROMPT_TEMPLATES`. Include an easy way to write/update snapshots (e.g. a custom `--update-snapshots` CLI flag or auto-generation of new template versions).
3. **Verify Snapshot Failure:** Test the implementation by editing a template to verify the test fails, and reverting the change to ensure it passes.
4. **Verify Version Bump flow:** Add a new test template/version and verify the test handles it correctly.

### Inputs & outputs
* **Inputs:** The active versioned prompt templates loaded from [prompt_templates.py](file:///Users/leminhhieu/github/pathreview/rag/generator/prompt_templates.py).
* **Outputs:** 
  * A set of snapshot files stored on disk.
  * Test execution results (Pass when templates match snapshots, Fail when there is any mismatch).

### Risks & unknowns
* **Risk:** Different operating systems might check out files with different line endings (LF vs CRLF), which would alter the MD5 hash or file comparison and cause tests to fail on Windows.
  * *Mitigation:* Normalize all line endings (e.g., `.replace("\r\n", "\n")`) before calculating hashes or doing string comparisons.

### Edge cases
* **Whitespace / formatting sensitive changes:** Extra trailing newlines or spacing. (Snapshot tests must catch these as LLM outputs can be sensitive to formatting).
* **Adding new versions:** Introducing a new version should not modify or invalidate the snapshots of older versions.
