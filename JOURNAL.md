# Development Journal — Module 3

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/111

**Issue title:** No property-based tests for the PII scrubber

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The `PIIScrubber` in `safety/pii_scrubber.py` strips personal data (emails,
US/international phone numbers, SSNs, and street addresses) out of text by
running a set of regexes and replacing matches with `[REDACTED]`. Today it is
only covered by example-based tests in `tests/unit/test_pii_scrubber.py` — a
fixed list of hand-picked strings — so any PII format the author didn't happen
to think of can slip through untested. The missing piece is *property-based*
testing: using `hypothesis` to generate large numbers of randomized but valid
PII values and assert an invariant (the raw value never survives in the
scrubber's output). A successful fix adds `hypothesis` strategies for each PII
type plus round-trip properties that catch regex gaps (e.g. unusual but valid
emails, spacing/punctuation variants in phone numbers) which the current fixed
examples miss.

**Branch name:** test/111-pii-scrubber-property-tests

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### "Is this right for me?" — scope reasoning

- **Scope fits the tier.** Tier 2, estimated 4–6 hours. It's additive test work in
  one file against a small, well-defined public API (`PIIScrubber.scrub` /
  `.detect`) — no schema, API, or frontend changes required.
- **Clear, verifiable definition of done.** "Generated PII is always removed" is a
  concrete invariant, so success is objectively checkable via `make test-unit`.
- **Tooling already in place.** `hypothesis` is already a dev dependency
  (`pyproject.toml`), and the existing example tests give a working template.
- **Bounded blast radius.** Adding tests can't regress production behavior; the
  worst case is that new properties surface real regex gaps in the scrubber,
  which is exactly the value the issue is asking for.

---

## Setup notes (Week 7)

Bootstrapped and verified the local environment before starting.

**Verified working:**
- `docker compose up -d` → `db`, `redis`, `vector-db` all healthy
- `make setup` → venv on Python 3.13.11, deps installed, Alembic at head (`002`), DB seeded
- `make run` → backend on :8000, frontend on **:5173** (returns 200)

**Setup fixes committed on this branch:**
- `Makefile` — bootstrap the venv with an auto-detected Python ≥3.11
  (`python3.13/3.12/3.11`) instead of the hardcoded system `python`, which was
  3.9 and failed the `requires-python >= 3.11` constraint.
- `docker-compose.yml` — bumped `chromadb/chroma` `0.4.22` → `0.5.23`; `0.4.22`
  crashes on startup under NumPy 2.0 (`np.float_` was removed).

**Follow-up noted:** `GET /health` returns 503 due to two pre-existing bugs in
`api/routes/health.py` (raw `SELECT 1` needs `text()` for SQLAlchemy 2.0; the
redis check reads a nonexistent `settings.redis_host`/`redis_port`). The
containers themselves are reachable.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/kredd2506/pathreview/commit/3cec9027cd92340440e0294b44d4f4be4590e082

**Reproduction summary:**
Ran the existing suite (`pytest tests/unit/test_pii_scrubber.py`) and found it
already red on a clean checkout — 5 failed, 20 passed — with `(555) 123-4567`,
the most common written US phone format, not redacted at all; a `hypothesis`
harness with a strategy per PII type then failed 3 of 4 properties and shrank
them to minimal counterexamples (`000-000 0000`, `+1 00 000`, `I worked for
5 adr`). Root cause is two defects in `safety/pii_scrubber.py`: the phone
separator classes are `[-.]?` and omit whitespace (so `+44 20 7946 0958` →
`[REDACTED] 20 7946 0958`, which *looks* redacted but leaks the subscriber
number), and `re.IGNORECASE` lets the two-letter address abbreviations `St`/`Dr`/
`Pl` match inside ordinary words (so `5 years developing Python applications` →
`[REDACTED]ications`).

**PLAN.md link:** https://github.com/kredd2506/pathreview/blob/test/111-pii-scrubber-property-tests/PLAN.md

**Walkthrough video (recommended):** *not recorded — script drafted locally*

**Blockers or open questions:**
1. **Scope — the main one.** The issue asks for tests, so my PR lands tests only,
   with the failing properties as `xfail(strict=True)`. Rewriting the regexes is
   a behavior change to a *safety* component and I think it deserves its own
   issue and review. The fix is pre-drafted in PLAN.md in case the maintainer
   wants it in the same PR. Asking on the issue thread before I open it.
2. **Is dashed-only SSN intentional?** `123 45 6789` and `123456789` slip
   through, but the regex has deliberate exclusions (`(?!000|666)`), so real
   thought went into it. I don't want to assume the omission is a bug.
3. **No hypothesis profile convention exists** in the repo — no registration in
   `conftest.py`. I'll propose one rather than assume.
4. **The wider unit suite is broadly red** — 53 pre-existing failures across
   `skill_extractor`, `tech_detector`, `security`, `structural_chunker`.
   Verified identical count with and without my file, so none are mine, but the
   maintainer should know. Will flag on the issue thread.
5. **Pre-commit mypy conflicts with repo convention.** `make typecheck` excludes
   `tests/` and all 32 existing test functions are unannotated, but the
   pre-commit mypy hook runs on every changed file and rejects them. I annotated
   my file to satisfy the hook rather than bypass it; worth raising upstream as
   a config mismatch.

**Still outstanding from Week 7:** none — #111 has since been recorded in the
cohort ledger.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

Sub-tasks 1–4 of PLAN.md are done, and the Week 8 open question about scope is
resolved: **the PR now carries the regex fix as well as the tests.** The issue
text asks for property tests, but the properties only have value if something
acts on what they find, and what they found was a live PII leak. Shipping tests
that document a leak while leaving it open was the wrong call. The fix is
staged as its own commit so the test-only change stays reviewable on its own.

- *Sub-task 1 — Reproduction.* Done in Week 8 (commit `3cec902`).
- *Sub-task 2 — Strategies.* Done. Five `@st.composite` strategies in
  `tests/unit/test_pii_scrubber_properties.py` — `emails()`, `us_phones()`,
  `intl_phones()`, `ssns()`, `street_addresses()` — each parameterizing the
  dimensions the fixed examples hold constant (separator character,
  parenthesized vs. bare area code, optional `+1`, TLD shape, casing).
  `street_addresses()` draws from `STREET_SUFFIXES`, now exported from
  `safety/pii_scrubber.py`, so the strategy cannot drift from the pattern.
- *Sub-task 3 — Round-trip properties.* Done. One per PII type plus a combined
  property that puts all four types in one string, since `scrub()` applies its
  patterns sequentially to progressively rewritten text and composition is
  where the interesting bugs live.
- *Sub-task 4 — Cross-API and invariant properties.* Done. `detect()`/`scrub()`
  agreement, offset correctness, idempotence, no-PII passthrough, plus negative
  properties so a scrubber that redacted *everything* would not pass either.
- *Sub-task 5 — Stabilize and land.* In progress — see Next steps.

**The fix.** Three defects from PLAN.md, plus two more the properties found
that I had not predicted:

1. Phone separators omitted whitespace (`[-.]?` → `[-.\s]?`). The leading `\b`
   was also load-bearing in the wrong direction — it can never match before a
   `(`, so `(555) 123-4567` failed on two counts. Replaced with a
   `(?<![-.\d])` lookbehind.
2. `phone_intl` consumed only the country code. It now consumes every digit
   group, and requires at least two so `+12` is not read as a phone number.
3. `re.IGNORECASE` applied to `street_address` matched `St`/`Dr`/`Pl` inside
   ordinary words. Patterns are now compiled individually; `street_address` is
   case-sensitive and requires a capitalized name word before the suffix.
4. **New, found by the properties:** pattern *ordering* leaked a country code.
   `phone_us` ran first and ate the national part of `+2-000-000-0000`,
   stranding `+2-` outside the redaction. `phone_intl` now runs first.
5. **New, found by the properties:** `1000-000-0000` — an unseparated trunk
   prefix running into the area code — matched nothing at all.

Defects 4 and 5 are the direct payoff of the issue: I did not think of either
format, and hypothesis shrank both to minimal counterexamples in one run. That
is the argument for property tests in a nutshell.

**Verification so far** (measured against a clean `main` worktree, since the
repo has a large pre-existing red baseline):

| | `main` | this branch |
|---|---|---|
| `tests/unit` | 53 failed, 375 passed | **48 failed, 408 passed** |
| `ruff check .` | 182 errors | **178** |
| `black --check .` | 52 files unformatted | **51** |
| `mypy` (as `make typecheck` runs it) | 5 errors in 4 files | **5 errors in 4 files** |

Diffing the two failure lists: **zero new failures**, and the five that
disappear are exactly the `test_pii_scrubber.py` phone/address cases the fix
addresses. `tests/unit/test_pii_scrubber.py` now passes 25/25 without being
modified — I treated it as a fixed contract rather than editing it to match
new behavior. `ruff`, `black` and `mypy` are all clean on the files I touched.

**Next steps:**

1. Open the PR and post it for peer review (Slack), flagging the scope
   decision and the SSN question specifically.
2. Fill in the PR template completely, including a documented list of the
   pre-existing failures and an explicit statement that this branch does not
   affect them.
3. Address review feedback, then write Check-in 2 with the PR link and submit
   the `/tree/test/111-pii-scrubber-property-tests` URL to the course portal.

**Blockers:**

1. **No maintainer response on the issue thread.** I asked about scope in Week 8
   and nothing came back, and four other people have commented claiming #111.
   I stopped waiting and made the call myself, but the PR description leads with
   the scope decision so a maintainer can push back cheaply — reverting to
   tests-only is one commit.
2. **The SSN question from Week 8 is still open, and I made a judgment call.**
   I added the space-separated form (`123 45 6789`) but deliberately *not* the
   unseparated one (`123456789`). A bare nine-digit run carries no signal
   distinguishing an SSN from an order number or an ID, so matching it trades a
   real leak for a broad false-positive class in a component that feeds LLM
   prompts. I flagged it in the PR rather than deciding it silently.
3. **`make check` fails on `main`, before I change anything.** It runs
   `lint format typecheck` in order and aborts at `lint` on 182 pre-existing
   ruff errors, so `format` and `typecheck` never execute. The documented
   pre-PR command therefore cannot pass for any contributor right now, which is
   worth raising upstream as its own issue. Two follow-on notes: because `lint`
   aborts first, `make format`'s `black .` never runs, so nothing in the working
   tree gets rewritten; and `make typecheck` fails independently (5 errors, all
   missing third-party stubs outside `safety/`). I ran the three tools
   individually to get per-file results.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/358 *(open, ready for
review — not a draft)*

**Branch:** `test/111-pii-scrubber-property-tests`

**What you built:**

Property-based tests for `PIIScrubber` using `hypothesis`: a strategy per PII
type that generates randomized-but-valid values, asserting the invariant issue
#111 names — a generated PII value never survives `scrub()`. Writing them
surfaced five real defects in `safety/pii_scrubber.py`, including a live leak
where `phone_intl` consumed only the country code and turned `+44 20 7946 0958`
into `[REDACTED] 20 7946 0958`, output that reads as redacted while the
subscriber number sits beside it. The PR fixes all five: whitespace-aware phone
separators, a `(?<![-.\d])` lookbehind replacing a `\b` that could never match
before a `(`, full consumption of international digit groups, per-pattern case
sensitivity so `Dr`/`Pl`/`St` stop matching inside `adr`/`applications`/
`streetwise`, and reordering so `phone_intl` runs before `phone_us`.

**Tests added or updated:**

- `tests/unit/test_pii_scrubber_properties.py` **(new)** — the deliverable. Five
  `@st.composite` strategies (`emails`, `us_phones`, `intl_phones`, `ssns`,
  `street_addresses`), each parameterizing exactly the dimensions the fixed
  examples hold constant: separator character, parenthesized vs. bare area code,
  optional country prefix, TLD shape, casing. Twenty tests in three groups —
  **round-trip** (generated PII never survives `scrub()`, plus a combined
  property placing all four types in one string, since `scrub()` applies its
  patterns sequentially to progressively rewritten text and composition is where
  the interesting bugs live); **cross-API** (`detect()`/`scrub()` agreement,
  offsets slice back to the reported value, idempotence, total-function behavior
  on arbitrary text); and **negative** (prose returns byte-identical, a bare
  number followed by lowercase words is not an address), so a scrubber that
  simply redacted everything would fail too.
- `tests/unit/test_pii_scrubber_repro_111.py` → **renamed** to
  `test_pii_scrubber_regression_111.py` — the Week 8 reproduction, with its six
  `xfail(strict=True)` markers dropped now that the fix has landed. Every one
  flipped to `XPASS(strict)` the moment the regexes were corrected, which is
  that marker doing exactly its job. The pinned `@example` counterexamples stay:
  each is the minimal input hypothesis shrank to against the unfixed scrubber,
  so they guard the formats that actually regressed rather than formats someone
  guessed at.
- `tests/unit/test_pii_scrubber.py` — **deliberately unmodified.** Five of its
  25 tests were already red on `main`; all 25 now pass. I treated the file as a
  fixed contract rather than editing its assertions to match new behavior, since
  rewriting the tests you are supposed to satisfy is how a real fix gets faked.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

*Both in the "no new failures" sense the module guidance defines for a codebase
with documented pre-existing failures — `main` is already substantially red.
Measured against a clean `main` worktree:*

| Check | `main` | This branch |
|---|---|---|
| `tests/unit` | 53 failed, 375 passed | **48 failed, 408 passed** |
| `ruff check .` | 182 errors | **178** |
| `black --check .` | 52 files unformatted | **51** |
| `mypy` (as `make typecheck` runs it) | 5 errors in 4 files | **5 errors in 4 files** |

*Diffing the two failure lists gives **zero new failures**; the five that
disappear are exactly the `test_pii_scrubber.py` phone and address cases this
fix addresses. `ruff`, `black` and `mypy` are all clean on the three files the
PR touches, and `mypy safety/` alone is clean. Full table in the PR description.*

**Stated plainly: `make check` does not pass, and it does not pass on `main`
either.** It runs `lint format typecheck` in order and aborts at `lint` on
pre-existing ruff errors — 182 on `main`, 178 here — so `format` and
`typecheck` never execute and `make check` exits non-zero on both. I checked
the box above only in the "introduces no new failures" sense the module
guidance defines for a codebase with documented pre-existing failures; this
branch strictly reduces every count in the table and adds nothing to any of
them. It would be wrong to read that checkbox as "the command exits 0".

Verified directly rather than assumed: `make check` on this branch aborts at
`lint` with `make: *** [lint] Error 1`, and leaves the working tree untouched
(0 files modified), because `format` is never reached. All 178 remaining ruff
errors are in files this PR does not touch; the three files it does touch are
clean under `ruff`, `black` and `mypy`.

Since `docs/CONTRIBUTING.md` instructs every contributor to run
`make check && make test-unit` before opening a PR, and neither command can
pass on a clean checkout today, that is worth its own issue upstream.

**Draft PR feedback received from:** *none yet — the PR is open and ready for
review, and I am posting it to the cohort Slack channel for peer feedback. I
will fold in anything I agree with before the deadline and note the reviewer
here.*

**Course portal submission:**
`https://github.com/kredd2506/pathreview/tree/test/111-pii-scrubber-property-tests`

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**

None. As of 9 Aug 2026, PR #358 has been open 11 days with 0 reviews, 0
comments and no review requests. The repository has no CI configured, so
nothing automated ran against it either. Per the Week 10 brief, reviewer
feedback is not a feature of the Summer 2026 cohort, so this is the expected
outcome rather than a stalled PR.

Worth recording that the silence started earlier: I asked a scoping question on
issue #111 in Week 8 and never got an answer, which is what forced the decision
described below. Four other contributors had also commented claiming #111, and
none of those claims were acknowledged either. I opened the PR knowing a
maintainer might never look at it.

**How you responded:**

No feedback to respond to. What I did instead was try to make the PR reviewable
without a conversation, on the assumption that the reviewer would arrive cold
and skeptical:

- Led the description with the scope decision I could not get answered, and
  isolated the fix in a single commit (`a0f75cd`) so rejecting it is one revert
  rather than an untangling.
- Wrote the two judgment calls up as open questions with the counter-argument
  included — the unseparated-SSN decision and case-sensitive addresses — rather
  than presenting them as settled.
- Documented the pre-existing red baseline in a table, with the explicit claim
  that this branch introduces zero new failures, so a reviewer running the suite
  and seeing 48 failures knows immediately which are mine (none).

---

### Reflection

**What was harder than you expected?**

Establishing what "working" even meant. I assumed a baseline where the suite is
green and my job is to keep it green; instead `main` had 53 failing unit tests,
182 ruff errors, and `make check` — the exact command `docs/CONTRIBUTING.md`
tells you to run before opening a PR — exits non-zero on a clean checkout. So
"do my tests pass" was not answerable in absolute terms. I had to build a clean
`main` worktree, capture a baseline, and `comm`-diff the two failure lists to
say anything defensible. The real work was constructing the measurement, not
passing it.

The second surprise was the shape of the bug. I picked an issue that asks for
*tests*, expecting additive work with zero blast radius, and the tests
immediately proved the component was broken — including `+44 20 7946 0958`
scrubbing to `[REDACTED] 20 7946 0958`, which leaks the subscriber number while
*looking* redacted. That is worse than no redaction, because it defeats review
by eye. A test-only PR would have documented a live PII leak and left it open.

Third, regex subtlety I would not have found by reading. `phone_us` began with
`\b` immediately before `\(?`. A word boundary requires a word character on one
side, so between a space and `(` there is no boundary — meaning that pattern
could *never* match `(555) 123-4567`, the single most common written US format.
The fix was a `(?<![-.\d])` lookbehind, which keeps the "don't start midway
through a digit run" guarantee that `\b` was there to provide. I stared at that
line several times believing it was fine.

**What did you learn about working in a large codebase?**

That the tests are a contract, not scratch paper. Five tests in
`tests/unit/test_pii_scrubber.py` were already failing, and the fastest way to
green was to edit their assertions. I left that file untouched on purpose and
made the source satisfy it, because rewriting the test you are meant to pass is
how a fix gets faked. Those 5 now pass without the file changing — which is a
far stronger claim than "25/25 green" would have been.

That scope is a real decision with a cost either way, and silence does not
excuse you from making it. Ship tests only and I document a leak I know about;
ship the fix and I exceed what the issue asked in a *safety* component. I chose
the fix, isolated it in one commit, and led the PR with the reasoning so it can
be cheaply overruled. In my own project this would have been a five-second call.

That conventions are inferred, not given. Nothing told me a `hypothesis` profile
belongs in `conftest.py` versus per-module `@settings` — there was no existing
convention, so I chose per-module specifically to avoid imposing one on other
suites, and said so in a comment. Similarly `make typecheck` excludes `tests/`
while the pre-commit mypy hook does not, so the repo disagrees with itself about
whether test files are type-checked; I annotated mine to satisfy the stricter of
the two rather than bypass a hook.

And that history is a shared artifact. I rebased onto an updated `main`, which
rewrote five already-pushed commits and would have required a force-push. Undoing
that — backup branch, reset to the published commit, cherry-pick on top — was
straightforward, but only because I noticed *before* pushing. On a branch someone
else had pulled, that force-push would have broken their checkout.

**How did AI tools help — and where did they fall short?**

Most useful on mechanical breadth: generating five `hypothesis` strategies with
the right parameterization, tracing `PIIScrubber` usage across the repo to
confirm no production callers, and drafting the PR description and commit
bodies. It was also good at the regex reasoning once I pushed for the actual
mechanism — the `\b`-before-`(` insight came out of that back-and-forth.

Where it fell short, concretely and worth remembering:

1. **It stated a verifiable fact without verifying it.** I wrote in both the
   journal and the public PR that `make check` "cannot be run because its
   `format` dependency runs `black .` and rewrites 52 files." That is wrong.
   `check` runs `lint format typecheck` in order, aborts at `lint`, and never
   reaches `format` — 0 files are modified. This came from reading the Makefile
   and reasoning, instead of typing `make check`. It survived into a PR on
   someone else's repository until I asked the direct question "is make check
   passing?" and we actually ran it.
2. **The first attempt to verify was itself invalid.** Checking it inside a
   `git worktree` produced `.venv/bin/ruff: No such file or directory` — a
   worktree has no `.venv` — and that missing-binary failure was briefly read as
   a real lint failure. Right answer, wrong evidence, which is the more dangerous
   failure mode.
3. **It could not make the calls that mattered.** Tests-only versus tests+fix;
   whether unseparated `123456789` should be redacted; whether case-sensitive
   addresses are worth losing lowercase matches. Those are judgment about
   consequences in a safety component, and defaulting to whatever sounded
   reasonable would have been the wrong move.
4. **The bugs were found by the technique, not the assistant.** Neither of us
   predicted the pattern-ordering leak (`+2-000-000-0000` → `+2-[REDACTED]`) or
   the unseparated trunk prefix (`1000-000-0000`). `hypothesis` found both and
   shrank them to minimal counterexamples on the first run. That is the entire
   argument of issue #111, demonstrated on me.

The pattern: excellent at producing plausible output fast, and plausible output
is exactly what a property test or an actually-executed command is for. Every
claim in the final PR is one I ran a command to check.

**What would you do differently if you started over?**

Run the target test file *before* choosing the issue. I picked #111 believing it
was additive test work and only discovered in Week 8 that the suite was already
red — which changed the work fundamentally. Thirty seconds of `pytest` in Week 7
would have told me.

Stop waiting on the issue thread sooner. I lost time in Week 8 waiting for a
scope answer that was never coming, on an issue four other people had already
claimed. Better to decide, build it so the decision is cheap to reverse, and say
so explicitly — which is where I eventually landed, just later than I should have.

Verify claims as I write them, not at the end. The `make check` error existed
because I wrote a plausible sentence and moved on. Writing "I ran X and got Y"
forces the run.

Ask for peer review at the start of the week rather than the end. The brief
recommended an early draft PR; I opened mine ready-for-review late, which left
no window for a classmate to look before the deadline.

**What are you most proud of from this module?**

That the property tests found two defects I had already convinced myself were not
there. By Week 8 I had root-caused the problem to two defects and written them up
in PLAN.md with a drafted fix — I thought I understood the component. The
properties then produced `+2-000-000-0000` → `+2-[REDACTED]` and `1000-000-0000`
matching nothing, neither of which I would have written a test for, because both
sit in formats I did not think to imagine.

The point of issue #111 is that example-based tests can only check formats the
author already thought of. I proved that on myself, in public, in the PR
description. Being the counterexample to my own analysis is a better outcome than
being right would have been.
