## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/163

**Issue title:** Review creation does not verify profile ownership

**Tier:** [x] Tier 2

**Problem summary:**
The POST /reviews endpoint accepts an authenticated user's request but doesn't verify that the profile belongs to that user. An attacker can create reviews on any profile by supplying another user's profile ID. The fix should add ownership checks to create_review(), matching the scoping already used in get_review() and list_reviews().

**Branch name:** fix/163-review-profile-ownership

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/AdetayoKalejaiye/pathreview/commit/6171fe1

**Reproduction summary:**
Added test `test_create_review_missing_ownership_check()` documenting the vulnerability: `create_review()` service accepts any `profile_id` without verifying it belongs to the current user. Unlike `get_review()` and `list_reviews()` which join with Profile and filter by user ownership, `create_review()` has no ownership check.

**PLAN.md link:** [PLAN.md](./PLAN.md)

**Walkthrough video (recommended):** (Not recorded)

**Blockers or open questions:**
- Clarify if non-existent profile should return 403 or 404
- Check if background task `process_review()` needs ownership verification too

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
- ✅ Sub-task 1: Added ownership verification to `create_review()` service function
  - Queries Profile by id and verifies `profile.user_id == user_id`
  - Returns None if ownership check fails
- ✅ Sub-task 2: Updated `create_review_endpoint()` to handle ownership verification
  - Checks if `create_review()` returns None
  - Raises HTTPException with 403 Forbidden status code
- ✅ Sub-task 3 (partial): Added comprehensive tests
  - `test_create_review_rejects_wrong_owner`: Verifies ownership check blocks attacker
  - `test_create_review_allows_owner`: Verifies owner can create reviews
  - `test_create_review_returns_none_for_nonexistent_profile`: Verifies non-existent profile handling

**Next steps:**
- Run make check and make test-unit to verify all tests pass
- Get peer/mentor feedback on draft PR
- Finalize PR and submit

**Blockers:**
None - implementation on track

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/703

**Branch:** fix/163-review-profile-ownership

**What you built:**
Added profile ownership verification to the review creation endpoint (issue #163). The `create_review()` service now queries the Profile table to verify the profile belongs to the requesting user before creating a review. If ownership verification fails, the endpoint returns 403 Forbidden, preventing unauthorized users from creating reviews on other users' profiles.

**Tests added or updated:**
Updated `tests/unit/test_review_service.py` with three new tests:
- `test_create_review_rejects_wrong_owner`: Verifies attacker cannot create reviews on others' profiles
- `test_create_review_allows_owner`: Verifies owner can successfully create reviews on their profile
- `test_create_review_returns_none_for_nonexistent_profile`: Verifies proper handling of non-existent profiles

**Self-review confirmation:** 
- [ ] make check passes
- [ ] make test-unit passes

**Draft PR feedback received from:** None (PR opened as draft for early feedback)

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] No — still awaiting review

**Summary of feedback:**
No review feedback received during Summer 2026 (reviewer feedback not available this session). PR remains open awaiting maintainer review.

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
The hardest part was understanding the scope of the ownership check. Initially, I wasn't sure whether the fix should only be in the service layer or also in the endpoint. I also had to think carefully about UUID type conversions (the database stores UUIDs as strings while the endpoint passes UUID objects), which required careful handling in the comparison logic. Additionally, understanding how SQLAlchemy handles type coercion between different UUID representations took time to get right. Finally, getting the gh CLI tool to work for creating the PR was unexpectedly difficult — ended up needing to manually create the PR through the web interface.

**What did you learn about working in a large codebase?**
Working in PathReview taught me that consistency and patterns matter tremendously. The existing `get_review()` and `list_reviews()` functions already had the right security pattern (joining with Profile and filtering by user_id), and my job was to apply that same pattern to `create_review()`. In a large codebase, you're not inventing solutions — you're reading existing code to find the established patterns and replicating them. I also learned that every change needs tests, and those tests should match existing test patterns in the same module. Large codebases enforce conventions through their structure and test suite, and that's actually helpful for maintaining consistency.

**How did AI tools help — and where did they fall short?**
AI was invaluable for exploring the codebase quickly — when I needed to understand the Review and Profile models, their relationships, and how authentication worked, I could ask targeted questions and get code references with line numbers. AI also helped me understand the existing patterns in `get_review()` and `list_reviews()` so I could replicate them correctly. However, AI fell short on two things: (1) Understanding the specific type conversions needed between UUID objects and string UUIDs stored in the database — I had to debug that myself by reasoning through the SQLAlchemy mapping, and (2) Creating a proper PR through the gh CLI — after several attempts failed, I had to fall back to manual creation. AI is great at pattern recognition and code navigation, but less reliable for tool-specific operations and subtle type system details.

**What would you do differently if you started over?**
I would fetch the upstream repository earlier so that git and gh have the proper remote setup. I spent time debugging why gh wouldn't create the PR when the real issue was that upstream wasn't configured yet. I'd also spend more time reading CONTRIBUTING.md upfront to understand the exact testing and linting requirements before starting implementation. Finally, I would test the UUID type conversion issue more carefully earlier on — I almost implemented a solution that wouldn't have worked due to type mismatches. Testing assumptions about types earlier would have saved iteration time.

**What are you most proud of from this module?**
I'm most proud of how thoroughly I documented the vulnerability and my solution approach in PLAN.md. Even though the actual code change was relatively small (adding a profile ownership check), understanding why it was needed, where it belonged, what could go wrong, and what edge cases to handle required real thought. The planning discipline — writing out the Understand/Map/Plan/Inputs/Risks/EdgeCases structure before touching code — forced me to think deeply about the problem and catch issues (like the UUID type handling) that I might have missed otherwise. That structured planning approach is something I'll carry forward to future contributions.