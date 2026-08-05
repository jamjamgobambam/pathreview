## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/106

**Issue title:** Shared test fixture for a sample user profile is missing from `tests/fixtures/`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Several integration tests depend on a fixture file,
`tests/fixtures/sample_profiles/basic_profile.json`, that no longer exists
in the repository — it was deleted at some point, and the tests that
reference it are currently being skipped rather than run. This means test
coverage for whatever functionality relies on that fixture is effectively
absent right now. The fix is to recreate the fixture as a realistic sample
user profile containing a GitHub username, a resume, and two repositories,
matching whatever shape the skipped tests expect it to have. Once restored,
those integration tests should un-skip and run against real (if synthetic)
profile data, closing the coverage gap.

**Branch name:** fix/106-restore-sample-profile-fixture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/krish-batra/pathreview/commit/8b724fb78d4b4f2d9f169303cf70aa73799a756e

**Reproduction summary:** The issue could not be reproduced as literally
described — the fixture `tests/fixtures/sample_profiles/basic_profile.json`
never existed in git history (confirmed via `git log --all` and a full-history
`git grep`) and `tests/integration/` was empty, so no tests were actually being
skipped. This is a seeded/synthetic practice issue, so the work was net-new
authoring of the fixture plus a matching integration test, not restoration of a
deleted file.

**PLAN.md link:** [PLAN.md](PLAN.md)

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:** None blocking. Note for reviewers: PR #134
attempted a different (conftest.py Python fixture) approach that never created
the JSON path the issue names and stalled unmerged; this branch delivers the
literal JSON fixture instead. The repo also has 53 pre-existing unit-test
failures unrelated to this change (all in `tests/unit/`); the 3 new integration
tests pass and the full suite is 378 passed / 53 failed. `make check` is
likewise pre-existing red (182 ruff, 52 black, 5 mypy findings), all in
unchanged code — this branch modifies zero existing files and its new files
contribute nothing to those counts (verified). See the PR description for the
per-issue breakdown of the baseline.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
The fix itself (fixture + integration test) was completed in Week 8, ahead
of schedule. This week I focused on pre-PR verification: ran `make check`
and `make test-unit` to establish the pre-existing failure baseline, and
confirmed via `git diff --stat main...HEAD` that my branch adds 4 files and
modifies zero existing files, so all 182 ruff errors, 52 black reformats,
5 mypy errors, and 53 unit test failures are pre-existing and unaffected
by this branch. I also mapped the 53 unit failures to their root causes
(#158: 13, #159: 1, unattributed pre-existing bugs: 39, #163: 0) with
verified error signatures rather than guessing from filenames.

**Next steps:**
Self-review against docs/CONTRIBUTING.md, draft the PR description with
the baseline documentation included, get a peer/mentor to review the draft
PR, then finalize and submit.

**Blockers:**
None.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/467 (moved from draft to ready for review)

**Branch:** fix/106-restore-sample-profile-fixture

**What I built:**
Restored the sample profile fixture (tests/fixtures/sample_profiles/basic_profile.json)
requested in #106 and added an integration test (tests/integration/test_profile_fixture_loading.py)
that constructs real Profile + IngestedSource ORM objects from it and verifies the relationship
graph is wired correctly.

**Tests added or updated:**
tests/integration/test_profile_fixture_loading.py — 3 new tests
(test_fixture_file_exists, test_profile_fields_populated, test_repos_map_to_two_ingested_sources),
all passing.

**Self-review confirmation:**
- [x] make check passes — passes for all files this branch adds/touches;
  182 pre-existing ruff errors / 52 black reformats / 5 mypy errors are
  unrelated and unaffected (0 contribution from this branch, verified
  via git diff --stat main...HEAD). Full breakdown in the PR.
- [x] make test-unit passes — 3 new integration tests pass; 53 pre-existing
  unit failures are unrelated to this branch (0 introduced). Per-issue
  breakdown in the PR.

**Draft PR feedback received from:**
Posted in [course Slack channel] for review; no response received before
submission deadline.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review has come in. Checked PR #467 directly (state: open, 0 comments,
0 reviews submitted) — this matches the course's Summer 2026 notice that
reviewer feedback isn't a feature this term.

**How you responded:**
N/A — no feedback received.

---

### Reflection

**What was harder than you expected?**
Trusting the issue description less than I wanted to. Issue #106 read like
a normal "a file got deleted, put it back" ticket, and my first instinct
was to just start writing the JSON. It wasn't until I actually ran `git log
--all` and a full-history `git grep` that I found the fixture had never
existed — the issue was seeded, not a real regression. That was harder than
the actual coding: it required stopping mid-flow, going back to first
principles, and being okay with the fact that "reproduce the issue" for
Week 8 meant proving there was nothing to reproduce, which isn't what the
assignment template assumed I'd find.

**What did you learn about working in a large codebase?**
That the codebase's own history is a source of truth I hadn't thought to
consult before writing code. On my own projects I don't need `git log --all
--diff-filter=D` to know whether something used to exist — I remember. In
someone else's repo, especially one with 66 curated issues and prior
contributor attempts (like PR #134, which tried a different approach and
stalled), the git history and the open PRs are basically a paper trail I
should read before I touch anything. I also learned that "passes all
checks" doesn't mean the same thing in a large repo as it does in a fresh
project — `main` itself had 182 lint errors and 53 failing tests before I
touched anything, and figuring out how to prove my 4 new files contributed
zero to that was its own small skill.

**How did AI tools help — and where did they fall short?**
Claude Code was strongest at exactly the kind of investigation I was
initially reluctant to do — running the full-history git searches, reading
the Profile/IngestedSource models to make sure my fixture used real column
names instead of invented ones, and catching a mypy error I would have
committed past. It also caught its own gap once, flagging that it hadn't
independently re-verified a number it was about to cite (the 378/53 test
split) after a later change — that's the kind of self-check I want to
build the habit of doing myself, not just relying on it to do.

Where it fell short: it can't tell me whether an issue is "real" without
being asked to check — it took an explicit prompt to go dig into git
history rather than just accepting the issue text and building the fixture
I initially assumed was needed. The judgment calls (whether to rewrite
commit history, which of two valid fixture designs to pick, whether to
present the "no bug to reproduce" finding honestly instead of chasing the
literal Week 8 template) were mine to make; AI could lay out the tradeoffs
clearly, but it wasn't going to decide "be honest here" for me.

**What would you do differently if you started over?**
I'd run the git-history check in Week 7, during issue selection, instead of
Week 8. If I'd known upfront that #106 was synthetic, I might have picked a
different issue, or at least gone in with the right framing from day one
instead of writing a Week 7 problem summary that took the issue's premise
at face value. I'd also set up my environment outside OneDrive from the
very first command, instead of hitting the same file-locking problem I'd
already learned about in a previous project.

**What are you most proud of from this module?**
Not the fixture or the test — the PR description. I documented that the
issue's premise didn't hold up, that a prior contributor's PR took a
different approach and stalled, and exactly which of the repo's 53
pre-existing test failures were and weren't mine, with real error
signatures instead of guesses. That's the part I'd want a reviewer or
future me to actually read.