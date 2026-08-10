## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/18

**Issue title:** Add end-to-end ingestion test with a sample resume fixture
#18

**Tier:** [ ] Tier 1 [x] Tier 2 [ ] Tier 3

**Why this issue is right for me:** I've worked on unfamiliar codebases before, so a Tier 2 issue that spans a couple of modules is a reasonable step. I already located and read the exact code the issue touches (`ingest_resume()` in `pipeline.py`, and the existing parser tests), and I can trace the flow well enough to plan the test without guessing. There are no blockers on the issue, and I feel confident that I will be able to finish before the week 9 deadline.

**Problem summary:**
Right now the codebase only tests parsers in isolation. There's no test that checks the whole resume upload process work from start to finish. When someone uploads a resume, it's supposed to get parsed, split into chunks, turned into embeddings, and saved to the database, but nothing currently verifies all of those steps actually work together correctly. The tests/integration/ folder is empty, and there isn't a sample resume file set up to test with yet. Fixing this means writing a new test that uploads a real sample resume and checks it makes it all the way through the pipeline successfully. Also, there needs to be a sample resume file for the test to use. This issue/feature mainly in the ingestion pipeline code and the test folders. While reviewing the pipeline, I also noticed the database-recording step is still a placeholder and doesn't actually save anything yet, so I'm scoping my test to the parts that are implemented rather than testing against that unfinished part.

**Branch name:** test/18-ingestion-pipeline-integration

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

Add this section below your Week 7 entry in JOURNAL.md. Do not replace your previous entry!

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/CarlosSac/pathreview/commit/60d20d18121fa7bb694da07d8692905075ede5a7

**Reproduction summary:**
I ran ingest_resume() with a mocked db_session, the same way the existing unit tests mock it, and it reported skipped=True, chunk_count=0 on a brand new profile that had never been ingested before. Nothing was actually parsed, chunked, or embedded. I traced this to \_check_skip() in pipeline.py, which queries db_session.query("IngestedSource") using a string instead of the actual model class, so a mocked session always returns a truthy result and the pipeline thinks a match already exists.

**PLAN.md link:** https://github.com/CarlosSac/pathreview/blob/test/18-ingestion-pipeline-integration/PLAN.md

**Walkthrough video (recommended):** Not recorded this week.

**Blockers or open questions:**
Still deciding whether to work around the `_check_skip()` bug by configuring the mock explicitly in the test, or fix it directly in `pipeline.py`. Leaning toward the workaround, since it keeps this PR scoped to adding a test rather than fixing an unrelated pipeline bug, but open to feedback on that call before I start Week 9.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
3 of 5 tasks from PLAN.md are done. I fixed the mock setup so the test gets past the pipeline bug and actually passes now. I added a check that embeddings really get stored, not just chunked. I also added a second sample resume (one with no work experience section) and a test for it.

**Next steps:**
Add a test for the "skip if already ingested" case, and then clean up the test file and make sure everything passes before opening a PR.

**Blockers:**
None right now.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/810

**Branch:** `test/18-ingestion-pipeline-integration`

**What you built:**
An end-to-end integration test suite for the resume ingestion pipeline (parse, chunk, embed, store), using sample resume fixtures. Along the way I found and documented a real bug in the pipeline's already-ingested check, and worked around it in the tests rather than fixing the pipeline itself, since that's out of scope for this issue.

**Tests added or updated:**
Added `tests/integration/test_ingestion_pipeline.py` with 3 tests: the full ingestion flow on a normal resume, the same flow on a resume with no work experience section, and the already-ingested skip path. Added two fixtures in `tests/fixtures/sample_resumes/` (`resume.txt`, `resume_no_experience.txt`).

**Self-review confirmation:** [x] make check passes [x] make test-unit passes
(Both have pre-existing failures/errors unrelated to this change, documented in the PR's Notes for Reviewers. Confirmed via `git diff --stat main...HEAD` that none of the affected files were touched here, and verified under a clean Python 3.11 environment per SETUP.md.)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes [ ] No — still awaiting review

**Summary of feedback:**
Technically I did receive feedback but it wasn't a human review. GitHub's Copilot left an automated review, the review said that it is "🟢 Ready to approve," and noted that the changes are additive (tests, fixtures, a small pre-commit config tweak) and align with the pipeline's current behavior, including the mocked `db_session` skip-check, without touching risky production code. That automated review doesn't count toward the repo's actual merge requirement, so I'm still waiting on a real reviewer.

**How you responded:**
No changes were needed in response, Copilot's note matched what I already documented in the PR's Notes for Reviewers section, so it confirmed rather than changed anything.

---

### Reflection

**What was harder than you expected?**
Issue #18 was framed as a testing gap, not a bug, so I expected Week 8's "reproduce the issue" step to just build understanding of the codebase, not to hunt for a real defect. But when I ran `IngestionPipeline.ingest_resume()` locally with a mocked `db_session`, it reported `skipped=True` for a resume that had never been ingested before. Tracking that down took longer than writing the actual test assertions: `_check_skip()` was querying `db_session.query("IngestedSource")` with a string instead of the model class, and the mock's default truthy return value made the pipeline silently skip ingestion instead of raising any error. On top of that, `make typecheck` kept crashing on me until I figured out I had the wrong Python version installed, not a problem with my code.

**What did you learn about working in a large codebase?**
The biggest adjustment was realizing how much of my "did I break anything" story had to be proven, not assumed. `make test-unit` had 53 pre-existing failures and `make lint` had 182 pre-existing errors before I touched anything, and I had to explicitly diff my branch against `main` to prove none of those were mine before I could honestly check the self-review boxes. In a solo project I'd never have needed that. I also learned that conventions documented in `CONTRIBUTING.md` (commit message scopes, branch naming) aren't optional style points, they're something a reviewer or grader will actually check, to the point that I ended up rewriting my own commit history to add missing scopes before opening the PR.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for tracing execution paths quickly, e.g. confirming exactly how `BatchEmbeddingProcessor._store_embedding()` calls `vector_db.add()` so my assertions were grounded in the real API instead of a guess, and for diagnosing the mypy/numpy crash by actually running commands and comparing environments rather than speculating. It fell short on the judgment calls that were actually mine to make: whether to fix `_check_skip()` or work around it in tests, whether it was safe to rewrite already-pushed git history, and whether to open the PR as a draft or go straight to ready-for-review given I was already past the intended timeline. Those needed context about my actual constraints, not just technical correctness.

**What would you do differently if you started over?**
I'd run `make check` and `make test-unit` on a clean checkout in Week 7, before writing any code, to get the pre-existing-failure baseline up front instead of discovering it while trying to finish Week 9. I'd also open the PR as a draft earlier in the week to actually get human feedback, instead of ending up choosing ready-for-review mainly because I was behind schedule.

**What are you most proud of from this module?**
Finding the `_check_skip()` bug wasn't something the issue asked for, I found it by actually running the pipeline instead of just writing tests against my assumptions of how it should behave. I'm proud that instead of quietly working around it or quietly fixing it, I documented it clearly in PLAN.md, the PR description, and JOURNAL.md, and made a deliberate, explained scope decision to leave it for someone else to pick up as its own issue.
