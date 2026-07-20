## Week 7 — Issue selection

**Issue link:** [[paste link here](https://github.com/ascherj/pathreview/issues/11)]

**Issue title:** [Add support for ingesting a portfolio website URL]

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
Right now the ingestion pipeline only pulls in data from GitHub and resumes, so it has no way to capture context that only lives on a candidate's personal portfolio site, like project write-ups or bio copy. This means the vector store is missing potentially valuable signal about a person's work that they've chosen to showcase outside of GitHub. The fix requires adding a new web parser (likely `ingestion/parsers/web_parser.py`) that fetches a submitted portfolio URL, scrapes the page, and extracts relevant text such as bio and project descriptions. That extracted content then needs to be wired into `ingestion/pipeline.py` so it's embedded and stored alongside the existing GitHub/resume data, and `api/schemas/profile.py` needs to be updated so the API can accept and validate a portfolio URL field on a profile submission.

**Branch name:** [feat/11-add-support-for-ingesting-portfolio-website-url]

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

## "Is this right for me?" — selection notes

**Part 1 — Understanding the issue**
- [x] Can paraphrase without re-reading: the app currently only ingests GitHub and resume data into the vector store; there's no way to pull in content from a candidate's own portfolio site, so anything they've written there (project write-ups, bio) never becomes searchable context.
- [x] Located the relevant files and confirmed they exist: `ingestion/parsers/` (has `readme_parser.py`, `repo_analyzer.py`, `resume_parser.py`, `skill_extractor.py`, `base.py`, but no `web_parser.py` yet — matches the issue's ask), `ingestion/pipeline.py`, `api/schemas/profile.py`.
- [x] Before/after is concrete: before, submitting a portfolio URL does nothing beyond storing the string; after, submitting one triggers a fetch + parse + chunk + embed step so that portfolio text shows up in retrieval alongside GitHub/resume content.

**Part 2 — Tier fit**
- [x] Tier 2 is a fair match — this isn't my first contribution to this repo, and the change genuinely spans multiple layers (a new parser, pipeline orchestration, and API schema), not just one file.

**Part 3 — Codebase readiness**
- [x] Read `ingestion/pipeline.py` in full: `IngestionPipeline` already has a clear pattern to follow — `ingest_resume`, `ingest_readme`, and `ingest_repo_metadata` all do parse → build metadata → chunk via `StrategySelector` → embed via `BatchEmbeddingProcessor` → record via `_record_ingested_source`. A new `ingest_portfolio` method should mirror this shape.
- [x] Read `ingestion/parsers/base.py`: every parser subclasses `BaseParser` and returns a `ParseResult(text, metadata, source_type)` — that's the contract `web_parser.py` needs to satisfy.
- [x] Checked `api/schemas/profile.py`: `portfolio_url` already exists on `ProfileCreate`/`ProfileUpdate`/`ProfileResponse` as an optional string field. **Scope note:** this means the schema work described in the issue may already be partially done — the field exists but isn't validated as a URL (just `max_length=500`) and isn't yet consumed anywhere in ingestion. I'll confirm during implementation whether URL validation needs to be added here or if that's out of scope.
- [x] Read a full existing test end-to-end (`tests/unit/test_readme_parser.py`): tests are organized under `tests/unit/`, use `@pytest.mark.unit`, instantiate the parser via a fixture, and assert on `ParseResult` fields (`text`, `source_type`, `metadata` keys). **Scope note:** there's no existing test file for `pipeline.py` itself (only parser-level tests exist for readme/resume), so I'll need to decide whether to add pipeline-level tests or keep coverage at the new `web_parser.py` level, consistent with what's already there.

**Part 4 — Scope and time**
- [ ] Claims/comments check: need to check the issue comments and the Claims column in the cohort ledger's Issue Catalog tab before finalizing — not yet confirmed from within this session.
- [x] Time estimate: issue lists 5–8 hours; that lines up with the actual scope found in the code (one new parser + one new pipeline method + a small schema check), so Tier 2 / Weeks 8–9 timeline looks realistic.
- [x] No "blocked by #X" language in the issue body, and no other unresolved dependency was mentioned.

**Overall scope reasoning:** The issue is well-scoped and the referenced files check out — including one pleasant surprise, `portfolio_url` is already on the Pydantic schemas, so the real net-new work is the `web_parser.py` module and the `ingest_portfolio` pipeline method, following the existing `ingest_readme`/`ingest_resume` pattern almost exactly. The one open item is manually confirming the claims count in the cohort ledger before committing to start.