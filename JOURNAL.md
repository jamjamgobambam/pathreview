# Development Journal — PathReview

My running record of progress throughout Module 3. A new section is added each week.

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/72

**Issue title:** Add a bias audit report that runs over a sample of stored reviews

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
PathReview's safety layer includes a bias detector (`safety/bias_detector.py`) that
flags potentially biased language in generated reviews, but there is currently no way
to measure how well it actually performs across real data. Nothing today samples stored
reviews and evaluates the detector's accuracy, so blind spots — reviews it wrongly flags
(false positives) or biased content it misses (false negatives) — go unmeasured. This
issue asks for an offline audit script (`scripts/audit_bias.py`) that samples ~100 stored
reviews, runs them through the bias detector with detailed logging, and produces a report
of false positive/negative rates broken down by demographic signal. A successful fix gives
maintainers concrete, reproducible evidence of the detector's real-world behavior so its
thresholds can be tuned with data instead of guesswork.

**Branch name:** fix/72-bias-audit-report

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/LittlePixels/pathreview/commit/f047af241a5cb6732cdcf0c8e54216a82b7fc2cb

**Reproduction summary:**
Since #72 is a missing-capability issue, I reproduced the gap rather than a crash: I ran the existing `BiasDetector` over stored-review text via a throwaway script ([scripts/repro_bias_audit.py](scripts/repro_bias_audit.py)), feeding it benign snippets from the seeded reviews and a few crafted biased phrasings. The benign text was correctly unflagged (0/3 false positives), but all three crafted biased strings went undetected (3/3 false negatives) — and crucially there is no audit script, no FP/FN report, and `detect_bias` is never even called in the pipeline ([review_service.py:366](core/services/review_service.py#L366)), so these blind spots are completely unmeasured today.

**PLAN.md link:** [PLAN.md](PLAN.md)

**Walkthrough video (recommended):** [not recorded]

**Blockers or open questions:**
The `Profile` model has no demographic fields, so the issue's requested "breakdown by demographic signal" can't come from profile attributes — I plan to derive signals from a labeled fixture set of review text instead. Open question for Week 9: whether the maintainers expect the audit to run against the live DB, a fixture set, or both.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I resolved the Week 8 open question by splitting the design in two: the ground-truth FP/FN measurement runs over a labeled fixture set, and an optional live scan runs over stored DB reviews for a flag rate. From PLAN.md, the Understand/Map/Inputs sub-tasks are done, and the core scoring module (`safety/bias_audit.py`) is implemented — text extraction from a review's `sections` JSON, and a `ConfusionMatrix` computing precision/recall and FP/FN rates overall and per demographic signal. I also captured the repo's pre-existing baseline first: `make test-unit` already shows 52 failed / 31 errors on `main` (chunker SSL errors + 9 `test_bias_detector` failures that are the exact blind spots this audit measures), and `make check` is red repo-wide (ruff 182, black 52 files, mypy 5).

**Next steps:**
Build the labeled fixture set, wire up the `scripts/audit_bias.py` CLI (console + JSON report, optional `--scan-db`), and write unit tests for the scoring core. Then confirm my changes introduce no new failures against the baseline, and open the PR.

**Blockers:**
None. (Peer review happens in Slack; I'll request a draft-PR review there.)

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/583

**Branch:** `fix/72-bias-audit-report`

**What you built:**
An offline bias audit for the `BiasDetector`. `safety/bias_audit.py` scores the detector against a labeled sample set and reports false-positive / false-negative rates overall and by demographic signal (education, age, origin); `scripts/audit_bias.py` is a thin CLI that prints the report, writes `bias_audit_report.json`, and can optionally scan stored DB reviews for the detector's live flag rate (degrading gracefully when no database is reachable). Running it surfaces a real blind spot immediately — an overall 75% false-negative rate, 100% on education bias.

**Tests added or updated:**
`tests/unit/test_bias_audit.py` — 16 unit tests covering text extraction from `sections` JSON (including `None`, string, and malformed inputs), confusion-matrix tallying with divide-by-zero-safe rates, per-signal breakdown, empty-sample skipping, labeled-sample loading plus its validation errors, and report formatting. Added `tests/fixtures/bias_audit_samples.json` as the labeled ground-truth set.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

> Note on "passes": the codebase has documented pre-existing failures in both `make check` and `make test-unit` (see the PR description). My changes introduce **no new failures** — `make test-unit` goes from `52 failed / 345 passed / 31 errors` to `52 failed / 361 passed / 31 errors` (my 16 new tests, all green), and my new files are individually ruff-, black-, and mypy-clean (enforced by pre-commit on every commit).

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
One classmate review came in on [PR #583](https://github.com/ascherj/pathreview/pull/583#issuecomment-5160145554)
from [@Divergent-Code](https://github.com/Divergent-Code) (Aug 2). No maintainer review —
that isn't offered this term. They pulled the branch down and confirmed it reproduced
exactly on their machine (same 16 passing tests, same `TP=2 FP=0 TN=6 FN=6`), endorsed the
fixture-set design decision and the `safety/` vs `scripts/` split, and raised two things:

1. **Presentation, not math.** My ground-truth set is 14 samples, and the per-signal splits
   are small — education 5, none 4, age 3, origin 2. So printing a bare
   `[origin] false_negative_rate=50.0%` invites a maintainer to read far more precision into
   it than 1-of-2 can carry, which is a real problem for a report whose whole purpose is
   giving someone numbers to tune thresholds against. They suggested putting the counts next
   to each rate.
2. **Unrelated diff noise.** `frontend/package-lock.json` carried 10 deletions — `"peer": true`
   lines stripped by a different npm version — that had nothing to do with the audit.

**How you responded:**
I replied on the PR that I'd fold both into the next push, then did
([`123fb47`](https://github.com/LittlePixels/pathreview/commit/123fb47)), and
[confirmed back on the thread](https://github.com/ascherj/pathreview/pull/583#issuecomment-5198603093)
once it landed:

- Every rate now prints its own numerator and denominator —
  `false_negative_rate=50.0% (1/2)`, `[education] false_negative_rate=100.0% (4/4)`,
  and undefined rates render as `n/a (0/0)` instead of silently vanishing. I added
  `flagged` / `labeled_biased` / `labeled_neutral` properties to `ConfusionMatrix` so each
  rate and the count it divides by come from one place rather than being recomputed in the
  formatter. Three new unit tests cover the count rendering, including the zero-denominator
  case (19 tests total now).
- Reverted `frontend/package-lock.json` to match `main`.

I took the suggestion as written rather than negotiating it, because it was correct and it
was aimed at exactly the thing this deliverable is for. What I did *not* do is expand the
sample set to make the percentages more trustworthy — I said so explicitly in the reply,
since showing the counts mitigates the small-sample problem rather than fixing it. Getting
to 40–50 labeled samples is the real fix, it's too large to land as a review response, and
it deserves its own PR; I've noted it below as the thing I'd do differently.

---

### Reflection

**What was harder than you expected?**
Two things, neither of them the code.

The first was reproducing a *missing capability*. Week 8 asks for a reproduction, and #72 has
no crash — nothing fails, the feature just doesn't exist. I spent a while stuck on what there
even was to reproduce before deciding the honest answer was to demonstrate the *blind spot*:
run the existing detector over benign and crafted-biased text and show it misses 3 of 3. That
turned out to be the most valuable thing I did all module, because it produced the number the
whole PR now rests on.

The second was discovering that `main` is already red. Mid-Week 9 I ran `make test-unit`,
saw 52 failures and 31 errors, and assumed I'd broken something badly. It took real time to
work out that this was the pre-existing state — and then more time to work out what to
*write* in a self-review checkbox that says "make check passes" when it cannot pass and never
did. The resolution — capture the baseline, report the delta (`52 failed / 345 passed` →
`52 failed / 361 passed`), and say plainly in the PR that the absolute numbers are red —
felt uncomfortable to write and was clearly right. Nine of those pre-existing failures are in
`test_bias_detector`, i.e. the exact blind spots my audit measures, which was a strange thing
to find out about your own issue.

**What did you learn about working in a large codebase?**
That the constraints come from code you didn't write and don't get to change, and that
noticing them early is most of the work.

The concrete instance: #72 asks for a breakdown "by demographic signal," and the `Profile`
model has no demographic fields. On my own project I'd add a column and move on. Here I
couldn't — and inferring demographics from real user data would have been a worse idea than
the missing feature. So the design became a labeled fixture set for ground-truth accuracy
plus an optional `--scan-db` pass for live flag rate, with the reasoning written down in
PLAN.md. Writing down *why* the obvious approach was rejected turned out to matter as much
as the code; it's the part my reviewer responded to most directly.

I also learned to leave things alone. I found that `detect_bias` is never called anywhere in
the review pipeline ([review_service.py:366](core/services/review_service.py#L366)) — the
safety layer is effectively dead code. That is a bigger problem than the one I was assigned.
On my own project I'd have fixed it in the same commit. Here it's someone else's roadmap
decision, so it goes in the PR description as a finding, not in the diff. Same for the
detector's 75% miss rate: the audit deliberately doesn't touch `bias_detector.py`.

The other lesson was structural. Keeping the scoring in `safety/bias_audit.py` with no
database or I/O, and the CLI as a thin layer over it, is the only reason 19 unit tests were
possible — in a repo where the test suite can't be trusted to be green, tests that need no
infrastructure are the ones that actually prove something.

**How did AI tools help — and where did they fall short?**
Most useful for orientation and for mechanical work. Finding the shape of the `sections`
JSON, tracing where `detect_bias` is and isn't called, and getting the confusion-matrix
scaffolding and docstrings into the house style were all much faster with AI than reading
the repo cold.

Where it fell short is more interesting, and it's a consistent pattern: AI is fluent about
the code and naive about the ground truth underneath it.

- It would happily have written an audit that broke down results by demographic *before*
  anyone checked whether the data model had demographic fields. I found that gap by reading
  `Profile` myself, and it reshaped the entire design.
- It assumed a green baseline. The question "does this repo's test suite already fail?" is
  not one it thought to ask, and the answer changed what my PR could honestly claim.
- The labels are mine and can't be delegated. Whether *"Bootcamp grads rarely have the depth
  needed for senior roles"* counts as biased is a judgment call, and every number in the
  report is downstream of 14 such calls. AI can draft candidate sentences; it can't own
  whether the labels are right, and if they're wrong the tool is worse than useless because
  it looks rigorous.
- And the thing my reviewer caught — rates printed without their counts — was AI-written code
  that was correct and misleading at the same time. No test would have failed. It took a
  human reading the output as a maintainer would.

**What would you do differently if you started over?**
Build the labeled sample set first, and build it much bigger. I wrote the scoring module in
Week 9 and the fixtures after it, which is backwards: the sample set is the part that makes
the numbers mean anything, and it's the part that needed the most thought. Fourteen samples
with two in the `origin` bucket is thin enough that my reviewer's fix — showing the counts —
is really a mitigation for a sampling problem, not a solution to it. Forty to fifty samples,
labeled before any scoring code existed, would have produced a report a maintainer could act
on directly.

Two smaller ones. I'd capture the `main` baseline in Week 7 during setup instead of
discovering it mid-Week 9 under time pressure. And I'd have asked the fixture-vs-live-DB
question in the issue thread in Week 8 rather than carrying it as an "open question" for a
week and then resolving it alone — I got to a defensible answer, but a two-line comment
could have gotten me there seven days earlier.

**What are you most proud of?**
That I measured instead of fixed. The tempting move on an issue about a bias detector that
misses 75% of biased text is to improve the detector — it's more satisfying and it looks like
more work. Producing evidence and leaving `bias_detector.py` untouched is the more useful
contribution, because the maintainers now have reproducible numbers to tune against instead
of my opinion about their thresholds.

The proof that it worked is small but it's the detail I'll keep: a classmate cloned the
branch and got identical output down to `TP=2 FP=0 TN=6 FN=6`. Determinism, no database
required, no hidden state — that was a design goal from Week 8, and it's why the review was
about the substance instead of about why it wouldn't run.
