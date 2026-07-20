# Plan: Snapshot tests for prompt template version drift

## Issue
[paste your issue link here]

## Problem
Prompt templates directly shape review quality, but the existing test
(`test_template_snapshot_content_hash`) only checked that a hash was a
32-character string — it never compared against a fixed baseline. This
meant a developer could silently edit a template's text and CI would
still pass, with no signal that review-affecting prompt content had
changed without a version bump.

## Approach
- Added `tests/unit/prompt_template_snapshots.py`: a checked-in baseline
  storing a SHA-256 hash per (template_name, version) pair.
- Added `tests/unit/generate_prompt_snapshots.py`: a script to regenerate
  the baseline. Only meant to be run when intentionally adding or
  changing a template version.
- Replaced the old no-op hash test in `test_prompt_templates.py` with a
  new `TestPromptTemplateSnapshots` class:
  - `test_template_content_matches_snapshot` — parametrized over every
    template/version, fails if content no longer matches the recorded hash.
  - `test_no_untracked_template_versions` — fails if a template/version
    exists in code but has no snapshot recorded.
  - `test_no_orphaned_snapshots` — fails if a snapshot exists for a
    template/version that's since been removed from the code.

## Why this enforces version bumps
Editing v1's text in place changes its hash, so the test fails. The
intended fix is to add a new version key (v2) with the updated text,
leaving v1's hash as a historical record, then regenerate snapshots.

This is a soft guard — a developer could technically regenerate the
baseline without bumping the version. Enforcement ultimately relies on
reviewers noticing a diff to `prompt_template_snapshots.py` in a PR that
doesn't also show a new version key being added in `prompt_templates.py`.

## Testing
- Ran `python -m pytest tests/unit/test_prompt_templates.py -v` — 43 passed.
- Verified failure mode by editing skills_feedback v1 text without a
  version bump; confirmed the test failed with the expected guidance
  message; reverted the change and confirmed 43 passed again.