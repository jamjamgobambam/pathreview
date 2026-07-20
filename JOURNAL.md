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