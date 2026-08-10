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

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in. PR #776 is still open with no comments from anyone but me, no requested changes, and no CI checks reporting on it. I asked six specific questions in the "Notes for Reviewers" section, covering exact vs. normalized whitespace matching, MD5 vs. SHA-256, inline snapshot vs. a JSON file, and whether the course artifacts should be dropped from the diff. They were meant to give a reviewer easy entry points. None were answered.

**How you responded:**
Nothing to respond to, so I did the one thing that was still in my control: I re-read my own PR as if I were the reviewer. That caught a real problem. My PR body claimed the change was "All in `tests/unit/test_prompt_templates.py`", but the actual diff against `upstream/main` was three files. My working branch also carried `JOURNAL.md` and `PLAN.md` from Weeks 7 through 9, plus some `black` reflowing of pre-existing assertions from my Week 8 commit. The description didn't match the diff. I corrected the body to describe all three files, flagged the reformatting, and offered to re-open from a branch containing only the test change. I also fixed the PR title, which GitHub had auto-generated from my branch name as "Test/37 prompt template snapshot tests" instead of the Conventional Commits format this repo requires.

---

### Reflection

**What was harder than you expected?**

Two things, and neither was writing the test.

The first was that the codebase was never green. I assumed a baseline of "everything passes, so if something fails, I broke it." That assumption was wrong on arrival: `make test-unit` had 53 failing tests, `make lint` had 176 ruff errors, `make check` aborted at its first step and never even reached the type checker, and `black` wanted to rewrite 51 files I hadn't touched. That meant I couldn't use "did it pass?" as my signal at all. I had to capture a baseline failure list before writing a line of code and diff my results against it with `comm`, because the failure *counts* could stay the same while the actual failures swapped underneath me. There were smaller traps inside that: the pre-commit `mypy` hook checks `tests/`, but `make typecheck` doesn't, so my two new test methods added two errors that `make typecheck` would never have shown me. I only found that because a commit got blocked. Every `.py` commit on this branch needed `--no-verify`, which felt wrong to type until I confirmed the hooks were failing on debt that predated me.

The second was making design decisions with nobody to ask. MD5 or SHA-256 (the rest of the codebase uses SHA-256, but the test I was fixing used MD5). Inline dict or a separate JSON file. Whitespace-exact or normalized. Per-template hashes or one combined hash. Every one of these is defensible either way, and the issue thread didn't answer any of them. I ended up making the call, writing down *why* in the code, and surfacing the reversible ones in the PR so a maintainer could overrule me cheaply. That's the part I felt least sure about, and still do, not because I think the choices are wrong but because "defensible" isn't the same as "what this project actually wants."

**What did you learn about working in a large codebase?**

That reading the code is not the same as knowing the state of the repo, and only one of those is written down. Nothing in `README.md` or `docs/CONTRIBUTING.md` told me the suite was failing, that `make check` dies before the type checker, or that pre-commit covers directories the Makefile skips. I found all of it by running things and looking. In my own projects I know that context because I created it; here it had to be measured.

I also learned that scope discipline is a real skill and it's uncomfortable. `test_prompt_templates.py` has 13 ruff errors and 36 mypy errors sitting right next to my code, and I could have fixed them in twenty minutes. I deliberately didn't, because they're in test methods unrelated to #37 and cleaning them would have buried a focused fix under noise in ~10 other methods. Leaving visible mess alone felt like doing a worse job; I think it was actually the right call, and I offered a follow-up `chore` PR instead. The related lesson is that a diff is a communication tool, not just a set of changes. That's exactly what I got wrong by shipping a body that described one file when the diff had three.

The last thing: in someone else's production code, the existing tests are the specification. I couldn't ask the author what the prompt templates were *supposed* to say, so "correct" had to mean "unchanged unless deliberately versioned." That reframing is what made the fix straightforward once I saw it.

**How did AI tools help — and where did they fall short?**

Most useful for the mechanical and the exploratory: finding where `PROMPT_TEMPLATES` was used, generating the baseline comparison commands, drafting the snapshot test structure, and writing up the PR. It compressed hours of navigation into minutes.

Where it fell short is that its output looked right more often than it *was* right, and the difference only showed up when something was actually run. The clearest example was in my own fix. The regression-guard test, the one that proves the hash is content-sensitive, was originally written to edit the template by replacing the literal phrase `"Analyze the skills"`. It passed. It looked completely reasonable in review. But when I ran the verification scenario where a developer rewords that exact phrase, *two* tests failed instead of one: my guard broke as collateral damage, because the wording it depended on had changed. A test that breaks whenever the thing it's guarding legitimately changes is a bad test, and reading the code hadn't revealed that. Running the scenario did. I rewrote it to build edits by appending instead of replacing known text, so it no longer depends on any particular wording.

That pattern repeated. The claim that `black` wouldn't disturb my stored hashes was plausible reasoning, but I only trusted it after copying the file, running `black` on the copy, and confirming all five hashes were byte-identical. The lesson I'm taking is that AI shortens the distance to a candidate answer, but the verification is still mine to do, and the bugs that survive are specifically the ones that look fine on the page.

**What would you do differently if you started over?**

Open the PR far earlier. That's the big one. I opened in Week 9 with the work essentially finished, which meant "get peer or mentor feedback and iterate" had no time to happen, and it didn't. A rough draft PR in Week 8, right after the reproduction commit, would have put my four open design questions in front of someone while they could still change the design cheaply. Instead I answered them all myself and shipped. The iteration week had nothing to iterate on, and that's a scheduling mistake I made, not bad luck.

I'd also pick a less-claimed issue. #37 had around 13 claim comments and 3 students in the cohort ledger. I stayed because I'd already done the readiness work and grading is on my own artifacts, which was reasonable at the time, but a maintainer looking at a dogpiled `good first issue` has little reason to engage with any one PR. A quieter issue would probably have gotten me the review I actually wanted, which was worth more to me than the safety of a Tier 1.

Smaller one: I'd keep `JOURNAL.md` and `PLAN.md` off the contribution branch from the start, so the PR diff was only the fix.

**What are you most proud of from this module?**

That I finished a real contribution to someone else's production codebase. Four weeks ago I hadn't done that, and the honest reason was that a repo this size felt like something you needed permission to touch. The work itself turned out to be ordinary: read the code, reproduce the problem, make a small careful change, prove it does what you say. What changed isn't a skill so much as the sense that the door is open. The PR may sit unreviewed, and it might get closed; I'd still have gone from "I don't contribute to projects like this" to having done it end to end.
