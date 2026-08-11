## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/106
**Issue title:** Restore deleted basic_profile.json fixture
**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Multiple integration tests in the test suite are currently skipped because a required test fixture file, `tests/fixtures/sample_profiles/basic_profile.json`, was deleted from the repository. Without this file, integration tests that depend on a baseline user profile cannot execute properly. Restoring this fixture with a realistic sample portfolio containing a GitHub username, resume text, and two repository links will allow those skipped integration tests to run cleanly and pass.

**Branch name:** fix/106-restore-basic-profile-fixture
**Setup confirmation:** [x] App runs locally at localhost:5173
**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:**
https://github.com/ChristopherPaladines/pathreview/commit/4f1543b

**Reproduction summary:**
I reproduced the issue by confirming the file `tests/fixtures/sample_profiles/basic_profile.json` was missing from the repository. I observed that while no tests failed (because the tests themselves are also missing), the issue description `G-01` and the project structure clearly indicate this file is a required test fixture.

**PLAN.md link:**
https://github.com/ChristopherPaladines/pathreview/blob/fix/106-restore-basic-profile-fixture/PLAN.md

**Walkthrough video (recommended):** Not recorded (recommended, not graded).

**Blockers or open questions:**
The integration tests that are supposed to use this fixture are not present in the repository. While restoring the fixture is the correct fix for this issue, the ultimate validation would require finding or rewriting those tests.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Restored `tests/fixtures/sample_profiles/basic_profile.json` and enriched it into a realistic portfolio: a GitHub username, a resume with recognizable sections, and two differentiated repositories (a Python repo with tests + CI, and a TypeScript repo without) shaped with the GitHub-API fields that `RepoAnalyzer` actually reads. Wrote `tests/unit/test_basic_profile_fixture.py` (5 tests) that loads the fixture and feeds it through the real `ResumeParser` and `RepoAnalyzer`, asserting the expected sections and repo signals. All 5 pass; the new file is `ruff`/`black`/`mypy` clean.

**Next steps:**
Open the PR, request peer feedback, and finalize the submission.

**Blockers:**
None. Noted pre-existing, unrelated failures in the codebase (see Check-in 2) that my change does not affect.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ChristopherPaladines/pathreview/pull/1

**Branch:** `fix/106-restore-basic-profile-fixture`

**What you built:**
Restored the deleted `basic_profile.json` fixture with a realistic sample portfolio and added a unit test that loads it and runs it through the real `ResumeParser` and `RepoAnalyzer`, verifying the fixture is valid/usable and guarding it against future deletion.

**Tests added or updated:**
Added `tests/unit/test_basic_profile_fixture.py` (5 tests): fixture loads, required top-level keys present, resume text parses into detected sections, and each repository is analyzed with the expected language / tests / CI signals.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Codebase has documented pre-existing failures — baseline `make test-unit`: 53 failed / 375 passed; `make lint`: 182 errors. After my change: 53 failed / 380 passed = +5 passing, 0 new failures. My new file passes ruff/black/mypy. Per the Week 9 guidance, "passes" here means my change introduces no new failures.)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback was received. As of 2026-08-11 the PR
(https://github.com/ChristopherPaladines/pathreview/pull/1, opened 2026-08-05) is
still open with 0 reviews, 0 issue comments, and 0 inline review comments. No CI
checks ran against the branch either, so there was no automated feedback to respond
to. This matches the course guidance that reviewer feedback is not a feature of the
Summer 2026 cohort. I also received no peer or mentor feedback on the draft PR in
Week 9.

**How you responded:**
No changes were warranted, since no feedback arrived. In place of external review I
did a final self-review of the branch: I verified the pushed branch still contains
both `tests/fixtures/sample_profiles/basic_profile.json` and
`tests/unit/test_basic_profile_fixture.py`, and confirmed the local `HEAD` matches
`origin/fix/106-restore-basic-profile-fixture` with nothing unpushed. That check
caught a discrepancy worth recording: the test file had been deleted from my local
working tree without the deletion being committed, so `git status` showed it as `D`
while GitHub still had it. The commit and the PR were never affected, and
`git restore` brought the local copy back in sync.

---

### Reflection

**What was harder than you expected?**
Git and GitHub themselves, not the code. I came in thinking a fork and a clone were
roughly the same thing. I assumed a fork was just the user's saved copy of a project,
and a clone was the edited version of that code inside git. I couldn't have told you
which copy lived where, or that a fork records where the original came from. Pull
requests were the same kind of blur: I knew a PR was something you opened, but not
what it was comparing against, and definitely not that it is the actual collaboration
surface, the place a maintainer reviews your work and where you are expected to be
reachable and responsive. Opening one in Week 9 is what made that click.

The most concrete version of the confusion hit me in Week 10. `git status` showed my
test file as deleted and I thought I had lost the work. It had been committed and
pushed days earlier and was sitting on GitHub the entire time. What had been deleted
was only my local copy. I had not understood that the working tree, the commit, and
the remote branch are three separate states that can disagree with each other, and
that `git status` is the thing that shows you the disagreement. Staging, committing,
and pushing felt like they should be one action. They are not, and not knowing that
made the whole process feel less predictable than it actually is.

**What did you learn about working in a large codebase?**
In my own projects I know where everything is because I put it there. In PathReview I
had to work out the structure before I could make a one file change. Restoring a
single JSON fixture meant tracing how data actually moves through the project: which
module reads the file, what shape that module expects, and what it produces
downstream. Putting a file back at the correct path was not enough. I had to
understand what `ResumeParser` and `RepoAnalyzer` do with it, or the fixture would
have been valid JSON and still useless to the tests it exists to serve. That meant
digging through several directories that had nothing obviously to do with my issue.

The other thing I did not expect was how much of the difficulty was infrastructure
rather than code. A project this size comes with an entire layer I had never touched.
I had to learn what a CI pipeline is and why a codebase this size depends on one, and
what Docker is and why the application would not run locally without it. You never
hit those building a small project alone, because you never need them. Understanding
why containerization makes sense at this scale, so that every contributor gets the
same environment instead of fighting their own machine, changed how I think about
setting up projects. It is also why I now want to learn Kubernetes.

Leaving the rest of the project alone was harder than I expected. The branch had 53
pre existing test failures and 182 lint errors, and it was humbling to see that my
contribution added 5 passing tests and left all 53 of those failures exactly where
they were. While I was still stuck on my own issue, I kept asking myself whether I
should be fixing the things around it instead. Staying in scope was correct, but I
felt it as a limit on my ability more than as discipline: a Tier 1 issue took me long
enough that I did not want to reach for anything harder until I understood the basics
properly. What I take from it is that in a codebase this size, a change has to be
small enough for someone else to review and guarded well enough that it does not
create new problems downstream.

**How did AI tools help, and where did they fall short?**
AI was most useful as a tutor for vocabulary and concepts. I asked a lot of questions
I would have been slow to answer on my own: what a CI pipeline is and why a project
this size needs one, what Docker is, why the application would not start locally
without it, and what containerization actually buys you at this scale. The answers
were condensed, efficient, and correct, and they saved me hours of searching for them
piecemeal.

Where it fell short is that a correct explanation is not the same as understanding.
The logic did not click until I had to do the thing myself inside the project.
Reading about how the parsers relate to one another did not stick. Tracing what
`ResumeParser` actually did with my fixture did. Looking back, the parts I struggled
with feel smaller and less intimidating now, and that is because I did them, not
because they were explained well to me.

The clearest concrete example came in Week 10. My test file showed as deleted
locally, and I was told it was still safely committed and pushed to my branch. The
explanation was correct, but I did not accept it until I opened the file's URL on the
branch and saw it for myself. That instinct turned out to be worth developing. AI can
tell you what your repository state probably is, but it does not know it the way
`git status` and the branch on GitHub do, and confirming a claim against the actual
source is a habit I want to keep.

The larger limitation is that AI assistance assumes prior knowledge. It works best
when you already understand roughly how systems fit together, because then it removes
busywork and lets you spend your attention on design and the harder technical
decisions. Without that foundation it made learning harder rather than easier,
because I could not always tell a genuinely good answer from one I was misreading.
Contributing to a codebase this size felt like stepping into a fully finished house
and being asked to locate and fix a problem in something I had never built or lived
in. AI could describe any room I asked about. It could not give me the experience of
having built one.

**What would you do differently if you started over?**
I would verify the issue before accepting how it was described. Issue #106 said that
multiple integration tests were being skipped because the fixture was missing, and I
repeated that in my Week 7 problem summary before I had looked. When I actually
reproduced it in Week 8, I found that `tests/integration/` contains nothing but an
`__init__.py`, and that no code in the project reads `basic_profile.json` at all. The
only other mention of the fixture directory is a comment inside an unimplemented stub
script. So the tests I was supposedly unblocking did not exist. The fix was still
correct, but I could not validate it the way the issue implied, and I would rather
have known that before claiming the issue than after.

That changes how I would select an issue next time. I would check that a fix can
actually be proven to work before committing to it, rather than assuming the issue
text is accurate. Maintainers write issues from memory, and repositories drift.

I would also be present after submitting. I treated opening the pull request as the
finish line, and it is not. A PR is where collaboration starts, and being reachable
to answer questions and make requested changes is part of contributing. No review
came in this term, so it cost me nothing, but I would not want that to be a habit I
only avoided by luck. Related to that, I opened my pull request against my own fork
rather than the original repository, which meant there was no maintainer on the other
end even in principle. I understand that distinction now in a way I did not when I
opened it.

**What are you most proud of from this module?**
That I finished something inside a codebase that genuinely intimidated me, and did
not quietly make the job easier for myself along the way. What I shipped is small:
one restored fixture and five tests. But I did not widen the scope to feel more
accomplished, and I left the 53 failing tests and 182 lint errors sitting next to my
work alone, even during the stretch where staying inside my issue felt more like
avoidance than discipline. Small and correct turned out to be the harder thing to do.

The part I did not expect to value as much is that I got to see how developers work
on a real project instead of a teaching example: how issues get written, how fixtures
and tests exist to support code other people depend on, and why all the
infrastructure around the code is there. Breaking those concepts down with classmates
and talking them through in a mentor and student setting is what made them stick.
Reading explanations on my own did not do that.
