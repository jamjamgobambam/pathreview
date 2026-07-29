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

**Cohort ledger:** [ ] Issue added to cohort ledger  *(action item — record #111 in the cohort ledger)*

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

**Still outstanding from Week 7:** record #111 in the cohort ledger.

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
3. **`make check` cannot be run as written.** The `check` target depends on
   `format`, which runs `black .` and rewrites 52 unrelated files. I ran
   `black --check` instead and am reporting per-file results; worth raising
   upstream as a separate issue, since the documented pre-PR command mutates
   the working tree.

---

### Check-in 2 (end of week)

**PR link:** *pending — to be filled in on submission*

**Branch:** `test/111-pii-scrubber-property-tests`

**What you built:** *pending*

**Tests added or updated:** *pending*

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** *pending*
