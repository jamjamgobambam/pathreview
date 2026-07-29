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
