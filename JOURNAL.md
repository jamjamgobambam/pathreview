## Week 7 — Issue selection


**Issue link:** https://github.com/ascherj/pathreview/issues/88


**Issue title:** `POST /reviews` endpoint has no test for when the profile has no ingested documents


**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3


**Problem summary:**
From reading the issue, it looks like `POST /reviews` is missing a test for the scenario where a profile exists but no resume or repositories have been ingested yet. Since the review generator wouldn't have any data to work with, I'll verify how the endpoint currently handles that situation and add a test in `tests/unit/test_review_routes.py` to ensure it returns an appropriate error rather than crashing.


**Branch name:** test/88-review-endpoint-no-ingested-content


**Setup confirmation:** [x] App runs locally at localhost:5173


**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/jupitersnow1/pathreview/commit/4323e66 

**Reproduction summary:**
I called the review pipeline directly with a mock profile that had no GitHub, portfolio, or resume data and confirmed the ingestion step returned an empty source list. Even with no sources to process, the downstream generation steps still produced the same hardcoded feedback, and the review completed successfully instead of reporting an error.

**PLAN.md link:** https://github.com/jupitersnow1/pathreview/blob/test/88-review-endpoint-no-ingested-content/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
I'm still deciding where the validation should happen. One option is to check in the create_review endpoint so the request fails immediately before a review record is created. The other option is to let the review be created and have process_review detect the missing data, mark the review as status="failed", and include a clear error message.

Right now I'm leaning toward validating in the endpoint because it prevents creating a misleading pending review in the first place. I just want to make sure that's the approach the frontend is expecting when a submission doesn't include enough information to generate a review.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the fix outlined in PLAN.md by adding check_has_ingested_sources in core/services/review_service.py and calling it from create_review_endpoint in api/routes/reviews.py. Now, if a profile has no ingested sources, the endpoint returns a 400 Bad Request with the message "Profile has no ingested content" before creating a review or scheduling process_review.

I also added unit tests in tests/unit/test_review_routes.py to cover both scenarios: rejecting requests when there are no ingested sources and confirming the normal review creation flow still works when ingested content exists.

Steps 1–4 from PLAN.md are complete. I looked into the stretch service-layer test, but decided it wasn't needed because the new guard prevents process_review from being scheduled in the first place, so the downstream orchestration code is no longer reachable.

**Next steps:**
Run make check and make test-unit, compare any failures against the existing baseline, split the work into focused commits, and open a draft PR for feedback before submitting the final version.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/492

**Branch:** test/88-review-endpoint-no-ingested-content

**What you built:**
Added a guard to POST /reviews that returns a 400 Bad Request when the target profile has no IngestedSource records, preventing the endpoint from creating a review with placeholder feedback.

**Tests added or updated:**
`tests/unit/test_review_routes.py` (new) — tests the 400-rejection path and the happy-path pending-review creation for `create_review_endpoint`.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** [name or Slack handle, or "none"]

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review came in.

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
Honestly, the biggest thing that surprised me was just how big the codebase was. Even though this was a "small" guard-clause change, I couldn't just look at one file and make the change. I had to trace through the request lifecycle, including ingestion, review creation, and the guards connecting everything, to make sure the change was actually safe. Building that mental map of how everything connected ended up taking longer than actually writing the fix.

**What did you learn about working in a large codebase?**
I learned that clear communication is just as important as the code itself. When you're working on your own project, you can usually keep the context in your head and figure things out as you go. But in someone else's codebase, no one else has that context, so a vague PR description, commit message, or comment forces a reviewer to reconstruct your reasoning from scratch. I didn't get reviewer feedback this module to confirm that firsthand, but writing PLAN.md and my PR description made me notice how much I was tempted to skip explaining a decision because it was obvious to me — even though it wouldn't be obvious to someone reading the code for the first time. That's more a lesson I anticipated than one I had proven back to me, but it changed how carefully I wrote those docs.

**How did AI tools help — and where did they fall short?**
AI was helpful for getting through some of the longer files, especially things in the ingestion folder like pipeline.py and the chunking strategies. It helped me get a general idea of what a module was doing without having to read every single line first, which saved me some time. I also used it to dig deeper once I had narrowed down the part of the code I actually needed to understand. Where it fell short was knowing whether a change was truly safe. I still had to trace through the code myself and understand how everything connected instead of just relying on an AI-generated summary.

**What would you do differently if you started over?**
I think I would change how I picked the issue. I chose a Tier 1 issue, and while it did require me to trace through the ingestion and review-creation flow to make sure I implemented it correctly, it wasn't actually as difficult as I expected once I understood the codebase. Knowing that now, I probably would have been more willing to pick a higher-tier issue from the beginning. I think I had more room to challenge myself than I gave myself credit for.

**What are you most proud of from this module?**
I'm most proud of actually learning how to contribute to an open-source project — the whole workflow of reproducing an issue, planning a fix, and getting it into a PR against someone else's codebase, not just writing code. Before this module I'd only ever worked in projects I built myself, so I never had to reason about someone else's existing architecture or write for a reviewer instead of just for myself. Going through that process end to end on a real repo is the skill I'm most proud of picking up.
