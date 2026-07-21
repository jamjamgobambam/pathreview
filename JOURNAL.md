## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/13]

**Issue title:** [Add a content hash to detect unchanged documents and skip re-embedding]

**Tier:** [Tier 2] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]
The issue is that when a user re-submits the same README file without making any chnages the whole file still gets re-embbeded, leading to more unnessary API calls. A fix for this issue would be to create a hash of the README and only re-embed the file if the hash changes at all. To implement this fix, a hash for the readme will need to be processed at every upload and stored for future uploads. This will primarily effect the ingestion pipline

**Branch name:** [feat/13-add-conditional-hash-re-embedding]

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

This issue is right for me!