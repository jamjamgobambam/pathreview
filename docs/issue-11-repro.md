# Reproducing Issue #11 — Portfolio URL Ingestion Gap

**Issue:** [Add support for ingesting a portfolio website URL](https://github.com/ascherj/pathreview/issues/11)

## How I reproduced it

This issue describes a missing feature rather than a crash, so "reproducing" it
means confirming exactly what's absent and where. I inspected `main` (the
pre-fix state) along the two paths a portfolio URL could take: ingestion time
(profile creation) and review-generation time (review processing).

### 1. The ingestion pipeline has no portfolio path

```
$ git show main:ingestion/pipeline.py | grep -n "def ingest"
55:    def ingest_resume(
126:    def ingest_readme(
201:    def ingest_repo_metadata(
```

No `ingest_portfolio` method exists. `ingestion/parsers/` on `main` has no
web/HTML parser either:

```
$ git ls-tree main ingestion/parsers/
__init__.py  base.py  readme_parser.py  repo_analyzer.py  resume_parser.py  skill_extractor.py
```

### 2. `portfolio_url` is stored but never processed

`api/routes/profiles.py` on `main` accepts and stores `portfolio_url` on
profile create/update, but nothing reads it back afterward to fetch or parse
the page:

```
$ git show main:api/routes/profiles.py | grep -n portfolio_url
26:    portfolio_url: str = Form(default=None),
81:            portfolio_url=portfolio_url,
```

### 3. The one place that *mentions* portfolio ingestion is a stub

`core/services/review_service.py::_run_ingestion_pipeline` (run during
`process_review`, i.e. at review-generation time, not profile-creation time)
does reference `profile.portfolio_url`, but only inside an explicit
placeholder:

```python
# Ingest from portfolio URL if available
if profile.portfolio_url:
    try:
        # Placeholder: actual portfolio ingestion logic
        portfolio_data = {
            "source_type": "portfolio",
            "url": profile.portfolio_url,
            "data": f"Portfolio data from {profile.portfolio_url}",
        }
```

No HTTP fetch, no HTML parsing, no chunking, no embeddings — just a
hardcoded string built from the URL itself. The same placeholder pattern
also exists for the `github` and `resume` branches in that function, and
`_run_rag_retrieval_generation` further down returns fully hardcoded
feedback sections rather than querying the vector store. This means it's
pre-existing scaffolding across the whole review-generation flow, not
something specific to issue #11 — see `PLAN.md` risks for how this affects
this fix.

## Observed outcome (pre-fix)

A user could submit a portfolio URL when creating a profile. It saved to the
database correctly, but no content from that URL ever reached the vector
store, so the review agent had no way to reference the user's actual
portfolio bio or project descriptions — confirming the gap as described in
the issue.

## What a successful fix needs to do

Per the issue text: fetch the page content, extract relevant text (bio,
project descriptions), and include it in the vector store alongside GitHub
and resume data. That means building the missing *ingestion-time* path (a
new parser plus a new `IngestionPipeline` method) — not the review-time
placeholder described above, which is out of scope for this issue.
