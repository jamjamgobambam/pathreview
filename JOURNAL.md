## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/11

**Issue title:** Add support for ingesting a portfolio website URL

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
Right now PathReview can use GitHub and resume data, but it cannot pull information from a user’s personal portfolio website. That means project descriptions, bios, and other useful context on a portfolio site are currently left out of the review. This issue would add a web parser that fetches and extracts relevant text from a submitted URL, then passes that content through the existing ingestion pipeline. A successful fix would store that portfolio content in the vector store alongside the user’s other profile data.

**Branch name:** feat/11-portfolio-url-ingestion

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ItzRae/pathreview/commit/103ecae18838f6b23b87fa79f2afad92ee71201a

**Reproduction summary:**
I created a profile and confirmed that the app already lets users enter a portfolio URL. However, after tracing the ingestion code, I found that the URL is only stored on the profile and is never fetched or processed. The pipeline currently supports resumes, READMEs, and repository metadata, but there is no web parser or portfolio ingestion flow to add website content to the vector store.

**PLAN.md link:** https://github.com/ItzRae/pathreview/blob/feat/11-portfolio-url-ingestion/PLAN.md

**Blockers or open questions:** None at the moment. My remaining work is primarily implementation and tracing the existing ingestion flow to determine the correct integration point.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the core portfolio website ingestion feature. I added a new `WebParser` to extract readable text and metadata from HTML pages, integrated a new `ingest_portfolio()` method into the ingestion pipeline, and added unit tests for both the parser and pipeline. I also verified the implementation by reproducing the issue locally and comparing it with the existing ingestion architecture.

**Next steps:**
Run final project checks, open a draft PR for feedback, address any review comments, and prepare the PR for final submission.

**Blockers:**
No major blockers. While tracing the codebase, I found that the existing resume and README ingestion methods are not currently wired into an application-level workflow either, so I began drafting my PR to ask/confirm whether that integration is expected as part of this issue.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/783

**Branch:** `feat/11-portfolio-url-ingestion`

**What you built:**
Implemented support for ingesting portfolio websites into the existing ingestion pipeline. The new `WebParser` extracts readable content and metadata from HTML pages, and `ingest_portfolio()` fetches portfolio pages, processes them through the existing chunking and embedding workflow, and stores the resulting content with portfolio-specific metadata.

**Tests added or updated:**
- `tests/unit/test_web_parser.py` — verifies HTML parsing, metadata extraction, ignored elements, and invalid input handling.
- `tests/unit/test_ingestion_pipeline.py` — verifies successful portfolio ingestion, metadata propagation, invalid URLs, empty pages, duplicate sources, and request failures.

**Self-review confirmation:**
- [x] make check passes (no new failures introduced beyond documented pre-existing mypy issues)
- [x] make test-unit passes

**Draft PR feedback received from:**
None (awaiting feedback)

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
My reviewer pointed out three smaller issues with the web parser: the page title was also being included in the extracted body text, `source_type` was being stored redundantly in both the metadata and `ParseResult`, and an unclosed `<script>` tag could cause the parser to ignore the rest of the page. The last point was especially useful because it was an edge case I had not considered in my original tests.

**How you responded:**
I reproduced the unclosed `<script>` issue with a new test before changing the implementation, then updated the parser to handle the malformed HTML case. I also prevented title text from being duplicated in the body and changed the metadata structure to be consistent with the existing parsers. I added/updated tests for these cases, reran the checks, and pushed the fixes to my existing PR.

---

### Reflection

**What was harder than you expected?**
Understanding the boundaries of the issue was harder than the actual HTML parsing. I initially assumed there would be an existing profile workflow where I could simply plug in portfolio ingestion, but while tracing the code I found that the existing resume and README ingestion methods were not wired into an application-level trigger either. I had to figure out what belonged in my issue versus what would unnecessarily expand its scope. I also underestimated how many edge cases even a relatively small web parser could have, especially with malformed HTML.


**What did you learn about working in a large codebase?**
I learned that contributing to someone else's codebase is less about finding a solution that works in isolation and more about understanding and following the patterns that are already there. I spent a lot more time tracing existing parsers, the ingestion pipeline, tests, typing conventions, and contribution guidelines than I normally would when building my own project. I also learned not to assume that every part of a codebase is complete or perfectly consistent. There were existing type-checking failures and partially connected workflows, so I had to distinguish between problems caused by my changes and problems that were already there.

**How did AI tools help — and where did they fall short?**
AI was most useful for helping me navigate an unfamiliar codebase, understand existing patterns, think through test cases, and debug tooling issues like my Python environment and pre-commit checks. It also helped me reason about how the new parser should fit into the existing ingestion pipeline. Where it fell short was knowing the intended scope and architecture of the repository. For example, I still needed to inspect the code myself to discover that the existing ingestion methods were not connected to an application-level trigger. I also needed peer review to catch edge cases like the unclosed `<script>` tag that I had not originally tested


**What would you do differently if you started over?**
I would spend more time tracing the complete existing workflow before writing my implementation - I started with the files listed in the issue, but mapping where data entered the system, how the existing ingestion methods were used, and what tests already existed earlier would have made my plan more precise. I would also run the repository-wide linting and type checks before making any changes so I had a clearer baseline of which failures were pre-existing.

**What are you most proud of from this module?**
I'm most proud that I took on a Tier 2 issue even though this was my first time working through an opensource-style contribution workflow. I was able to go from reproducing a feature gap and navigating an unfamiliar codebase to implementing and testing the feature, opening a structured PR, getting peer feedback, reproducing an edge case from that feedback, and iterating on the implementation instead of treating the first working version as finished.