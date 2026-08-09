# Journal

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/soccerthomas/pathreview/commit/f53bbd8

**Reproduction summary:**
Ran the existing test suite and confirmed `test_template_snapshot_content_hash`
passed regardless of template content, since it only checked that the hash
was a 32-character string with no comparison to a fixed baseline. This
confirmed the gap described in the issue: prompt template edits could
happen silently with no test signal, even though prompt content directly
affects review quality.

**PLAN.md link:** https://github.com/soccerthomas/pathreview/blob/fix/prompt-template-snapshot-tests/PLAN.md

**Blockers or open questions:**
Unsure whether the maintainer expects MD5 (matching the original test) or
SHA-256 (what I used) for the hash algorithm — flagging this for review
when I open the PR in Week 9. Also uncertain whether the "soft guard"
nature of this approach (a developer could regenerate the snapshot
baseline without bumping the version) is an acceptable tradeoff or if a
stricter enforcement mechanism is expected.
## Week 9 — Implementation & validation

**Implementation commit:** f53bbd8

**What I changed:**
Implemented snapshot-based checks for the versioned prompt templates so
changes to prompt content produce a test failure instead of silently
passing. The snapshots use the template name/version as the baseline for
detecting unexpected content changes.

**Testing:**
- `make test-unit`: 53 failed, 381 passed. The failures were distributed
  across existing unrelated modules; the prompt-template tests were not
  among the reported failures.
- `pytest tests/unit/test_prompt_templates.py -v`: 43 passed.
- `ruff check tests/unit/test_prompt_templates.py`: passed.
- `make check`: could not complete because the repository's full lint run
  reports pre-existing failures across unrelated files.

**Self-review:**
Reviewed the changed prompt-template tests and ran targeted tests and
linting. No unrelated files were changed as part of the contribution.

**Open questions:**
The implementation uses SHA-256 for the snapshot hashes. I still want
maintainer/peer feedback on whether that is the preferred algorithm and
whether the snapshot baseline should be treated as a soft guard.

**PR:** To be added after the PR is opened.