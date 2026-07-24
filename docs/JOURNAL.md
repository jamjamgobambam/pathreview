## Week 7 — Issue selection

**Issue link:** [issue link](https://github.com/ascherj/pathreview/issues/11)

**Issue title:** Add support for ingesting a portfolio website URL

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
This is a feature to allow for ingesting a portfolio website url. A pipeline is required to take the portfolio website url, extract contents and include it in the vector store. The vector store should be alognside GitHub and resume data.

**Branch name:** feat/11-add-ingestion-support-for-portfolio-url

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Is This Issue Right for Me? — Checklist

### Part 1 — Understanding the Issue

- [x] I can explain the problem and the expected behavior in 2–3 sentences without reading the issue.
- [x]  I've located the relevant files and confirmed they exist in the codebase.
- [x] I can describe a concrete before-and-after: what the user sees before the fix and what they see after.

### Part 2 — Tier Fit

- [x] The tier is a realistic match for where I am right now:
  - If this is my first open source contribution: I'm choosing Tier 1.
  - If I've contributed to large codebases before: Tier 2 or 3 is fair game.
  - I'm not choosing a Tier 3 issue to "challenge myself" if I haven't completed a Tier 1 or 2 first — scope surprises in Week 9 don't have a safety net.

### Part 3 — Codebase Readiness

- [x] I've found and read the specific code the issue references (not just the file — the function or section).
- [x] I've read enough surrounding context that I can write a rough plan for the fix without looking anything up.
- [x] I've found the test file for my module and read at least one test end-to-end.

### Part 4 — Scope and Time

- [x] I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.
- [x] I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline.
- [x] This issue has no open blockers or dependencies on other unresolved issues.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [link to commit documenting the reproduced issue] <!-- TODO: fill in after committing this JOURNAL.md update -->

**Reproduction summary:**
Since this is a feature gap rather than a bug, I reproduced it by writing `scripts/check_portfolio_ingestion.py`, which queries the local dev database directly. The `profiles` table already has 4 rows with a `portfolio_url` set (e.g. `https://yasio.dev/`), confirming the field is accepted and persisted end-to-end at the API/schema/DB layer. But the `ingested_sources` table has 0 rows with `source_type='web'` — confirming that `portfolio_url` is never passed to the ingestion pipeline, so no chunks are ever extracted, embedded, or stored for it, unlike GitHub/resume data.

**Command run:**
```
.venv/bin/python -m scripts.check_portfolio_ingestion
```

**Output:**
```
Profiles with a portfolio_url set: 4
  - e953c1f6-30cf-488a-9d36-03760e496adb: https://user1.dev
  - 7abbe7f5-69af-40c9-9f1f-2754f22bc27a: https://user2.portfolio
  - bd3ae3df-71dd-481d-9726-d3773b3cc206: https://user3.io
  - 1e7f5e95-2284-45c4-b8a7-b47b03bcdbd9: https://yasio.dev/

IngestedSource rows with source_type='web': 0

Reproduction confirmed: portfolio_url is accepted and stored on Profile, but no IngestedSource has ever been created for it — the ingestion pipeline is never invoked for portfolio URLs (see PLAN.md).
```

**PLAN.md link:** [PLAN.md](../PLAN.md)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
`IngestionPipeline` currently has no live caller anywhere in the app — resume and readme ingestion aren't wired into any route either, only stored directly on the `Profile` row. Need to confirm with mentors/instructors whether wiring `ingest_portfolio_url` into `api/routes/profiles.py` is expected to also surface/fix this broader wiring gap, or whether it's acceptable to scope this issue narrowly to the portfolio-URL path only.