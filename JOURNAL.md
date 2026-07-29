## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/37

**Issue title:** Add snapshot tests for prompt templates to catch accidental changes.

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Prompt templates drive the wording and structure of generated review output, so even small edits can change review quality or formatting. The current test coverage checks that templates exist and contain placeholders, but it does not lock the exact prompt text for each version, so template bodies can drift silently. Adding snapshot coverage in `tests/unit/test_prompt_templates.py` will make any content change fail unless developers intentionally add a new version and update the snapshot. That keeps prompt evolution explicit and prevents accidental regressions in review behavior.

**Branch name:** test/37-prompt-template-snapshots

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/vrushtipatel1307/pathreview/commit/d63fde89409a93acd91281d9674814de49ac31ad

**Reproduction summary:**
I reproduced the gap by demonstration, not just inspection:

1. Ran the existing suite as a baseline — `python -m pytest tests/unit/test_prompt_templates.py -q` → **37 passed**.
2. Changed a single word in the `skills_feedback` v1 template in [rag/generator/prompt_templates.py](rag/generator/prompt_templates.py) ("Analyze" → "Examine").
3. Re-ran the suite → **37 passed again**. The wording change was not caught by any test.
4. Reverted the template change.

Root cause of the gap: the one test that claims to be a snapshot, [test_template_snapshot_content_hash](tests/unit/test_prompt_templates.py#L175-L188), computes an MD5 of the concatenated templates but only asserts `len(content_hash) == 32` — it never compares against a stored expected hash. Combined with the other tests (presence, placeholder, and length checks only), template bodies can drift silently. This is exactly the gap described in issue #37.

**PLAN.md link:** ./PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
No blockers. The next step is to add deterministic snapshot coverage for each prompt template/version and make intentional prompt edits require an explicit snapshot update.