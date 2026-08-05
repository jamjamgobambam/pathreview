## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/75

**Issue title:** Add integration tests for the full safety middleware chain

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
Unit tests exist for the individual `safety/` components (prompt defense, content
filter, bias detector, PII scrubber), but no test runs a request through the
full safety stack in the order listed in the issue
(prompt defense → content filter → bias detector → PII scrubber). The
`tests/integration/` directory currently has only an `__init__.py`, so the
`test_safety_middleware.py` module requested by the issue does not exist yet.
A successful fix adds that integration test module with fixtures covering pass
and fail cases for each layer. (Estimated effort per the issue: 4–7 hours.)

**Branch name:** feat/75-safety-middleware-integration-tests

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

**Selection reason** I have software development experience and have contributed to open source projects in the past, so I think this issue has the right difficulty for me.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** 


**Reproduction summary:**
Confirmed locally (Python 3.11.13, `LLM_PROVIDER=mock`, branch
`feat/75-safety-middleware-integration-tests`) that the issue is a missing-test
gap: `tests/integration/` holds only an empty `__init__.py` (no
`tests/integration/test_safety_middleware.py`), `python -m pytest
tests/integration --collect-only` collects 0 items, and no test anywhere chains
two or more safety components — `ContentFilter` has no test referencing it at
all. Per-component coverage is unit-only (`test_prompt_defense.py`,
`test_bias_detector.py`, `test_pii_scrubber.py`), so the four-layer pipeline
(prompt defense → content filter → bias detector → PII scrubber) is unexercised
end-to-end and even pairwise.

**PLAN.md link:**
[PLAN.md](./PLAN.md)

**Walkthrough video (recommended):**

**Blockers or open questions:**

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All five PLAN.md sub-tasks are complete. I created
`tests/integration/test_safety_middleware.py` with a `run_safety_chain` helper
(returns a `SafetyChainResult` dataclass of per-layer `LayerResult`s) encoding
the four-layer ordering (prompt defense → content filter → bias detector → PII
scrubber) and the short-circuit / passthrough semantics. The 16-test suite
covers per-layer pass/fail cases (including reuse of the shared
`sample_resume_text` / `sample_readme_text` fixtures), cross-layer ordering
the unit tests can't express (injection short-circuit over PII, content-filter
placeholder not tripping downstream layers, bias + PII both reported
independently, chain idempotency), and edge cases (empty / whitespace-only /
unicode / large input). All 16 pass; the file is clean under `ruff`, `black`,
and the pre-commit `mypy` hook (fully annotated — `SafetyChain` callable alias,
`-> None` on every test method, `str | None` narrowing asserts). Baseline
`make check` / `make test-unit` numbers recorded before and after the change
and are identical — no new failures introduced.

**Next steps:**
Final self-review pass — re-read `docs/CONTRIBUTING.md` to confirm branch name
(`feat/75-safety-middleware-integration-tests`) and commit message follow
Conventions — then open the PR with the `PR.md` body, request a draft review,
and fold in any feedback before the Sunday deadline.

**Blockers:**
None. (One noted out-of-scope pre-existing bug: `PIIScrubber.phone_us` does
not redact the parenthesized `(555) 123-4567` format — the `pii_text` fixture
uses the hyphenated form so the integration test stays focused on chain
behavior; fixing that regex would be a separate `fix(safety):` issue.)

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/759

**Branch:** feat/75-safety-middleware-integration-tests

**What you built:**
Added the first integration test for the `safety/` package
(`tests/integration/test_safety_middleware.py`) — a 16-test suite that runs a
representative text through the four safety layers in the order required by
the issue via a `run_safety_chain` helper, asserting the per-layer verdicts
plus the cross-layer ordering (injection short-circuits downstream PII,
content-filter placeholder doesn't trip bias/PII, bias is non-fatal so PII
still scrubs, chain is idempotent). No runtime code touched — purely
additive test coverage that makes `make test-integration` collect 16 items
(was 0).

**Tests added or updated:**
- `tests/integration/test_safety_middleware.py` (new, 16 tests):
  `run_safety_chain` chain helper + `SafetyChainResult` / `LayerResult`
  dataclasses; per-layer pass/fail cases for prompt defense, content filter,
  bias detector, and PII scrubber (incl. reuse of `sample_resume_text` /
  `sample_readme_text` from `tests/conftest.py`); cross-layer ordering tests
  (injection-over-PII, placeholder coupling, bias + PII, idempotency); and
  edge-case smoke tests (empty, whitespace, unicode, large input,
  harmful + PII).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No

**Summary of feedback:**
No reviewer feedback was received this module (Summer 2026 cohort does not
provide reviewer feedback). The PR was opened against `main` and left in a
draft-awaiting-review state; no comments, change requests, or approvals came
in before the end of the module.

**How you responded:**
Left blank — no feedback to respond to. I instead did a self-review pass
against `docs/CONTRIBUTING.md`: confirmed the branch name
(`feat/75-safety-middleware-integration-tests`) and Conventional Commit message
follow convention, re-ran `make check` and `make test-unit` to confirm no new
failures vs. the recorded baseline, and re-read the new test module front-to-
back for naming, docstring, and marker-convention consistency before marking
the PR ready.

---

### Reflection

**What was harder than you expected?**
The pre-commit `mypy` hook was the single hardest part. `make typecheck` only
runs `mypy` over `api/ core/ ingestion/ rag/ agent/ safety/` — it excludes
`tests/` — so the new file passed `make check` clean on the first try. But the
pre-commit hook runs `mypy --ignore-missing-imports` on each staged file
individually, which meant `disallow_untyped_defs` was suddenly enforced on
test methods I hadn't given `-> None`, and on `safety_chain` fixture params I'd
left untyped. That surfaced 16 "Function is missing a type annotation" errors
at commit time and blocked the commit. Fixing them cascaded: adding
`-> None` to every test method pushed several signatures past the 100-char
line limit, so `black` then wanted to reflow them onto multiple lines, and a
couple of the multi-line signatures then tripped the `str | None` LSP/`in`
operator diagnostics that needed narrowing asserts. It was three rounds of
black → ruff → mypy before the file settled. The lesson: the pre-commit hook
is stricter than `make check`, and "passes `make check`" is not the same as
"will commit cleanly."

The second surprise was a real bug I tripped over in `PIIScrubber.phone_us`.
The regex `\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?...` does not redact the
parenthesized format `(555) 123-4567` — the leading `\b` won't bind before
`(`, so the area-code group captures but the surrounding parens survive and
the match doesn't replace the whole phone number. My first `pii_text` fixture
used that parenthesized form and the `count("[REDACTED]") >= 3` assertion
failed with `count == 2`. I had to decide whether to treat it as a test bug
or a real bug: per the issue scope ("add tests"), it's a pre-existing
`fix(safety):` bug, so I switched the fixture to the hyphenated `555-123-4567`
form (which redacts cleanly) and documented the quirk in the PR's "Notes for
Reviewers." It was a useful reminder that writing integration tests for
someone else's component can surface latent bugs in that component — and that
the right move is to pin the *intended* behavior in the test and flag the
divergence, not to silently work around it or silently fix it.

**What did you learn about working in a large codebase?**
Three concrete things. (1) **The map is not the territory.** AGENTS.md says
`integration` tests "require Docker services," but the issue explicitly asked
for an integration test that has no Docker dependencies. I had to make a
documented exception to the literal rule rather than either blindly following
it (and using the `unit` marker, which would have made `make test-integration`
not pick the file up) or silently breaking it. Convention docs are a guide,
not a compiler; the right move is to surface the conflict in code comments
and the PR description. (2) **Baseline matters.** The repo has 53 pre-existing
unit-test failures, 182 ruff errors, and 103 mypy errors — all unrelated to my
issue. If I hadn't recorded those numbers before starting, I would have had
no way to prove my change didn't introduce new failures, and the PR's
self-review checkboxes would have been meaningless. "Doesn't make things
worse" is only checkable against a recorded baseline. (3) **Test coverage
gaps are wider than they look.** The issue said "Unit tests exist for
individual safety components," but `ContentFilter` had *no* test referencing
it at all — not unit, not integration. My PR is the first test touching that
class. Reading the issue at face value would have under-estimated the work;
exploring the codebase first surfaced the real gap.

**How did AI tools help — and where did they fall short?**
AI was most useful for two things: (a) **pattern-matching across the
codebase** — "show me the existing unit-test style, the safety component
signatures, the conftest fixtures, the pyproject markers" in parallel, so the
new file mimics the nearest neighbor's conventions instead of inventing its
own; and (b) **mechanical refactors** — adding `-> None` to 16 test methods
and reflowing through black/ruff/mypy is tedious and error-prone by hand, and
the tooling iteration loop was fast. Where it fell short: the tool's first
draft of the test file passed `ruff` and `black` but failed the pre-commit
`mypy` hook because the tool didn't know the hook is stricter than `make
typecheck` — I had to discover that from the hook's own error output and
drive the fix myself. And the `phone_us` regex failure was a case where the
AI's response was "the test is wrong, fix the fixture string" — which is
*correct* for the issue's scope, but it took me a beat to recognize that the
underlying regex was itself buggy and worth flagging in the PR rather than
just silently working around. AI is good at "make this pass"; it needs human
judgment to decide "should this pass, or is passing it the wrong outcome."

**What would you do differently if you started over?**
Two things. First, I'd read the `.pre-commit-config.yaml` *before* writing a
line of test code. I treated `make check` as the source of truth for what
"passes" means, but the pre-commit hook is the actual gate, and it runs a
stricter mypy on every staged file. If I'd known that up front, the first
draft would have had `-> None` and full param annotations from the start, and
I'd have avoided three round-trips. Second, I'd budget more time for the
"research" phase of issue selection. The issue's "Unit tests exist for
individual safety components" line was subtly wrong about `ContentFilter`,
and the "integration = requires Docker" convention was in tension with the
issue's ask. Both of those took ~20 minutes of codebase exploration to
surface; if I'd done that exploration during Week 7 (selection) instead of
Week 8 (planning), I'd have picked the issue with eyes open and the PLAN.md
would have reflected the real scope from the start. The implementation
itself I'm happy with — the chain-semantics decisions (short-circuit on
injection, passthrough on bias) are clearly documented and reversible, and
encoding them in a helper with a docstring rather than inlining them per test
made the cross-layer ordering tests genuinely readable.

**What are you most proud of from this module?**
The cross-layer ordering tests — specifically
`test_injection_attack_takes_precedence_over_pii` and
`test_content_filter_placeholder_does_not_trip_bias_or_pii`. They're the tests
no unit test can express, and they justify the entire module's existence:
the first proves layer 1 gates layer 4, the second guards against accidental
regex coupling between layers 2 and 3/4. Writing them forced me to think about
what "integration" actually means for a pipeline of independent filters
(ordering, short-circuit, non-fatal passthrough, idempotency) rather than just
"call each component once." The PLAN.md sub-task 4 is the part where the
contribution earned its keep.

