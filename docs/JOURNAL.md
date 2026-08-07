\## Week 7 — Issue selection



\*\*Issue link:\*\* https://github.com/ascherj/pathreview/issues/38



\*\*Issue title:\*\* \[Add an integration test that runs the full RAG pipeline against a mock LLM
]



\*\*Tier:\*\* \[ ] Tier 1  \[X] Tier 2  \[ ] Tier 3



\*\*Problem summary:\*\*

\[3–5 sentences, your own words]

The Integration Tests is missing for each component of the RAG Pipeline. It needs to be developed as there is currently no integration testing.

The full query/pipeline is: retrieval → reranking → generation → parsing
The goal is to add one to the tests/integration/test\_rag\_pipeline.py file



\*\*Branch name:\*\* test/38-integration-test\_rag-pipeline



\*\*Setup confirmation:\*\* \[x] App runs locally at localhost:5173



\*\*Cohort ledger:\*\* \[X] Issue added to cohort ledger: Added on Row 70



\*\*Scope and Reasoning Checklist:\*\*

Work through the checklist and note your scope reasoning in your selection notes



\*Part 1 — Understanding the Issue\* \[X]

The issue asks for a new integration test that exercises the full RAG pipeline

which is: retrieval → reranking → generation → parsing. It needs to use the mock LLM

provider instead of a live API call.

The file tests/integration/test\_rag\_pipeline.py needs to be developed as currently only the initializer (\_\_init\_\_.py) is present.

Right now the repo only has unit tests for each RAG component in isolation, so

there's no test verifying the components actually work together correctly.

I've opened those app and modules. I have confirmed the function/class names I'll need to

import and mock



\*Part 2 — Tier Fit\* \[X]

I selected a Tier 2, since it requires understanding how retrieval, reranking,

generation, and parsing interact as a pipeline rather than editing a single

isolated file. It's not too complex like an infrastructure change but not simple like a documentation update

I have contributed once to an first open-source contribution but it has been a while so I believe a Tier 2 is a reasonable stretch for me right now.



\*Part 3 — Codebase Readiness\* \[X]

I've located the existing unit tests for retrieval, reranking, generation,

and parsing. I understand the related folders for rag (evaluator, generator, and retriever) and related tests in conftest and tests/unit. These will be important for understanding the context when trying to implement test/integration/test\_rag\_pipeline.py



\*Part 4 — Scope and Time\* \[X]

I checked the issue comments and the cohort ledger's Claims count for issue

\#38. I am estimating 4-6 hours on this Tier 2 issue.

Given this is a Tier 2 issue, I'm estimating roughly 8–12 hours: time to trace

the pipeline's actual call chain, wire up the mock LLM, write realistic

fixtures for each stage, and assert on the final parsed output.

I've checked for "blockers" that may prevent me from completing this feature addition and found none.

&#x20;



\*\*Reproduction commit link:\*\* https://github.com/matthewpeck6/pathreview/tree/test/38-integration-test\_rag-pipeline



\*\*Reproduction summary:\*\*

Confirmed `tests/integration/` contained only `\_\_init\_\_.py`. Added an `xfail`stub test to `test\_rag\_pipeline.py`; running `pytest tests/integration/ -v`

now shows `XFAIL` instead of collecting zero tests, confirming the gap is real and pinpointing exactly where the new test needs to live.



\*\*PLAN.md link:\*\* https://github.com/matthewpeck6/pathreview/tree/test/38-integration-test\_rag-pipeline/docs/PLAN.md



\*\*JOURNAL.md link:\*\* https://github.com/matthewpeck6/pathreview/blob/test/38-integration-test\_rag-pipeline/docs/JOURNAL.md



\*\*Walkthrough video (recommended):\*\* https://drive.google.com/file/d/1QLX\_bdS22cbf8uDHbsW0zOAhvgPhdNdh/view?usp=sharing



\*\*Blockers or open questions:\*\*

I am still confirming exact mock LLM provider and how the system works. 

Furthermore, there is no subfolder with code for the reranker steps in pathreview/rag. retrieval (exist) → reranking (DNE) → generation (exist) → parsing (exist) 


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All 5 steps of the PLAN.md plan are done. Replaced the `xfail` stub with a real
end-to-end test in `tests/integration/test_rag_pipeline.py` that chains
retrieval → reranking → generation → parsing against the actual RAG modules
(`VectorStore`, `KeywordSearcher`, `HybridRetriever`, `ReviewGenerator`), and
confirmed `pytest tests/integration -v -m integration` passes. Also wrote
`tests/integration/EXPLANATION.md` documenting how the test works and why each
assertion is there. Ran a self-review pass afterward: fixed import ordering
and formatting (`ruff --fix`, `black`) and two `E501` long-line violations in
the new test file so it's lint-clean on its own.

**What you built:**
One integration test, `test_full_rag_pipeline_retrieval_to_parsed_output`,
that indexes a small resume/README corpus into a real ChromaDB
`VectorStore` + BM25 `KeywordSearcher`, retrieves and reranks via
`HybridRetriever`, feeds the retrieved chunks into `ReviewGenerator` with a
mocked LLM client (no live OpenAI calls), and asserts the parsed sections
have the right names, content, confidence, and citations — proving all four
stages actually connect end-to-end, not just in isolation.

**Next steps:**
Open the PR: fill out the PR template, write the PR description, and run
through the pre-submission checklist. Squash/clean up commit history if
needed before requesting review.

**Tests added or updated:**
`tests/integration/test_rag_pipeline.py` — new file, replaces the `xfail`
stub; covers the full RAG pipeline (retrieval, reranking, generation,
parsing) in one end-to-end test. No existing test files were modified.

**Blockers:**
None currently.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
*(`test_rag_pipeline.py` itself is lint/format-clean and its own test passes.
`make test-unit` has 53 pre-existing failures across unrelated modules —
documented in `tests/integration/EXPLANATION.md` — that predate this change
and are unaffected by it.)*
---

### Check-in 2 (end of week)

**PR link:** [ https://github.com/ascherj/pathreview/pull/429]

**Branch:** test/38-integration-test_rag-pipeline

**Branch Comparison Link:** [https://github.com/ascherj/pathreview/compare/main...matthewpeck6:pathreview:test/38-integration-test_rag-pipeline]

**What you built:**
[One integration test, test_full_rag_pipeline_retrieval_to_parsed_output, that indexes a small resume/README corpus into a real ChromaDB VectorStore + BM25 KeywordSearcher, retrieves and reranks via HybridRetriever, feeds the retrieved chunks into ReviewGenerator with a mocked LLM client (no live OpenAI calls), and asserts the parsed sections have the right names, content, confidence, and citations proving all four stages actually connect end-to-end, not just in isolation.]

**Tests added or updated:**
[pathreview/tests/integration/test_rag_pipeline.py]

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

Result: This branch introduces no new check failures. `make check` and
`make test-unit` both show only pre-existing, unrelated failures. The
before/after tables below shows proof none of them were introduced by this change.

Full repository validation:

make check
make test-unit
make check currently reports 182 Ruff errors across pre-existing and unrelated repository files.

**Pre-existing failure verification (before vs. after):**

`git diff main...HEAD --stat -- rag/ tests/unit/` returns empty — this branch
adds only `tests/integration/test_rag_pipeline.py`, `tests/integration/EXPLANATION.md`,
and docs. No file under `rag/` or `tests/unit/` is touched, so the pre-existing
failure count is identical before and after this change by construction.

| | Before (main) | After (this branch) |
|---|---|---|
| `make test-unit` result | 375 passed, 53 failed | 375 passed, 53 failed |

`make test-unit \| tail -5` output (captured on this branch, 2026-08-03):
```
FAILED tests/unit/test_structural_chunker.py::TestStructuralChunker::test_document_with_no_headings
FAILED tests/unit/test_tech_detector.py::TestTechDetector::test_node_modules_excluded
FAILED tests/unit/test_tech_detector.py::TestTechDetector::test_build_directory_excluded
================= 53 failed, 375 passed, 1 warning in 10.27s ==================
make: *** [Makefile:40: test-unit] Error 1
```

Full per-file breakdown of the 53 pre-existing failures (file, failure count)
is in `tests/integration/EXPLANATION.md` under "Pre-existing failures
(unrelated to this change)" — none of the 16 failing files import or exercise
`rag/retriever/hybrid.py`, `rag/retriever/vector_store.py`,
`rag/retriever/keyword_search.py`, or `rag/generator/review_generator.py`.

**Pre-existing Ruff errors (before vs. after):**

`git diff main...HEAD --stat --name-only` shows this branch only touches
`docs/JOURNAL.md`, `docs/PLAN.md`, and `tests/integration/test_rag_pipeline_demo.py`
(the earlier `xfail` reproduction stub) — none of the 61 files with Ruff
errors below. `ruff check tests/integration/test_rag_pipeline.py` on its own
returns `All checks passed!`, so the new integration test contributes zero of
the 182 errors.

| | Before (main) | After (this branch) |
|---|---|---|
| `ruff check .` total | 182 errors | 182 errors |

Top offenders by file (`ruff check . --output-format=concise`, re-run on this
branch, 2026-08-03):

| File | Errors |
|---|---|
| `tests/unit/test_prompt_templates.py` | 19 |
| `api/routes/profiles.py` | 16 |
| `api/routes/reviews.py` | 14 |
| `tests/unit/test_tech_detector.py` | 8 |
| `tests/unit/test_review_service.py` | 8 |
| `api/schemas/profile.py` | 8 |
| `tests/unit/test_bias_detector.py` | 5 |
| `rag/retriever/hybrid.py` | 5 |
| ... (53 more files, 1–4 errors each) | |

Full per-file list is captured in the command output above; not reproduced in
full here since it spans 61 files. None of these were touched by this branch
(see `git diff` note above), so — same as the unit-test table — the before
and after counts are identical by construction, not by re-running against a
`main` checkout.

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
No review came in. I checked PR #429 on `ascherj/pathreview`
(`main...matthewpeck6:pathreview:test/38-integration-test_rag-pipeline`) at
the end of the week and there are no review comments, no line comments, and
no maintainer replies on the PR or on issue #38. Per the Su26 note, reviewer
feedback isn't a feature this term, so this is the expected outcome rather
than a stalled PR. The PR is still open and unmerged as of this entry.

**How you responded:**
No response required — nothing to respond to. I re-ran `pytest tests/integration
-v -m integration` and `ruff check tests/integration/test_rag_pipeline.py` one
more time to confirm the branch is still in the state I described in Week 9,
and left the PR open in case a maintainer picks it up after the course window.

---

### Reflection

**What was harder than you expected?**

The hardest part was that the issue described a pipeline stage that doesn't
exist. Issue #38 asks for a test covering "retrieval → reranking → generation
→ parsing," and I planned around four modules. There is no reranker module in
`rag/`. `HybridRetriever.retrieve()` (`rag/retriever/hybrid.py:78-94`)
normalizes the vector and BM25 score sets, blends them `0.7 * vector + 0.3 *
keyword`, and sorts descending, all inline. I lost real time looking for a
file that was never written before concluding the blend-and-sort *is* the
reranking stage, then had to decide whether to say so or quietly test three
stages and call it four. I documented it in the test docstring and in
`EXPLANATION.md` — that felt more honest than pretending the issue's framing
matched the code.

The second surprise was `MockEmbeddingProvider`. I assumed "mock" meant
"cheap but semantically reasonable." It actually SHA-256 hashes the text to
seed numpy's RNG and returns a deterministic 1536-dim vector with no semantic
meaning at all. My first assertion — that the top retrieved chunk would be the
Python resume line — passed, and I nearly moved on. It only passed because
BM25 caught the literal word "Python"; the vector half of the hybrid score was
pure noise. If I'd written the query without a literal keyword overlap, the
test would have been flaky for reasons I wouldn't have understood. That's the
kind of thing that reads as a green checkmark and is actually a trap.

Third: the repo isn't clean. `make test-unit` fails with 53 pre-existing
failures and `ruff check .` reports 182 errors on `main`. The self-review
checklist asks you to confirm "make check passes," and it does not pass and
never did. Working out how to honestly report that — proving by `git diff
main...HEAD --stat` that I touched no file under `rag/` or `tests/unit/`, so
the before/after counts are identical by construction — took longer than
writing the test did.

**What did you learn about working in a large codebase?**

On my own projects I know the contract of every function because I wrote it,
so I test what I intended. Here I had to test what the code *actually does*,
and those turned out to be different things. The clearest example: I expected
five sections named after the five prompt templates, ending in
`first_impression`. The last one comes back as `general_feedback`, because the
`first_impression` template asks for plain text, and
`parse_review_output()` falls through JSON-fence → raw JSON → plain-text
fallback, and the fallback hardcodes the name `general_feedback`. Neither the
generator's unit test nor the parser's unit test catches that, because each
one is right about its own half. Only the seam is wrong. That is the entire
argument for integration tests, and I didn't really understand it until I hit
it.

I also learned that scope discipline is mostly about what you *don't* touch.
It was tempting to fix a few of the 53 failing unit tests while I was in
there. Not touching them is what let me make a clean, verifiable claim that my
branch introduces zero new failures. A diff that only adds files is trivially
easy for a reviewer to trust; one that also "fixes a couple things" is not.

The other thing: reading tests is the fastest way into an unfamiliar codebase.
`tests/conftest.py` gave me `sample_resume_text` and `sample_readme_text` for
free, which meant my corpus was realistic text rather than `"foo bar baz"` —
and the realism is what made the BM25 assertion meaningful.

**How did AI tools help — and where did they fall short?**

Most useful for orientation and for mechanical work. Tracing the call chain
from `generate_full_review()` down through `generate_section()` into
`parse_review_output()` across four files, and getting the shape of the
`openai` client right so `SimpleNamespace(chat=SimpleNamespace(completions=...))`
matched what `ReviewGenerator` actually calls — that would have been slow by
hand and AI collapsed it into minutes. Same for cleanup: import ordering,
`black`, the two `E501` violations.

Where it fell short was on the things that required looking at *this* repo and
believing what I saw. Asked about the pipeline, AI happily went along with the
issue's four-stage framing and would have had me import a reranker; the code
says otherwise, and only reading `hybrid.py` settled it. It also had no
opinion on whether my "top result is the resume Python line" assertion was
load-bearing or accidental that required understanding that
`MockEmbeddingProvider` returns hash-seeded noise and reasoning about which
half of the hybrid score was actually doing the work. AI generates a passing
test easily. Whether a passing test *proves anything* is a judgment call about
the specific system, and that part stayed mine. The rule I ended up with: use
it to move fast through code I could have read myself, don't use it to decide
what's true about the code.

**What would you do differently if you started over?**

Verify the issue's premises against the source before writing PLAN.md, not
during. My Week 7 plan listed "reranking" as a stage with a `[confirm: where
does reranking live?]` note attached, and I wrote the rest of the plan as if
that would resolve cleanly. It didn't, and every downstream estimate was off
because of it. Thirty minutes of reading `rag/` first would have changed the
plan's whole shape.

I'd also run the full test suite on `main` on day one and write the numbers
down. I discovered the 53 failures and 182 Ruff errors mid-implementation,
which meant a stretch of wondering whether I'd broken something. A baseline
captured before touching anything turns that panic into a one-line
comparison.

Smaller: my time estimate contradicts itself in the Week 7 entry — I wrote
"4-6 hours" and then "8–12 hours" two paragraphs later. I should have picked
one and revised it deliberately. And I'd write `EXPLANATION.md` as I went
rather than after; reconstructing why each assertion existed after the fact
was harder than narrating it in the moment would have been.

**What are you most proud of?**

`EXPLANATION.md` — specifically the part explaining *why* the top-result
assertion is safe despite fake embeddings. It documents a piece of reasoning
that isn't visible in the test code and would be invisible to anyone reading
the diff: that the assertion rides on the BM25 signal, not the vector signal,
because `MockEmbeddingProvider`'s vectors are hash-derived noise. Six months
from now, someone swapping in a real embedding provider or changing the hybrid
weights will know exactly why that line is written the way it is instead of
deleting it as an odd assertion. The test is the deliverable; explaining the
non-obvious reasoning behind it is the part I'd want a reviewer to notice.

