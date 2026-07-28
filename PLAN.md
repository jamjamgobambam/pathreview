# PLAN.md (rough draft)

## Solution plan

**Issue:** [Add snapshot tests for prompt templates to catch accidental changes (#37)](https://github.com/ascherj/pathreview/issues/37)

### Understand
There's already a test in `tests/unit/test_prompt_templates.py` called
`test_template_snapshot_content_hash` that looks like it should catch this, but it doesn't. It hashes
all the template content, and then just checks that the hash is a string of length 32. It never
compares that hash to anything fixed, so it can't actually tell if the content changed.

What should happen: if someone edits a template's wording without bumping its version, the test
suite should catch it and fail. What actually happens: you can change the text however you want and
everything stays green, because there's nothing pinned to compare against. I confirmed this in Week
8 by copying the templates, tweaking one, and rerunning the same hash logic - the hash changed like
it should, but the test itself would've kept passing either way.

### Map
- `rag/generator/prompt_templates.py` - this is where the templates actually live (5 of them, each
  currently sitting at version "v1"), plus `get_template()`. I don't think this needs to change,
  other than maybe bumping a version temporarily to make sure my fix actually works.
- `tests/unit/test_prompt_templates.py` - the main file I'll be editing. This is where the broken
  snapshot test is.
- Maybe a new file for storing the expected hashes, if I decide not to keep them inline in the test
  (something like `tests/unit/__snapshots__/prompt_templates.json`). Still deciding on this.

### Plan
1. Look around the repo first to see if there's already a snapshot-testing pattern or library in
   use (syrupy, pytest-snapshot, etc.) before I build something from scratch.
2. Decide: one combined hash for everything (closer to what's there now, simpler) or a separate
   expected hash per template/version (more setup, but tells you exactly what changed). Leaning
   toward the per-template version since a failure that just says "something changed" isn't that
   useful.
3. Record the current hashes as the "expected" baseline.
4. Rewrite the test to actually compare against that baseline and fail with a message that says
   which template/version drifted.
5. Actually test that it works - run it once with nothing changed (should pass), then edit a
   template on purpose, rerun (should fail), then put it back.

### Inputs & outputs
Input is just whatever's currently in `PROMPT_TEMPLATES` when the test runs. Output is pass or fail
- pass if every template's content still matches its recorded hash, fail (with a message pointing at
the specific template/version) if something drifted without the version being bumped.

### Risks & unknowns
- Don't know yet if there's already a snapshot convention elsewhere in the repo I should be
  following instead of rolling my own.
- Per-template hashes mean more to maintain than one combined hash - not 100% sure it's worth it yet.
- MD5 is already what's being used; no strong reason to swap it for sha256, but flagging it in case
  someone asks.
- All templates are currently on "v1" and I haven't seen any of them actually get bumped to "v2" -
  want to double check the intended workflow makes sense before assuming the test should handle
  multiple versions gracefully.

### Edge cases
- Someone adds a brand new template with no recorded hash yet - should fail loudly instead of just
  silently skipping it, so the hash gets recorded on purpose.
- A template gets a real new version added (v2 next to v1) - both versions should still get checked
  against their own hashes.
- Someone makes a "harmless" whitespace-only edit - should still count as a change and fail, since
  even small formatting shifts can affect what the model sees.
