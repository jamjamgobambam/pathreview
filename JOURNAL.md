## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/163

**Issue title:** Review creation does not verify profile ownership

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

**Problem summary:**
The POST /reviews endpoint accepts a profile_id, but core/services/review_service.py does not verify that the profile belongs to the authenticated user. As a result, a user who knows another user’s profile UUID could create a review for that profile. A successful fix will validate profile ownership before creating the review and reject unauthorized requests while preserving normal review creation.

**Branch name:** fix/163/Review-creation-does-not-verify-profile-ownership

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger