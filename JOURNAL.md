## Week 7 — Issue selection

---

### Issue 1

**Issue link:** https://github.com/ascherj/pathreview/issues/163

**Issue title:** Review creation does not verify profile ownership

**Tier:** 1

**Problem summary:**

Inside the `create_review_endpoint` route, the profile id and user id are passed into `create_review` but the system doesn't check wheater the the user owns this profile, causing review instancing where the current user reviewed themselves. With a fix, it'll avoid self-reported reviews and redundant code.

**Branch name:** fix/163-review-creation-does-not-verify-profile-ownership

**Setup confirmation:** [✅] App runs locally at localhost:5173

**Cohort ledger:** [✅] Issue added to cohort ledger

---


### Issue 2

**Issue link:** https://github.com/ascherj/pathreview/issues/47

**Issue title:** Agent state isn't persisted across API restarts, causing in-progress reviews to be lost

**Tier:** 3

**Problem summary:**

When the agent loops through reviews inside `orchestrator.run()`, it appends to `result` but doesnt save each loop. So when a review crashes, the whole system just loses the reviews. Originally the plan was to make a `CrashedReview(Base)` model fron scratch, but with further reading I realized `SessionStore` already exist. The solution was just to save after each review, which means adding to `SessionStore`. 


**Branch name:** fix/47-agent-state-isnt-persisted-across-restarts

**Setup confirmation:** [✅] App runs locally at localhost:5173

**Cohort ledger:** [✅] Issue added to cohort ledger

---