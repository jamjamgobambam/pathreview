## Week 7 — Issue selection

**Issue link:** [(https://github.com/ascherj/pathreview/issues/128)]

**Issue title:** [Add a dependency vulnerability scan to the CI pipeline]

**Tier:** A tier-3 issue

**Problem summary:**

We currently do not have any automated checks for security vulnerabilities in our Python or JavaScript dependencies. The goal is to integrate tools like pip-audit and npm audit into our CI pipelines so that any high-severity findings will cause the build to fail.

**Branch name:** [feat/128-add-vuln-scan-ci]

**Setup confirmation:** The App runs locally at localhost:5173

**Cohort ledger:** The issue is added to cohort ledger.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [e8b038e](https://github.com/J321A/pathreview/commit/e8b038e4f9f4159025daf2f712abef02af8d00d7)

**Reproduction summary:**
Confirmed `.github/workflows/ci.yml` has no dependency vulnerability scan (no `pip-audit`, no `npm audit`) across any of its five jobs. Running the tools locally proved the gap matters: `npm audit` reported 11 vulnerabilities in the frontend (1 critical, 5 high — e.g. `ws`, `react-router`) and `pip-audit` reported 2 in Python deps (`chromadb`, `ecdsa`) — 13 total that currently pass CI undetected. Full log: [docs/reproduction-128.md](docs/reproduction-128.md).

**PLAN.md link:** [PLAN.md](https://github.com/J321A/pathreview/blob/feat/128-add-vuln-scan-ci/PLAN.md)

**Walkthrough video (recommended):** _(not yet recorded)_

**Blockers or open questions:**
Whether maintainers prefer a separate `security-scan` CI job or added steps in existing jobs; and how to handle the 13 pre-existing findings so enabling the gate doesn't red-light every open PR (fix-first vs. a reviewed ignore-list at the `high` threshold).

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix end-to-end. Done from PLAN.md: (1) Python scan — added `pip-audit` to
`[dev]` deps and a `security-scan` CI job; (2) Frontend scan — `npm audit` step; (3) severity
gating at `high`; (4) local parity via a `make audit` target + `audit:ci` npm script; (5) backlog
handled — bumped the two fixable Python advisories (`aiohttp>=3.14.3`, `cryptography>=50.0.0`) and
added a reviewed, commented ignore-list for the two with no upstream patch (`chromadb`, `ecdsa`).
Resolved the open question on gate scope: the frontend high/critical findings are all in the
**dev-only** build/test toolchain (vite/vitest/esbuild), whose fixes require breaking major
upgrades (+ Node 20); gated **production** deps at `high` (green today) and report dev-tooling
advisories in a separate non-blocking step. Added `tests/unit/test_security_scan_ci.py` (6 tests,
passing) to lock the wiring in place.

**Next steps:**
Open the draft PR, request peer review in Slack, address feedback, then mark ready and submit.

**Blockers:**
None. Note: the local venv is Python 3.13, so `make typecheck`/`mypy` can't run locally (numpy
stub uses 3.12+ syntax) — CI runs Python 3.11 where it's unaffected. Pre-existing lint/format/test
failures documented in Check-in 2.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/728

**Branch:** `feat/128-add-vuln-scan-ci`

**What you built:**
A `security-scan` CI job (and matching `make audit` target) that scans both dependency trees for
known vulnerabilities and fails the build on high-severity findings — `pip-audit` for Python and
`npm audit --omit=dev --audit-level=high` for shipped frontend deps. Fixable Python advisories are
pinned to patched versions; unpatched ones sit in a reviewed, commented allowlist.

**Tests added or updated:**
`tests/unit/test_security_scan_ci.py` — 6 unit tests asserting the scan stays wired: `pip-audit`
in dev deps, a `security-scan` job running pip-audit + npm audit at `--audit-level=high`, and a
`make audit` target invoking both scanners. Guards against a future edit silently dropping the gate.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

> _"Passes" per the Week 9 pre-existing-failures policy = my changes introduce **no new**
> failures._ Baseline on `main`/this branch **before** my changes (documented so the reviewer can
> reproduce): `make check` — ruff 182 errors, black would reformat 52 files, mypy can't run in a
> Python 3.13 venv; `make test-unit` — 53 failed / 375 passed. **After** my changes these counts
> are unchanged; my new test file passes ruff + black and adds 6 passing unit tests. My changes
> touch CI/Makefile/pyproject/package.json/docs + one test file — none of the code under mypy's
> targets — so they introduce no new failures.

**Draft PR feedback received from:** Peer reviewed via the course Slack channel.

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No upstream review came in. [PR #728](https://github.com/ascherj/pathreview/pull/728) is open
against `ascherj/pathreview` with no maintainer comments, review, or requested changes as of this
entry, and per the Summer 2026 course note reviewer feedback isn't provided for this module. The
only outside eyes on the change were the peer review in the course Slack channel during Week 9
(noted in Check-in 2), which raised no blocking objections to the approach.

**How you responded:**
No upstream feedback to respond to. In its absence I self-reviewed against the reviewer's likely
questions rather than leaving the PR untouched: I documented the pre-existing failure baseline
(`make check` — 182 ruff errors, 52 files black would reformat, mypy unrunnable on a 3.13 venv;
`make test-unit` — 53 failed / 375 passed) directly in Check-in 2 so a reviewer can reproduce it
and see my changes add zero new failures, and I made every accepted risk legible in-line — each
ignored advisory carries its ID and rationale in both `.github/workflows/ci.yml` and the
`Makefile`, pointing back to [docs/reproduction-128.md](docs/reproduction-128.md). The open
question I'd flagged in Week 8 (separate `security-scan` job vs. steps bolted onto existing jobs)
went unanswered, so I resolved it myself and wrote the reasoning into the PR description instead of
leaving it implicit.

---

### Reflection

**What was harder than you expected?**

The code was the easy part. The final change is ~30 lines of YAML, a Makefile target, two version
pins, and a test file — I had a working scan on day one. What took the rest of the module was
deciding what the gate should *mean*. Turning the scanners on immediately red-lit the pipeline with
13 pre-existing findings, and every one of them was a judgment call: fix it, pin it, ignore it with
a written reason, or declare it out of scope. `npm audit fix --force` would have "solved" the
frontend findings and simultaneously made the PR unmergeable.

The specific thing that surprised me was discovering that all the frontend high/critical advisories
lived in **dev-only** tooling — vite, vitest, esbuild — code that never reaches a user's browser.
Patching them required breaking major upgrades plus a Node bump, i.e. a build-system migration
smuggled inside a security PR. That reframed the whole issue: I split the gate into a blocking
`npm audit --omit=dev --audit-level=high` on shipped dependencies and a separate informational
non-blocking run for dev tooling. Nothing in the issue text hinted that this distinction was the
actual work.

The other unexpected difficulty was telling my breakage apart from inherited breakage. When I first
ran `make check` and got 182 ruff errors and 52 files black wanted to reformat, my instinct was
that I'd done something catastrophic. I hadn't — the repo ships that way. Separately, `mypy`
wouldn't run at all locally because my venv is Python 3.13 and a numpy stub uses 3.12+ syntax; CI
runs 3.11, where it's fine. I burned real time chasing a failure that was purely environmental. The
deliverable says "confirm `make check` passes," and the honest answer was that it cannot pass and
never could — so I had to define what "passes" means, prove the before/after counts are identical,
and write that definition into the journal rather than tick a box that would have been false.

**What did you learn about working in a large codebase?**

Blast radius is the thing you can't feel on a personal project. A CI gate isn't a feature that sits
in a corner — it runs on every future PR by every contributor. If I set the threshold too tight,
I've blocked strangers' unrelated work; too loose, and I've shipped a check that's green by
construction and gives false confidence. That asymmetry made me far more conservative than I'd be
in my own repo.

Second: you can't fix what you can't scope. In my own project the correct move is "upgrade
everything, fix the fallout." Here, an unrequested major-version bump of the build toolchain inside
a security PR is a reviewer's reason to close it. Staying inside the boundary of issue #128 —
even when I could see adjacent problems — was a discipline, not a limitation.

Third: conventions beat cleverness. I matched the existing job layout in `ci.yml`, the `.PHONY`
list and `##` self-documenting help-comment style in the Makefile, and the class-based
`@pytest.mark.unit` fixture style already used in `tests/unit/`. None of that makes the code
better in isolation; it makes it invisible in review, which is the goal.

Fourth: decisions must survive your absence. I duplicated the `--ignore-vuln` list in both the
Makefile and `ci.yml` — genuinely a wart. But inventing a shared config file the maintainers never
asked for is worse, so I accepted the duplication and left a "keep in sync" comment with a pointer
to the rationale doc. Writing down *why* the ugly thing is there is what makes it a tradeoff
instead of a mistake.

Finally, a testing lesson I didn't anticipate: you can't unit-test "CI failed." What you *can*
test is that the wiring exists, so I wrote six tests asserting the `security-scan` job, the
`--audit-level=high` flag, the `pip-audit` dev dependency, and the `make audit` target are all
still present. They test configuration, not behavior — their entire job is to make a future silent
deletion of the gate fail loudly.

**How did AI tools help — and where did they fall short?**

AI was strongest at orientation and at boilerplate in an unfamiliar house style. Mapping which
files a CI change touches, reading the existing `ci.yml` job structure, drafting
`docs/reproduction-128.md`, and producing a first pass at the test file that already matched the
repo's pytest conventions — all of that would have taken me hours of directionless reading and
took minutes instead. It was also good at mechanical clarification, like confirming exactly how
`--audit-level` affects `npm audit`'s exit code versus what it merely prints.

Where it fell short was every place the answer depended on context outside the repo. Asked how to
clear the frontend advisories, it offered `npm audit fix --force` — technically correct, socially
wrong, and it had no view on whether a maintainer would accept a Node upgrade bundled into a
security PR. The dev-vs-production scoping decision, which is the actual substance of this
contribution, was not something I could get from a prompt; it required looking at what those
packages do and reasoning about who bears the risk.

It was also confidently unhelpful about my environment. Faced with the mypy failure it kept
proposing type-annotation fixes for a problem that was really "your venv is Python 3.13." Deciding
that the correct response was *don't fix it, prove it's pre-existing and document the baseline*
was mine.

And it fundamentally cannot know today's advisory database. Every version floor I pinned
(`aiohttp>=3.14.3`, `cryptography>=50.0.0`) and every PYSEC identifier in the ignore-list came from
actually running the tools and reading the output. Anything AI suggested there would have been a
plausible-looking hallucinated CVE — which, in a security PR, is exactly the worst kind of wrong.
The general shape of my usage ended up as: AI for speed on the known, me for judgment on the
contested, and never AI for facts that have a date on them.

**What would you do differently if you started over?**

Establish the failure baseline in Week 7, at setup, before touching anything. I didn't discover the
53 failing tests and 182 lint errors until Week 9 while trying to self-review, which meant a day of
"did I break this?" A five-minute `make check > baseline.txt` on a clean checkout would have made
every later comparison trivial and turned my self-review section into a diff instead of an
argument.

Ask the open question in the issue thread instead of deciding alone. In Week 8 I explicitly logged
"separate `security-scan` job vs. steps in existing jobs?" as a blocker — then resolved it
unilaterally in Week 9 because no answer was coming. Posting the comment costs nothing, creates a
visible record that I engaged before implementing, and if a maintainer had replied it would have
de-risked the entire PR. I treated a question I could answer myself as a question I should answer
myself, and those aren't the same thing.

Be more careful with the small consistency stuff. My branch shipped as `feat/128-add-vuln-scan-ci`
while my Week 7–9 journal entries said `bug/128-...`, which quietly broke the PLAN.md link I'd
given the grader. Nothing about the engineering, everything about whether a reviewer trusts the
rest of the document — I fixed it while writing this entry.

What I would *not* change is the issue. A tier-3 CI issue looks like "not real code," and I briefly
worried it was a soft pick. It forced me to read the entire dependency tree of a project I didn't
write, make defensible security calls, and touch the one file that affects every other
contributor. I'd take that over a self-contained bugfix again.

**What are you most proud of from this module?**

Not the YAML — the allowlist. Switching a security gate on in a repo that already has 13 known
findings has two easy failure modes: block everyone's PRs on day one, or set the threshold so loose
the check is decorative. I found the third path — pin what's fixable, gate production dependencies
at `high`, and record every accepted advisory with its ID, the reason there's no patched release,
and a documented place to revisit it. The gate is green today because I made specific, written,
reversible decisions, not because I looked away. If a maintainer pushes back on any single one of
those entries, the conversation starts from a documented position instead of from "why is this
ignored?" That's the part of the PR I'd actually want to defend out loud.
