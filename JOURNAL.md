## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/36
**Issue title:** Architecture doc doesn't explain the hybrid retrieval scoring formula
**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3 <!-- Put an x in the correct bracket -->

**Problem summary:**
docs/ARCHITECTURE.md contains a high level explanation of hybrid retrieval and how it's incorporated in this project, but doesn't explain the formula or the default wiehgts. A successful fix would be going more in depth in how the hybrid retrieval process works, and adding a section explaining the scoring logic. An example should also be included.
[Write 3–5 sentences in your own words explaining what is broken or missing, what a successful fix looks like, and which part of the codebase it touches.]

**"Is this right for me?" Reasoning:**
This issue is right for me because I have never worked on an open source issue. This issue was labeled with tier 1 and good first issue, so it seemed like a good option. I also want to learn more in depth about hybrid retrieval, so completely this issue allows me to get more experience with that topic.

[Briefly state your scope reasoning here based on the checklist guidelines.]

**Branch name:** `docs/36-hybrid-retrieval-scoring`
**Setup confirmation:** [x] App runs locally at localhost:5173
**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproducing the Issue:** confirmed ARCHITECTURE.md line 60 mentions hybrid retrieval but doesn't outline or explain the formula defined in hybrid.py:78-81
