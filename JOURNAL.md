# Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/18

**Issue title:** #18 Add end-to-end ingestion test with a sample resume fixture

**Tier:** [ ] Tier 1  [✅] Tier 2  [ ] Tier 3

**Problem summary:**  
The PathReview project is missing a complete, end-to-end test suite for ingestion pipeline (parsing, chunking, embedding, and storing documents). This test suite must be located at `tests/integration/test_ingestion_pipeline.py` and must use the fixtures in `tests/fixtures/sample_resumes/`.

**Branch name:** `test/18-ingestion-pipeline-tests`

**Setup confirmation:** [✅] App runs locally at localhost:5173

**Cohort ledger:** [✅] Issue added to cohort ledger

## Is This Issue Right for Me?
### Part 1 — Understanding the Issue
* **Can I explain what this issue is asking for in my own words?**  
✅ I can explain the problem and the expected behavior in 2–3 sentences without reading the issue: The problem summary can be found above.
* **Do I understand which part of the app is affected?**  
✅ I've located the relevant files and confirmed they exist in the codebase: `ingestion/pipeline.py`
* **Do I understand what "done" looks like?**  
✅ I can describe a concrete before-and-after: what the user sees before the fix and what they see after:  
*Before:* The ingestion pipeline is untested and could produce undetected bugs due to the absence of end-to-end integration test suite.  
*After:* A complete integration test suite exists at `tests/integration/test_ingestion_pipeline.py` and stress-tests the document ingestion feature. This test suite uses `pytest` and follows the code patterns and convenions that are set by the existing test suites in `tests/unit`

### Part 2 — Tier Fit
* **Is the tier a realistic match for where I am right now?**  
✅ If I've contributed to large codebases before: Tier 2 or 3 is fair game.

### Part 3 — Codebase Readiness
* **Can I find the relevant code?**  
✅ I've found and read the specific code the issue references (not just the file — the function or section).
* **Do I understand the surrounding code well enough to change it safely?**  
✅ I've read enough surrounding context that I can write a rough plan for the fix without looking anything up.
* **Have I read the relevant test file?**  
✅ I've found the test file for my module and read at least one test end-to-end.

### Part 4 — Scope and Time
* **How many others are already working on this issue?**  
✅ I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.
* **Is the scope realistic for Weeks 8–9?**  
✅ I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline.
* **Are there any blockers or dependencies?**  
✅ This issue has no open blockers or dependencies on other unresolved issues.


# Week 8 — Reproduction & solution planning
**Reproduction steps:**  
1. Set up Docker: `docker compose up -d` and `docker compose ps`
2. Set up project: `make setup`
3. Run ingestion test: `make test-integration`

**Reproduction result:** No test was ran when the command was executed. Additionally, there was no fixtures at all for this
test suite. The only fixture was `tests/conftest.py`. However, it contains in-line, non-file-based samples which cannot simulate
a real API call scenario for the ingestion pipeline

**Reproduction commit link:** https://github.com/AnhQuoc533/pathreview/commit/1e31039

**Reproduction summary:** I ran the test suite for ingestion pipeline by executing `make test-integration`. However, no test was ran and no file-based fixtures existed.

**PLAN.md link:** https://github.com/AnhQuoc533/pathreview/blob/test/18-ingestion-pipeline-tests/PLAN.md

**Blockers:**  
- The exact structure of `ParseResult` returned by parsers (need to verify metadata fields)
- The exact signature of `batch_processor.process()` and what it expects
- Whether `db_session.query()` in `_check_skip()` can be mocked directly or if it needs a spy


# Week 9 — Solution building & PR submission

## Check-in 1 (mid-week)
**Current progress:**  
- Collect sample data (fixtures) for the test suite
- Orchestrate fixtures in `tests/fixtures/sample_resumes/`
- Mock `vector_db`, `db_session`, and `EmbeddingProvider` in the test suite

**Next steps:** Complete the test suite by adding test cases for `ingest_resume()`, `ingest_readme()`, `ingest_repo_metadata()`.

**Blockers:**  
- Investigate which GitHub repository fields the `ingest_repo_metadata()` function needs to retrieve, inspect, and parse
- The correct way to create mock dependencies so that the test suite run smoothly


---

## Check-in 2 (end of week)
**PR link:** https://github.com/ascherj/pathreview/pull/719

**Branch:** `test/18-ingestion-pipeline-tests`

**What you built:** An end-to-end integration pipeline test suite exists at `tests/integration/test_ingestion_pipeline.py` and 
stress-tests the document ingestion features.
|         Method         | Test Count |                          Coverage                         |
|:-----------------------|:----------:|:----------------------------------------------------------|
|`ingest_resume() `      |     10     | PDF, Markdown, dedup, hash, error handling                |
|`ingest_readme()`       |      8     | Multiple repos, profile uniqueness, hash, error handling  |
|`ingest_repo_metadata()`|      8     | Multiple repos, language extraction, hash, error handling |
|Total                   |     26     |                                                           |

**Self-review confirmation:** [✅] make check passes  [✅] make test-unit passes

**Draft PR feedback received from:** *TF - Christopher Castro*


# Week 10 — Iteration & reflection

## Reviewer feedback

**Feedback received:** [✅] Yes  [ ] No — still awaiting review

**Summary of feedback:**
> Good coverage here, 25 tests across all three ingestion methods (resume, README, repo metadata) with dedup, hashing, and error handling. Two things to fix before this can move forward, though: it's still in Draft, so no one can review it yet, and the testing checklist is missing before/after numbers like your peers included, which would help a reviewer confirm no regressions were introduced.

**How you responded:**  
- Change the PR request from **Draft** to **Ready for Review**
- Add 1 more task to the testing checklist (code formatter passed) and mark it off
- Add **Demo Result** section to the PR, showcasing the result of my test suite
- Clarify the unit test results to confirm that no regressions occurred and that no additional errors were introduced.

---

## Reflection

**What was harder than you expected?**  
What challenged me the most were trying to understand the structure and the workflow of this project, as it did not contain a comprehensive documentation. Additionally, I found it quite hard to follow the pre-defined coding standards and pass all the commit checkers.

**What did you learn about working in a large codebase?**  
I have learned about the level of formality, the contribution process, and the coding conventions within a large, open-source codebase. Compared to building my own projects, contributing to a open-source, community-driven project requires compliance with well-established rules, standards, and procedures that protect and reinforce the professionalism, consistency, maintainability across the codebase.

**How did AI tools help — and where did they fall short?**  
AI tools helped me quickly analyze and understand the complexity of this codebase while navigating through the selected issue. They were especially useful for reading and understanding multiple files simultaneously, creating comprehensive test plans with edge cases, mocking setup, and detecting violations of coding standards.  
However, they occasionally fell short when understanding some of the edge cases, debugging linter/type checker failures, and specifying the exact exception type to expect.

**What would you do differently if you started over?**  
I would start early and plan my work carefully. More specifically, I would create a thorough checklist of all edge cases upfront, verify mock implementations with actual library behavior earlier, and spend more time reading existing test patterns in the unit test suites before writing my own.

**What are you most proud of from this module?**  
I am proud of the test suite I created for a feature in a large codebase and the PR I initiated for the first time on GitHub. This marks my first successful contribution to an open-source project and demonstrates my ability to write professional-grade test code. 