## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/72

**Issue title:** Add a bias audit report that runs over a sample of stored reviews

**Tier:** [x] Tier 2

**Problem summary:**
The pathreview app has a bias detector (`safety/bias_detector.py`) that analyzes reviews for demographic bias signals, but there is no tooling to audit its performance at scale. Issue #72 asks for an offline script (`scripts/audit_bias.py`) that samples 100 stored reviews from the database, runs them through the bias detector with detailed logging, and produces a report showing false positive and false negative rates by demographic signal. A successful fix would give maintainers a repeatable way to measure and track the bias detector's accuracy over time.

**Branch name:** feat/72-bias-audit-report

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Dagmawi20-tech/pathreview/commit/0ec6c3b

**Reproduction summary:**
Created `scripts/audit_bias.py` as a stub that raises `NotImplementedError`, confirming the script does not exist. Running `python scripts/audit_bias.py` produces the error, proving the gap described in issue #72 — `BiasDetector` is implemented but never called in a batch context.

**PLAN.md link:** https://github.com/Dagmawi20-tech/pathreview/blob/feat/72-bias-audit-report/PLAN.md

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
The seeded reviews use placeholder content that won't trigger any bias patterns, so verifying the script works correctly will require injecting synthetic reviews with known-biased text. Need to confirm the best approach for this — either add test fixtures in the script itself or insert them via the DB directly.

**Pre-existing test failures noted:**
Running `make test-unit` before starting implementation shows 53 pre-existing
failures across multiple files unrelated to issue #72. Of note: 9 tests in
`test_bias_detector.py` already fail because the existing regex patterns in
`safety/bias_detector.py` are too narrow — phrases like "bootcamp graduates
can't write production code" and "young developers can't handle complex systems"
are not caught. These failures exist before any changes and will be documented
in the PR. My changes will not introduce any new failures.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented `scripts/audit_bias.py` — samples up to 100 completed reviews from
the database, runs each through `BiasDetector`, categorizes flags by signal type
(dismissive education vs demographic assumption), and prints a structured report.
Added synthetic fixtures for detector validation. 27 unit tests written and passing.

**Next steps:**
Open PR, write PR description, finalize JOURNAL.md.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/636

**Branch:** `feat/72-bias-audit-report`

**What you built:**
`scripts/audit_bias.py` — an offline bias audit script that samples up to 100
completed reviews from the database, runs each through `BiasDetector` with detailed
structlog logging, and produces a report showing flag rates broken down by demographic
signal type. Includes synthetic test fixtures to verify the detector is working even
when seeded reviews contain only placeholder content.

**Tests added or updated:**
`tests/unit/test_audit_bias.py` — 27 tests covering `extract_text_from_review`,
`run_synthetic_validation`, `audit_reviews`, and `compute_report`. All pass.

**Self-review confirmation:** [x] make check passes (182 pre-existing errors, 0 new)  [x] make test-unit passes (53 pre-existing failures, 0 new)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback came in during the week. The PR (#636) was submitted to
the upstream pathreview repo and remains open. This is expected for a large
open-source repository with many contributors — maintainers prioritize reviews
on a schedule that doesn't always align with course deadlines.

**How you responded:**
No response was needed. The PR description is complete and self-documenting,
so a reviewer has everything they need when they do get to it.

---

### Reflection

**What was harder than you expected?**
Setting up the local environment on Windows was significantly harder than
expected. The project requires Docker with WSL 2, `make`, Python 3.11+, and
a specific PostgreSQL port configuration to avoid conflicts with native
installations — none of which work out of the box on Windows PowerShell.
I had to install WSL 2 from scratch, configure Docker Desktop's WSL
integration, install `make` via apt inside Ubuntu, and deal with Python
version issues (the system had Python 3.14 but the project expects 3.11).
The actual code contribution took a few hours; the environment setup took
longer. In a real job this would have been a half-day blocker before writing
a single line of code.

**What did you learn about working in a large codebase?**
The biggest difference from building your own project is that you have to
earn the right to change things. In my own projects I just make the change
and move on. In pathreview, I had to read the existing patterns first —
how `seed_db.py` connects to the database, how other scripts use `asyncio.run()`,
how structlog is configured — before I could write code that fits. If I had
just written the script without reading the existing code, it would have worked
but looked foreign to anyone else maintaining it. The pre-commit hooks (ruff,
black, mypy) also made this concrete: the codebase has standards that are
enforced automatically, and you have to match them whether you agree with them
or not.

The 53 pre-existing test failures were also instructive. In a real contribution
you're not responsible for fixing the whole codebase — you're responsible for
not making it worse. Learning to distinguish "this failure existed before my
change" from "I introduced this failure" is a real skill that doesn't come up
when you own everything.

**How did AI tools help — and where did they fall short?**
AI was most useful for orientation. Pasting five service files and asking for
a summary of what each one does saved me significant time building a mental
model of the codebase. It was also useful for generating the initial structure
of `audit_bias.py` — I gave it the spec from `PLAN.md` and the pattern from
`seed_db.py` and it produced a working skeleton quickly.

Where it fell short was mypy compliance. The first version of the test file
had 32 mypy errors — all missing `-> None` return type annotations on test
methods, and a type incompatibility in `audit_bias.py` where `detect_bias()`
received `object` instead of `str`. These are mechanical errors but they
required reading the actual error messages and understanding what mypy was
checking. AI generated code that "worked" but didn't meet the project's
type-checking standards. I had to fix both files manually after reading the
pre-commit output.

**What would you do differently if you started over?**
I would run `make check` and `make test-unit` immediately after cloning —
before writing any code — and document the baseline failure counts in my
notes. I did this eventually but only after I had already started implementing.
Having that baseline documented from the start would have saved me from
second-guessing whether any failures I saw were mine or pre-existing.

I would also choose a slightly different issue. Issue #72 was a good scope —
it was additive, didn't require touching existing code, and had a clear
definition of done. But because the seeded reviews contain only placeholder
text ("Analysis of technical skills from ingested sources"), the script always
reports 0 flags on real data. This makes it hard to demonstrate the script
working end-to-end in a meaningful way without injecting synthetic data. A
Tier 1 issue with a more observable output would have been easier to validate
and demo.

**What are you most proud of from this module?**
The synthetic validation fixtures in `audit_bias.py`. The issue description
asked for false positive/negative rates, but without ground-truth labels on
real reviews that's impossible to compute. Rather than just reporting 0% and
calling it done, I added three known-biased and known-clean test strings that
run through the detector at startup and confirm it's working before touching
the database. This means the script is useful even when the database has no
real biased content — it tells you whether the detector itself is functioning
correctly. That design decision came from reading the existing `BiasDetector`
test failures and realizing that some patterns genuinely don't catch the
phrases the tests expect, which means a real audit could silently undercount.
The fixtures make that visible.
