# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker (`rag/evaluator/faithfulness_checker.py`) builds the comparison context by calling `chunk.get("text", "")`, assuming that falls back to an empty string whenever a chunk has no usable text. But `dict.get()` only applies its default when the key is missing entirely — if a chunk instead stores `"text": None` (which happens when upstream parsing produces an empty chunk), `.get()` returns `None`, and the later `" ".join(...)` call crashes with a `TypeError`. In practice this means any RAG evaluation run that touches a document with even one malformed or empty chunk fails outright instead of just treating that chunk as having no content. A successful fix makes the checker handle the `None` case explicitly (e.g. `chunk.get("text") or ""`) so evaluation degrades gracefully rather than crashing, confirmed by the already-stubbed `test_none_context_chunk_text` test in `tests/unit/test_faithfulness_checker.py`.

**Scope check (issue checklist reasoning):** Single file to touch (`rag/evaluator/faithfulness_checker.py`), reproduction steps are already given in the issue, a failing test already exists to validate the fix, no new dependencies or schema changes involved, and the estimated effort (2-3 hours) fits a first issue. This made it a safer pick than the ingestion/pipeline issues, which touch multiple files and have less clear-cut reproduction steps.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from `PLAN.md`: `rag/evaluator/faithfulness_checker.py` now builds `context_text` with `chunk.get("text") or ""` instead of `chunk.get("text", "")`, so a chunk with `"text": None` degrades to an empty string instead of raising `TypeError`. Added a new test, `test_mixed_none_and_valid_chunk_text`, covering a case not in the original issue: a chunk list with one `None`-text chunk and one valid-text chunk, confirming the valid chunk still contributes to the score. Re-ran `scripts/repro_issue_153.py` from Week 8 and confirmed it now prints a score instead of crashing.

**Next steps:**
Run `make check` and `make test-unit` for real (mid-fix and pre-fix baseline) once local Docker/Postgres setup is fully sorted, commit the fix, and open the PR using the repo template.

**Blockers:**
Local environment setup (Docker Desktop / Postgres connection) was still being finalized as of this check-in — needed before `make test-unit`/`make check` can be run and confirmed.

---

### Check-in 2 (end of week)

**PR link:** (https://github.com/ascherj/pathreview/pull/263)

**Branch:** fix/153-faithfulness-checker-none-text

**What you built:**
Fixed `FaithfulnessChecker.check()` in `rag/evaluator/faithfulness_checker.py` so a context chunk with `"text": None` no longer crashes the faithfulness scorer with a `TypeError`. The fix builds `context_text` with `chunk.get("text") or ""` instead of `chunk.get("text", "")`, since `dict.get()`'s default only applies when the key is missing, not when it's present with a `None` value.

**Tests added or updated:**
Updated `tests/unit/test_faithfulness_checker.py`: the existing `test_none_context_chunk_text` (previously failing) now passes, and I added a new test, `test_mixed_none_and_valid_chunk_text`, covering a chunk list with one `None`-text chunk and one valid-text chunk, confirming the valid chunk still contributes to the score instead of the whole list being zeroed out.

**Self-review confirmation:** [x] make check passes*  [x] make test-unit passes*

*with documented pre-existing failures unrelated to this change: `make test-unit` shows 43 pre-existing failures in unrelated modules (bias_detector, resume_parser, review_service, pii_scrubber, readme_parser, readme_scorer, relevance_scorer, keyword_search, output_parser, prompt_defense) plus 3 pre-existing failures within `test_faithfulness_checker.py` itself (`test_partial_support_returns_middle_score`, `test_multiple_context_chunks`, `test_multiple_claims_varying_support`) — verified these produce identical scores with and without my change, so they're a separate pre-existing bug in the keyword-overlap logic. `make check` similarly surfaces a pre-existing unused-variable lint error in `test_common_words_filtered_in_overlap` and pre-existing missing type annotations across every test method in the file — neither introduced by my change. Full detail in the PR description.

**Draft PR feedback received from:** none yet

## Week 10 — Iteration & reflection

### Reviewer feedback

**How you responded:**
N/A — no feedback to respond to. My own self-review caught issues before submission: I confirmed the 3 pre-existing `test_faithfulness_checker.py` failures were unaffected by my change by running the same inputs against the pre-fix and post-fix code and comparing scores directly, rather than assuming.

---

### Reflection

**What was harder than you expected?**
Getting my local environment running took more persistence than I expected — `make setup`/`make run` only work inside Git Bash, not PowerShell, since the Makefile hardcodes `SHELL := /bin/bash`, and I also needed to install Docker Desktop from scratch. It took several rounds of troubleshooting (including recurring stale `.git/index.lock` files from OneDrive syncing mid-commit) before everything ran cleanly. It wasn't fun in the moment, but I worked through every blocker methodically instead of giving up, and by the end I understood exactly why each one happened rather than just making an error message disappear.

**What did you learn about working in a large codebase?**
I learned that a red test suite doesn't mean you broke something — this codebase had 43 pre-existing failing tests on a fresh checkout, completely unrelated to my issue, and part of doing this well was learning to verify that distinction with evidence instead of assuming. I also walked away with a concrete, hard-won understanding of `dict.get()` semantics: its default only applies when a key is missing, not when it's present with a `None` value — the kind of subtle bug that's obvious in hindsight but easy to miss, and I traced it all the way from a vague issue description to the exact line and a confident fix.

**How did AI tools help — and where did they fall short?**
AI was a strong pair-programmer for the analytical parts — tracing the root cause, writing a reproduction script, thinking through edge cases in `PLAN.md`, and verifying the fix didn't change behavior it shouldn't by comparing old and new code side by side. Where it fell short was anything that had to happen on my actual machine: installing Docker, running the real test suite, pushing to GitHub. That meant the environment setup and the final commit/push/PR steps were genuinely mine to execute, which turned out to be a good thing — it's the part where I actually learned the tooling instead of just watching it happen.

**What would you do differently if you started over?**
I'd get my local environment fully working before picking an issue, and I'd open the PR as a checkpoint earlier in the week rather than waiting until things felt "done." Both are easy, mechanical changes to make next time, not a sign anything went fundamentally wrong this time.

**What are you most proud of from this module?**
That I didn't just accept "43 tests are failing" as a red flag — I actually proved which failures were mine to worry about and which weren't, by running the same inputs through the old and new code and comparing the results directly. That's the actual skill this module was built to teach, and I did it for real, not just in theory.
