### Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/14

**Issue title:** Add support for parsing GitHub Actions workflow files to detect CI/CD skills

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

## Problem summary: 

PathReview reviews developer skills from a developer's repository and resume, but it
completely ignores CI/CD configuration, so DevOps skills never show up in a review.

At present, the ingestion pipeline has no parser for `.github/workflows/*.yml` files,
even though those files demonstrate skills like GitHub Actions, Docker, automated
testing with pytest, and deployment. 

Per `docs/ARCHITECTURE.md`, ingestion parsers implement a BaseParser interface, so the new workflow parser would follow that existing pattern (parse → chunk → embed → store).

A successful fix adds a new `workflow_parser.py` under `ingestion/parsers/` and wires it into `skill_extractor.py` so workflow files
are parsed during ingestion and CI/CD skills appear in the extracted skill set.

**Branch name:** feat/14-github-actions-workflow-parsing

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Selection notes ("Is this right for me?" checklist): 

**Understanding:** The ingestion pipeline extracts skills from portfolio documents but
never reads `.github/workflows/*.yml`, so CI/CD skills are invisible in reviews. 

Before: A repo with GitHub Actions workflows shows no DevOps skills in its review. 

After: Skills like GitHub Actions, Docker, and pytest appear in the extracted skill set.

**Files located:** Confirmed `ingestion/parsers/skill_extractor.py` exists and read it alongside `ingestion/parsers/resume_parser.py`. Parsers like ResumeParser implement the `BaseParser` interface (returning a `ParseResult` with text + metadata), while SkillExtractor is a separate keyword-matching layer that scores skills from parsed text. The workflow parser will need to produce output SkillExtractor can score.

**Tier 3 fit:** I've built multi-service projects (FastAPI, Docker, vector databases) in prior coursework, so following an existing parser interface is realistic for me in Weeks 8–9 even as a first contribution to this codebase. I'm choosing it with the scope warning in mind, not despite it.

**Codebase readiness:**  Read `skill_extractor.py` and `resume_parser.py` end-to-end. The closest unit test to my module is `tests/unit/test_batch_processor.py` (ingestion embeddings), which uses a `@pytest.mark.unit` class with `@pytest.fixture` mocks for external services. No parser-specific unit test exists yet, so I'll model a new `test_workflow_parser.py` on that pattern.

**Scope and time:** 6–10 hours across two weeks is achievable with my current schedule and work responsibilities.

No blockers or dependencies on other issues. 3 other students have claimed it; claims are non-exclusive and grading is based on my own artifacts.