## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/18

**Issue title:** Add end-to-end ingestion test with a sample resume fixture

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The ingestion pipeline currently only has unit tests that check individual
parsers in isolation, so there is no coverage proving the pieces work together
as one flow. This issue asks for an integration test that exercises the full
path — from a resume file being uploaded, through parsing and processing, to
the resulting embeddings being stored. The fix lives in the ingestion module and
adds `tests/integration/test_ingestion_pipeline.py` backed by realistic sample
resume fixtures under `tests/fixtures/sample_resumes/`. Success means a single
test can catch regressions where a component works alone but breaks when wired
into the complete pipeline.

**Branch name:** test/18-e2e-ingestion-test-with-sample-resume-fixture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

### Reproduction of the gap

Because this is a missing-coverage issue (not a runtime bug), "reproducing" it
means confirming the test does not exist and pinning down exactly where it
should live. I verified three things locally on this branch.

**1. The integration suite is empty — it collects zero tests:**

```
$ .venv/bin/pytest tests/integration -v
collected 0 items
============================ no tests ran in 1.25s =============================
```

`tests/integration/` contains only `__init__.py`; there is no
`test_ingestion_pipeline.py`.

**2. The pipeline orchestrator has no test that exercises it end-to-end:**

```
$ grep -rl "ingest_resume\|IngestionPipeline" tests/
(no matches)
```

The orchestrator lives in
[`ingestion/pipeline.py`](ingestion/pipeline.py) — `IngestionPipeline.ingest_resume()`
chains the full flow: `ResumeParser.parse()` → `StrategySelector.chunk()` →
`BatchEmbeddingProcessor.process()` (embed + store in the vector DB) →
`_record_ingested_source()`. Every unit test under `tests/unit/` covers one of
these components in isolation (e.g. `test_resume_parser.py`,
`test_semantic_chunker.py`, `test_batch_processor.py`), but nothing wires them
together, so a break at a seam between components would go undetected.

**3. The required fixtures directory does not exist:**

```
$ ls tests/fixtures/sample_resumes
ls: tests/fixtures/sample_resumes: No such file or directory
```

There is no `tests/fixtures/` directory at all. The only resume sample today is
an inline string fixture, `sample_resume_text`, in
[`tests/conftest.py`](tests/conftest.py) — not a file-based fixture that
exercises the upload path.

**Conclusion / where the fix lives:**
- Add sample resume file(s) under `tests/fixtures/sample_resumes/`.
- Add `tests/integration/test_ingestion_pipeline.py` that drives
  `IngestionPipeline.ingest_resume()` from a fixture file through to stored
  embeddings, asserting each stage's output and the final `IngestResult`
  (`chunk_count`, `skipped`, `source_id`), with the embedding provider / vector
  DB stubbed so the test runs offline.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/emilypmendez/pathreview/commit/ab805f9

**Reproduction summary:**
Ran `pytest tests/integration -v` and `grep -rl "ingest_resume\|IngestionPipeline" tests/`,
observing that the integration suite collects 0 tests, no test touches the
pipeline orchestrator, and `tests/fixtures/sample_resumes/` does not exist —
confirming the coverage gap is real and isolating exactly where the fix belongs.

**PLAN.md link:** https://github.com/emilypmendez/pathreview/blob/test/18-e2e-ingestion-test-with-sample-resume-fixture/PLAN.md

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
None blocking. Verified via a throwaway script that the full pipeline runs
end-to-end with the existing `MockEmbeddingProvider` and a fake vector-DB spy,
so no production code changes are needed — the fix is test-only. One decision
settled during research: use a fake vector DB rather than a live ChromaDB
client, because chunk metadata includes a list (`detected_sections`) that
ChromaDB's scalar-only metadata constraint would reject.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Working from PLAN.md, all sub-tasks are done. Sub-task 1: added the sample
resume fixture at `tests/fixtures/sample_resumes/sample_resume.md`. Sub-tasks
2–5: added `tests/integration/test_ingestion_pipeline.py`, which builds the
offline test doubles (existing `MockEmbeddingProvider` + an in-memory
`FakeVectorDB` spy, with the `db_session` dedup lookup returning `None`), drives
`IngestionPipeline.ingest_resume()` end-to-end, and asserts both the returned
`IngestResult` and the stored embeddings/metadata/IDs at the storage seam. All 8
tests pass under `make test-integration`; each change was committed separately.

**Next steps:**
Add the edge-case tests (duplicate-skip, empty resume), run the full baseline
comparison to confirm no new failures, self-review against CONTRIBUTING.md
(branch name, commit format, docstrings), and open the PR to upstream.

**Blockers:**
None. Confirmed the mypy pre-commit hook flags unannotated test methods, but
existing `tests/unit/*` files are unannotated too, so I'm matching the repo's
established test style (`make check` excludes `tests/` from typecheck anyway).

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/502

**Branch:** `test/18-e2e-ingestion-test-with-sample-resume-fixture`

**What you built:**
An end-to-end integration test for the resume ingestion pipeline. It feeds a
sample resume fixture into `IngestionPipeline.ingest_resume()` and verifies the
full parse → chunk → embed → store flow, using the offline `MockEmbeddingProvider`
and an in-memory vector-DB spy so it runs with no network or Docker services.
No production code was changed — the fix is test-only.

**Tests added or updated:**
- `tests/integration/test_ingestion_pipeline.py` (new) — 8 tests: end-to-end
  happy path, embedding shape (1536-dim), metadata propagation across stage
  seams, stored document text, `{source_id}_chunk_{index}` ID convention,
  duplicate-source skip, empty-resume handling, and mock-embedding determinism.
- `tests/fixtures/sample_resumes/sample_resume.md` (new) — realistic resume
  fixture with detectable sections.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Interpreted per the pre-existing-failures guidance: this branch introduces no
new failures. Baseline recorded before starting — `make test-unit`: 53 failing
before and 53 after, identical set; `make check`: 182 ruff lint errors before
and after, none in the files I added. All pre-existing and documented in the PR.)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review has come in yet. The PR (https://github.com/ascherj/pathreview/pull/502)
is still open and unreviewed by the maintainer.

**How you responded:**
N/A — no feedback to respond to. If review lands after this entry, I'll address
it on the same branch and note it in the PR thread rather than the journal, since
this is the final entry.

---

### Reflection

**What was harder than you expected?**
The hardest part was not writing the test — it was proving I didn't need to
change production code. My instinct on a "add a test" issue was to jump straight
to writing assertions, but I kept getting stuck because I didn't actually
understand how the four stages (`parse → chunk → embed → store`) handed data to
each other. The real work was in Week 8: writing a throwaway script to run the
whole pipeline once and watch what each stage returned, so I could see the seams
before I tried to assert on them. The specific thing that surprised me was the
ChromaDB scalar-only metadata constraint — chunk metadata carries a list
(`detected_sections`), which a live ChromaDB client would reject, so a naive
"just use the real DB" integration test would have failed for a reason that had
nothing to do with the code under test. Discovering that quietly reframed the
whole approach toward an in-memory `FakeVectorDB` spy. I would not have predicted
that a metadata typing rule would be the thing that shaped my test architecture.

**What did you learn about working in a large codebase?**
Contributing to someone else's production code is mostly about reading the room,
not writing code. On my own projects I set the conventions; here I had to infer
them and then defer to them even when they felt wrong. The clearest example was
the mypy pre-commit hook flagging my unannotated test methods. My reflex was to
add type annotations to "do it right," but the existing `tests/unit/*` files are
all unannotated, and `make check` excludes `tests/` from typechecking anyway.
Matching the repo's established style was the correct move — a PR that
gratuitously annotates only the new test file creates inconsistency and gives a
reviewer a reason to ask "why is this file different?" I also learned to
establish a baseline before touching anything: recording that `make test-unit`
had 53 failures and `make check` had 182 ruff errors *before* my change is what
let me say with confidence "I introduced zero new failures" instead of panicking
when I saw red. In my own repo a green suite is the baseline; in a large shared
codebase the baseline is often already broken, and the honest claim is "no new
breakage," not "everything passes."

**How did AI tools help — and where did they fall short?**
AI was most useful for orientation and mechanical scaffolding: tracing which
files `IngestionPipeline.ingest_resume()` touched, drafting the `FakeVectorDB`
spy boilerplate, and sanity-checking that my fixture had the sections the chunker
would actually detect. That saved real time in the exploration phase. Where it
fell short was exactly the judgment calls above. AI could not have told me the
ChromaDB metadata constraint would bite until I ran the pipeline and hit it — the
knowledge lived in runtime behavior, not in any single file it could read. And on
the mypy/annotation question, AI's default lean is toward "best practice" (add
the types), which was the *wrong* call for this repo. Deciding to match an
imperfect local convention over a general best practice is a judgment I had to
make by reading the surrounding files myself. AI is good at "what does this code
do"; it is weak at "what will this specific maintainer want," which is the actual
question a contribution has to answer.

**What would you do differently if you started over?**
I'd run the pipeline end-to-end on day one instead of reading it statically for
too long first. The throwaway exploration script in Week 8 unlocked everything —
the seams, the metadata constraint, the confirmation that no production change
was needed — and I could have written it in Week 7 and saved myself a lot of
guessing. On process, I'd also open the PR as a draft earlier and explicitly ask
the maintainer about the annotation/style question up front, rather than deciding
it solo and documenting my reasoning in the PR description. My call was defensible,
but surfacing it as a question would have been a cheaper way to de-risk the review
than hoping my written justification lands. Issue selection I wouldn't change — a
test-only, no-production-change issue was a good first contribution because it let
me learn the codebase's shape without the pressure of also not breaking it.

**What are you most proud of from this module?**
The discipline of the baseline comparison and the honesty in how I reported it.
It would have been easy to write "all tests pass" and move on, or to quietly fix
a couple of the 53 pre-existing failures to make my PR look cleaner. Instead I
recorded the before/after numbers, kept my change strictly scoped to the missing
coverage, and stated plainly that the repo has pre-existing failures my work
neither caused nor fixed. That's the habit I most want to carry forward: making
a claim I can actually defend, rather than the claim that looks best.
