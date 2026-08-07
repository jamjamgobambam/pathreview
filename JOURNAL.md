# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The PII scrubber in `safety/pii_scrubber.py` uses a phone-number regex that only
matches the dashed format (e.g. `555-123-4567`) and misses the parenthesized
format `(555) 123-4567`, which is one of the most common ways US phone numbers
are written. Because of this gap, `scrub()` leaves parenthesized numbers in the
text unredacted and `detect()` reports no PII for them — a real safety leak, since
the whole point of this module is to strip personal information before it reaches
the model. A successful fix broadens the phone pattern to cover the parenthesized
area-code form (and the space/format variants around it) so both `scrub()` and
`detect()` handle it, making the four related tests in
`tests/unit/test_pii_scrubber.py` pass without regressing the dashed format.

**Branch name:** fix/146-pii-scrubber-parenthesized-phone

**Setup confirmation:** [ ] App runs locally at localhost:5173
> Backing services (PostgreSQL, Redis, ChromaDB) run via Docker, which is not yet
> installed on this machine, so the full app has not been launched at localhost:5173
> yet. Environment is otherwise prepared: fork cloned, `upstream` remote added,
> `.env` created (defaults to the `mock` LLM provider — no API key needed), and
> `make` is on PATH. This issue is unit-test-driven, so it can be developed and
> verified with `make test-unit` against `tests/unit/test_pii_scrubber.py`
> independently of the running web app.

**Cohort ledger:** [ ] Issue added to cohort ledger
> To be completed manually on the cohort ledger spreadsheet (name, GitHub
> username `shahriarshabib`, issue #146).

### "Is this right for me?" — scope reasoning

- **Scope is small and well-bounded.** The bug lives in a single regex in one file
  (`safety/pii_scrubber.py`); the failing tests already exist and define exactly
  what "fixed" means, so success is unambiguous.
- **No cross-module or architectural knowledge required.** It doesn't touch the
  RAG pipeline, the agent orchestrator, the API, or the frontend — just a
  standalone safety utility.
- **Reproducible and testable without the full stack.** The issue includes a
  concrete repro snippet, and verification is a focused unit-test run rather than
  end-to-end app usage — which fits my current environment (Docker not yet set up).
- **Right difficulty for a first contribution.** Tier 1 / "good first issue"; the
  main risk is over-broadening the regex and matching non-phone text, which the
  existing dashed-format test guards against.
- **Conclusion:** appropriately scoped for Week 7 — no hidden dependencies or
  scope creep expected.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/shahriarshabib/pathreview/commit/6fb7d3fc84a926334f87a977eaa0557da648649a

**Reproduction summary:**
In my freshly cloned fork I created a lightweight virtualenv (`pytest` +
`structlog`, no Docker needed for this safety-layer unit) and ran the four phone
tests in `tests/unit/test_pii_scrubber.py` — all four fail
(`test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`,
`test_phone_at_start_of_text`). The issue's repro snippet reproduces it directly:
`scrub("Call me at (555) 123-4567 or 555-123-4567")` returns
`"Call me at (555) 123-4567 or [REDACTED]"` (only the dashed number is redacted)
and `detect("(555) 123-4567")` returns `[]`. This confirms the `phone_us` regex in
`safety/pii_scrubber.py` cannot consume the space after `)`, so the most common US
phone format leaks through unredacted. The reproduction commit pins a `BUG(#146)`
comment on the exact regex line.

**PLAN.md link:** https://github.com/shahriarshabib/pathreview/blob/fix/146-pii-scrubber-parenthesized-phone/PLAN.md

**Walkthrough video (recommended):** _(not recorded)_

**Blockers or open questions:**
- The full app still isn't running at `localhost:5173` (Docker not installed on
  this machine), but issue #146 is a self-contained safety-layer unit, so it is
  reproduced and will be verified via `tests/unit/test_pii_scrubber.py` rather than
  the running web app.
- Open question for Week 9: whether `+1 555 123 4567` should be matched by
  `phone_us` or `phone_intl` (the `test_us_phone_formats` fixture includes it).
- Noted but out of scope: `test_mixed_pii_and_text` also fails, for an unrelated
  reason — the `street_address` regex over-matches (`"Pl"` inside "applications"),
  which redacts "Python". Not part of #146; flagged so I don't confuse it with a
  regression from my fix.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md. Reworked the `phone_us` regex in
`safety/pii_scrubber.py` so number separators accept space/dot/hyphen (not just
`[-.]`) and switched the anchors to lookarounds `(?<!\w)…(?!\w)` so the leading
`(` is redacted too. PLAN.md sub-tasks 1–3 are done: the four target tests
(`test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`,
`test_phone_at_start_of_text`) now pass, and the full `tests/unit/test_pii_scrubber.py`
run is 26 passed / 1 pre-existing-unrelated failure. `mypy safety/pii_scrubber.py`
is clean and `ruff` reports nothing on the changed lines.

**Next steps:**
Sub-tasks 4–5: add the focused regression tests, do the final self-review, open a
draft PR for peer feedback, then mark it ready.

**Blockers:**
Full `make check` / `make test-unit` can't run locally (Docker + full deps like
`tiktoken` not installed), so I verify the affected module with a minimal venv and
rely on repo CI for the rest.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/997

**Branch:** `fix/146-pii-scrubber-parenthesized-phone`

**What you built:**
Broadened the `phone_us` PII pattern so parenthesized and space-separated US phone
numbers (`(555) 123-4567`, `555 123 4567`, `+1 555 123 4567`) are now redacted by
`scrub()` and reported by `detect()`, while the previously-working dashed/dotted
formats are unchanged. The separator class is space/dot/hyphen (not `\s`) so a
match can't span a line break and merge two numbers.

**Tests added or updated:**
`tests/unit/test_pii_scrubber.py` — added `test_parenthesized_phone_regression_issue_146`
(asserts full redaction incl. the leading paren, an accurate `detect()` span, and
no regression on the other formats) and `test_phone_pattern_does_not_span_line_break`.
The four pre-existing phone tests in the same file now pass.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
> "Passes" here follows the course rule for a codebase with documented
> pre-existing failures: **my changes introduce no new failures.** What I actually
> ran (full `make` targets need Docker/deps not on this machine): `mypy
> safety/pii_scrubber.py` → clean; `ruff` → no findings on changed lines (only
> pre-existing repo findings remain on untouched code); `pytest
> tests/unit/test_pii_scrubber.py` → 26 passed, 1 pre-existing unrelated failure
> (`test_mixed_pii_and_text`, the `street_address` regex). Baseline before my
> change was 5 failed / 20 passed in that file.

**Draft PR feedback received from:** none yet — draft PR opened for peer review in
Slack; will address feedback and mark ready before the deadline.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer feedback arrived on PR #997 by the end of the week (0
review comments, 0 reviews as of submission). Per the Summer 2026 note, reviewer
feedback isn't a feature this term, so this is expected rather than a sign that
anything was wrong. The 30 comments on issue #146 itself are other cohort members
claiming the same "good first issue," not review of my change.

**How you responded:**
No feedback to respond to. If a maintainer comments after the deadline I'll reply
professionally and push follow-up commits, but there's nothing to address right now.

---

### Reflection

**What was harder than you expected?**
The environment, not the code. The actual fix was a one-line regex change, but
getting to the point where I could *trust* it took much longer. `make setup`
assumes Docker + Postgres/Redis/Chroma and heavy deps like `tiktoken`, none of
which I had, so I couldn't run the full `make check` / `make test-unit`. I had to
build a minimal venv (`pytest` + `structlog`) just to exercise
`tests/unit/test_pii_scrubber.py`. The other genuinely hard part was
*disambiguating failures*: when I first ran the file, **five** tests failed, but
only four were mine — the fifth (`test_mixed_pii_and_text`) turned out to be an
unrelated `street_address` regex over-matching `"Pl"` inside "app**pl**ications"
and eating "Python". Proving that was pre-existing (and not something I broke)
mattered more than writing the fix.

**What did you learn about working in a large codebase?**
Restraint. In my own projects I'd have "cleaned up" the pre-existing `ruff`/`black`
findings and the buggy `street_address` regex while I was in the file. Here the
right move was the opposite: keep the diff to the single `phone_us` line + its
tests, and *document* everything else as out-of-scope. I also learned to let the
existing tests define "done" — the four failing tests were effectively the spec —
and to match the repo's conventions (Conventional Commit scopes like
`fix(safety):`, the `<type>/<issue#>-<desc>` branch name, Google-style docstrings)
instead of my own habits. Contributing to someone else's production code is
graded on "don't make it worse," not "leave your mark."

**How did AI tools help — and where did they fall short?**
AI was most useful for *tracing and reasoning*: pinpointing why the regex failed
(the missing space separator after `)`), reasoning through the `\b` vs
`(?<!\w)…(?!\w)` anchor trade-off so the leading `(` gets redacted, and drafting
PLAN.md and the regression tests quickly. Where it fell short: it couldn't install
Docker or run the full suite for me, so "does the whole thing actually pass in CI"
is still something I can't verify locally — I had to reason about pre-existing vs
new failures myself. It also can't make the judgment calls: whether checking the
"make check passes" box is honest given I couldn't literally run it, or whether the
`street_address` bug was worth scoping in. Those were mine to decide.

**What would you do differently if you started over?**
I'd verify the environment *before* committing to an issue — specifically confirm I
can run `make test-unit` end to end (Docker installed) so my "passes" claims are
literal, not "no new failures." I got lucky that #146 was verifiable with a tiny
venv; a different issue might have been unreproducible for me locally. I'd also
open the draft PR a day or two earlier to leave real room for peer feedback instead
of opening it close to the deadline.

**What are you most proud of from this module?**
The paper trail, more than the one-line fix. I have a clean four-week arc — issue
selection → a documented reproduction commit that pinpoints the exact regex → a
PLAN.md that predicted the real risks (over-broadening, `\s` spanning line breaks,
the `+1` format question) → a minimal, tested fix → an honest PR that documents
pre-existing failures instead of hiding them or over-reaching to "fix" the repo.
Being able to say exactly what I changed, what I deliberately didn't, and why, is
the part I'd want a real maintainer to see.
