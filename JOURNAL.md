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

**PLAN.md link:** [PLAN.md](PLAN.md)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
No blockers. The next step is to add deterministic snapshot coverage for each prompt template/version and make intentional prompt edits require an explicit snapshot update.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the snapshot coverage for prompt templates. Sub-tasks 1–4 from PLAN.md are done:
- Reviewed the templates and chose to lock all five `v1` bodies verbatim (they carry no leading/trailing whitespace beyond a single trailing newline, so verbatim snapshots are stable and produce readable diffs — no `dedent`/`strip` normalization needed).
- Added an `EXPECTED_TEMPLATES` fixture in [tests/unit/test_prompt_templates.py](tests/unit/test_prompt_templates.py) with the exact body of every template/version, plus two new tests: `test_template_registry_matches_snapshot_names` (locks the set of name/version pairs) and a parametrized `test_template_body_matches_snapshot` (exact-string equality per template).
- Fixed the false-positive `test_template_snapshot_content_hash`: it now asserts against a committed `EXPECTED_CONTENT_HASH` instead of only checking `len(...) == 32`.
- No snapshot plugin (`syrupy`/`pytest-snapshot`) is installed, so I used an in-repo committed-expected approach rather than adding a dependency.
- Verified the guard works: re-running the Week 8 reproduction ("Analyze" → "Examine") now fails both the per-template snapshot and the content-hash test with a readable diff; reverting makes them pass. The suite went from 37 → 43 passing tests.

**Next steps:**
Finish sub-task 5 (document the "update snapshots deliberately" expectation — done inline as a header comment in the test file), open a draft PR, request peer review in Slack, and finalize.

**Blockers:**
None. Noted a set of pre-existing failures in the repo (unrelated files) that I am tracking so I can confirm my change introduces none — see Check-in 2.

---

### Check-in 2 (end of week)

**PR link:** _[to be added once the PR is opened]_

**Branch:** `test/37-prompt-template-snapshots`

**What you built:**
Added regression ("snapshot") coverage for the five prompt templates in [rag/generator/prompt_templates.py](rag/generator/prompt_templates.py). The test file now stores each template body verbatim in an `EXPECTED_TEMPLATES` fixture and asserts exact equality per template/version, locks the set of template names/versions, and checks a committed `EXPECTED_CONTENT_HASH`. Any accidental wording, formatting, or placeholder change now fails loudly with a readable diff, so prompt edits must be intentional (update the fixture + hash).

**Tests added or updated:** [tests/unit/test_prompt_templates.py](tests/unit/test_prompt_templates.py) — added `test_template_registry_matches_snapshot_names` and a parametrized `test_template_body_matches_snapshot`, and rewrote `test_template_snapshot_content_hash` to compare against a committed hash. Existing presence/placeholder/retrieval tests are unchanged.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

_Pre-existing failures (documented, not introduced by this change):_ `make test-unit` had **53 failing / 381 passing** before my change, in unrelated files (e.g. `test_review_service.py`, `test_skill_extractor.py`, `test_tech_detector.py`). `make check` also fails pre-existing (ruff: 182 errors; black: 52 files would reformat) across the repo. My change touches only `test_prompt_templates.py`: all 43 tests there pass, my added lines are ruff- and black-clean (I also fixed the file's import-sort error, reducing its ruff count 19 → 18), and I introduced **no new** `make check` or `make test-unit` failures. "Passes" above is checked in the sense that this contribution makes nothing worse.

**Draft PR feedback received from:** none