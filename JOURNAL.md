# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/37

**Issue title:** Add snapshot tests for prompt templates to catch accidental changes

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview uses prompt templates to generate its reviews, and even small wording changes can affect the results. Right now, those changes can happen without being noticed or requiring the template version to be updated. This issue adds tests that detect changes to the templates and require a version bump, making edits intentional and easier to review.

The work will be done in tests/unit/test_prompt_templates.py and will cover the prompt templates in the rag module.

**Selection notes — "Is this right for me?" checklist:**

*Part 1 — Understanding the issue*
- **In my own words:** Prompt templates are the core of the reviews this project produces, so a test should exist that fails if a template's text changes without bumping its version — that way a change can't slip in silently.
- **Part affected:** The issue affects the `rag` module's prompt templates (`rag/generator/prompt_templates.py`); my test guards them and lives in `tests/unit/test_prompt_templates.py`.
- **What "done" looks like (before → after):** Before the fix, a developer can edit a template and the whole test suite still passes, so the change ships unnoticed. After the fix, editing a template without a version bump makes the snapshot test fail, forcing the developer to either revert or consciously bump the version and update the stored snapshot.

*Part 2 — Tier fit*
- This is my first contribution to a large open-source codebase, so I chose a Tier 1 issue. #37 is labeled `tier-1` and `good first issue`, which is the recommended starting point.

*Part 3 — Codebase readiness*
- **Found the code:** `PROMPT_TEMPLATES` is a two-level nested dict — outer keys are the 5 template names, inner keys are version labels (`"v1"`) mapping to the template text; `get_template(name, version="v1")` reads from it.
- **Rough plan:** The existing `test_template_snapshot_content_hash` already computes an MD5 hash of all template content but never asserts it against a known value. I'll store an expected hash (ideally per template) in the test and assert the current hash matches it, so any content change fails the test and a version bump + snapshot update is the deliberate escape hatch.
- **Read the test file:** Read `test_all_5_templates_exist` end-to-end — it builds a set of the 5 expected names and asserts it equals `set(PROMPT_TEMPLATES.keys())`, catching both missing and extra templates. These tests are fixture-free and assertion-based.

*Part 4 — Scope and time*
- **Claims:** 3 students in the ledger and ~13 claim comments on the issue. Claims are non-exclusive and grading is on my own artifacts, and I've already done the readiness work for this issue, so I'm comfortable staying on #37.
- **Time:** Estimated at 3–5 hours (Tier 1 range), and I'm confident I can complete it within Weeks 8–9.
- **Blockers:** No "blocked by" references or dependencies on other unresolved issues; the code it touches already exists and is self-contained.

**Branch name:** test/37-prompt-template-snapshot-tests

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/jundaBu/pathreview/commit/96476f97f542f71e1bdbc3b127a64d41aeebb350

**Reproduction summary:**
I edited the `skills_feedback` template text in `rag/generator/prompt_templates.py` and ran `.venv/bin/pytest tests/unit/test_prompt_templates.py` — all 37 tests still PASSED, including `test_template_snapshot_content_hash`. That "snapshot" test only asserts the hash is a 32-char string (always true for any MD5) and never compares it to a stored value, so template wording can change silently without any test catching it or requiring a version bump. I restored the template afterward and documented the exact gap as a `REPRODUCTION — issue #37` comment on the no-op test.

**PLAN.md link:** [PLAN.md](PLAN.md)

**Blockers or open questions:**
- Confirm with maintainers whether the snapshot should assert *exact* text hashes (trailing-whitespace-sensitive) vs. normalized text.
- Confirm snapshot storage preference: inline `EXPECTED_TEMPLATE_HASHES` dict vs. a separate JSON file.
- Ensure stored hashes reflect the post-`black`/`ruff` template text so the `make check` formatter pass doesn't cause snapshot drift.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

All five sub-tasks from [PLAN.md](PLAN.md) are implemented, in `tests/unit/test_prompt_templates.py` only — no production code or template text changed:

1. **Stored snapshot added.** `EXPECTED_TEMPLATE_HASHES`, keyed by `(template name, version)`. I went with the inline dict over a separate JSON file so the snapshot and the assertion that reads it stay reviewable in one diff.
2. **The no-op is now a real assertion.** `test_template_snapshot_content_hash` hashes each template and compares it to its stored value. The failure message names the template that changed and points at the escape hatch.
3. **Coverage check added.** `test_snapshot_covers_exactly_the_current_templates` asserts set equality between `PROMPT_TEMPLATES` and the snapshot keys, so a template/version added or removed without a snapshot update fails, with separate messages for missing vs. orphaned entries.
4. **Escape hatch documented** in a comment block above the snapshot, including the one-liner that prints a hash for a new version.
5. **Verified** by temporarily editing the templates and re-running the suite (details below).

**Two deliberate deviations from PLAN.md:**

- **Dropped the combined-hash assertion.** Per-template hashes strictly subsume it: they detect every change the combined hash would, but also name *which* template changed. Keeping both would also break PLAN.md's own edge case "a new version added deliberately with its hash must PASS", since a combined hash would need a second, redundant update.
- **Added a third test not in PLAN.md** — `test_snapshot_hash_detects_template_edits` — asserting the hash is content-sensitive for both a reworded and a whitespace-only edit. This is the regression guard for issue #37 itself: it fails if the suite ever drifts back toward a hash check that passes regardless of template content.

**Edge-case verification.** Each scenario was produced by temporarily editing `rag/generator/prompt_templates.py` (and, for the v2 case, the snapshot too), running the suite, then restoring:

| Scenario | Expected | Result |
| --- | --- | --- |
| Template reworded, no version bump (the issue #37 case) | FAIL | FAIL — 1 test, message names `skills_feedback` v1 |
| Whitespace-only edit (added a trailing space) | FAIL | FAIL — 1 test |
| New template added with no snapshot entry | FAIL | FAIL — 3 tests |
| Template removed, leaving an orphaned snapshot entry | FAIL | FAIL — 6 tests |
| `v2` added deliberately *with* its hash | PASS | PASS — 39 tests |
| Template keys reordered, no text change | PASS | PASS — 39 tests |

**Next steps:** open the PR with the template filled in, request peer feedback in Slack, and address anything that comes back.

**Blockers:** none. The three Week 8 open questions are resolved:
- *Exact vs. normalized text* — went with exact/strict matching, since trailing whitespace reaches the model too; the reasoning is in the `_hash_template_text` docstring so a maintainer can push back easily.
- *Snapshot storage* — inline dict (see above).
- *Formatter drift* — verified empirically: `black` reformats the `PROMPT_TEMPLATES` dict layout but not the string contents, so all five hashes are byte-identical before and after a `black` run. The snapshot will not drift when someone formats that file.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/776

**Branch:** `test/37-prompt-template-snapshot-tests`

**What you built:**
`test_template_snapshot_content_hash` used to compute an MD5 of all prompt template content and then assert only that the digest was a 32-character string — both assertions true for *any* MD5, so a reworded prompt shipped silently. It now hashes each template individually and compares against a committed `EXPECTED_TEMPLATE_HASHES` snapshot, so a template edit fails the suite until it is either reverted or shipped deliberately as a new version key with its hash added. Two supporting tests cover snapshot/template set drift and assert the hash is content-sensitive.

**Tests added or updated:** all in `tests/unit/test_prompt_templates.py` — rewrote `test_template_snapshot_content_hash` (per-template snapshot assertions), added `test_snapshot_covers_exactly_the_current_templates` (no missing or orphaned snapshot entries) and `test_snapshot_hash_detects_template_edits` (hash is content-sensitive; guards against regressing to a no-op). File goes from 37 to 39 tests, all passing.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Checked per the assignment's rule for a codebase with documented pre-existing failures — "passes" means my changes introduce no new failures. Exact measurements:

| Command | Before my change | After my change |
| --- | --- | --- |
| `make test-unit` | 53 failed, 375 passed | 53 failed, 377 passed — *identical* failure set (verified with `comm`), +2 from my new tests |
| `make lint` (ruff) | 176 errors, aborts `make check` | 176 errors — unchanged |
| `make typecheck` (mypy) | 5 errors | 5 errors — unchanged (it does not cover `tests/`) |
| `black --check .` | 51 files would reformat | 51 files — unchanged; my file is `black`-clean |

`make check` fails at its first step (`make lint`) on 176 pre-existing ruff errors across the repo, so it never reaches `black`/`mypy`. None of the 53 pre-existing unit-test failures are in `test_prompt_templates.py`. The pre-commit hooks also fail on pre-existing debt in this file (13 ruff, 36 mypy `no-untyped-def`) — all in *other* test methods; I annotated the three methods I own, which takes mypy from 37 to 36, so I add none and remove one. Fixing the rest was left out of scope to keep the diff focused on #37.

**Draft PR feedback received from:** none
