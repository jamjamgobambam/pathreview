## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/11

**Issue title:** Add support for ingesting a portfolio website URL

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
Currently, users cannot provide their personal portfolio website URLs as a data source for the application. The system only ingests data from GitHub and resumes. Fixing this issue will involve adding a new pipeline that fetches the content of the provided portfolio URL, extracts relevant textual information such as the user's bio and project descriptions, and indexes it into the vector store, allowing the application to use this information alongside existing data sources. This will affect `ingestion/parsers/`, `ingestion/pipeline.py`, and `api/schemas/profile.py`.

**Branch name:** feat/11-portfolio-url-ingestion

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Checklist reasoning:**
- **Understanding:** I can clearly explain that we need to add a `WebParser` to extract text from a portfolio URL and index it via `ingestion/pipeline.py`. I've located `api/schemas/profile.py`, `ingestion/pipeline.py`, and `ingestion/parsers/base.py`.
- **Tier Fit:** As a Tier 1 issue, it touches a few specific files (creating a parser, updating the pipeline, updating the schema) which is a great fit for a first contribution.
- **Codebase Readiness:** I've read `ingestion/pipeline.py` (specifically `ingest_resume` and `ingest_readme`) and understand how the new `ingest_portfolio` method will fit in.
- **Scope & Time:** The estimated 5-8 hours is realistic and achievable before Week 9. There are no open blockers or dependencies.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/mridultailor/pathreview/commit/a4105bf8fa4e7dd1393de3172a1cccd767112ab2

**Reproduction summary:**
I reviewed the existing ingestion pipelines and confirmed that we currently only support Resumes, Repos, and READMEs. I added a TODO comment in `ingestion/pipeline.py` to mark the exact location where the missing `ingest_portfolio` method should be implemented.

**PLAN.md link:** https://github.com/mridultailor/pathreview/blob/feat/11-portfolio-url-ingestion/PLAN.md

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
None at the moment.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I have implemented the `WebParser` class that extracts HTML content from a given URL and strips away boilerplate. I have also added `beautifulsoup4` to dependencies and implemented `ingest_portfolio` in the `IngestionPipeline`. All sub-tasks from PLAN.md are complete.

**Next steps:**
I am submitting the PR.

**Blockers:**


---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/700

**Branch:** `feat/11-portfolio-url-ingestion`

**What you built:**
Added support for ingesting personal portfolio websites into the vector store. A new `WebParser` fetches and extracts the text content from the provided URL, and the `ingest_portfolio` pipeline method chunks and embeds this data just like existing sources.

**Tests added or updated:**
Added `tests/unit/test_web_parser.py` which covers successful and failed HTTP responses and input validation for the new `WebParser`.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes (Note: Pre-existing test and check failures exist, but my changes introduced no new failures.)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer comments came in on PR #700 by the end of the course. Per the
Su26 course note, reviewer feedback isn't an active feature this term, so
this is expected rather than a gap on my end. The PR remains open with no
reviewers or assignees.

**How you responded:**
N/A — no feedback arrived, so there was nothing to respond to. I made sure
the PR description itself does the work a reviewer's first pass normally
would: it calls out the known SPA-rendering limitation and the pre-existing
mypy/test failures on `main` up front, so a future reviewer wouldn't have to
ask about either.

---

### Reflection

**What was harder than you expected?**
Hooking into the existing pipeline was harder than writing the parser
itself. `WebParser` — fetch with httpx, strip `<script>`/`<style>`/`<nav>`
with BeautifulSoup, return clean text — was the easy part. The harder part
was `ingest_portfolio()`: figuring out how the existing semantic chunker and
batch embedding processor expected their input, so the new method could
reuse them instead of duplicating logic. I had to actually trace how the
existing ingestion paths (GitHub repos, PDF resumes) called into the
chunker/embedder before I could write a portfolio path that fit the same
shape instead of bolting on something parallel and inconsistent.

**What did you learn about working in a large codebase?**
The chunker and embedder didn't care where text came from — they just
needed content in the format they already expected. That's the real
difference from a solo project: I wasn't free to design the ideal interface
for my feature, I had to reverse-engineer the interface that already
existed and conform to it. Reading someone else's abstractions accurately
is a bigger part of the job than writing new code.

**How did AI tools help — and where did they fall short?**
AI was fastest at scaffolding: the `WebParser` skeleton, the httpx call, the
basic BeautifulSoup strip logic, and the unit test structure came together
quickly. Where it fell short was real-world HTML. The suggested fetch/parse
logic worked cleanly on simple test pages but didn't hold up against actual
edge cases — pages with malformed markup, non-HTML content types, or (the
limitation I ended up documenting explicitly) JS-rendered SPA portfolios
where `httpx.get()` just returns an empty shell. I had to test against real
URLs myself, catch the failure modes the AI-generated code didn't
anticipate, and add explicit error handling (raising `ValueError` on bad
content types/HTTP errors) that the first pass didn't have.

**What would you do differently if you started over?**
I'd trace the pipeline's existing integration points before writing any
parser code, rather than after. I ended up writing `WebParser` first and
only then working out how it needed to plug into `ingest_portfolio()`,
which meant some rework once I understood the chunker/embedder's actual
expectations. Reading the integration point first would have saved a
commit's worth of typing/linting cleanup at the end.

**What are you most proud of from this module?**
Being upfront in the PR description about what I didn't fix and what still
doesn't work — the pre-existing mypy errors and failing tests on `main`,
and the SPA-rendering gap — instead of glossing over them to make the PR
look cleaner. That's the kind of documentation that actually helps a real
reviewer trust the change.
