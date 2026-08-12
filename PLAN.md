# Implementation Plan: Issue #43 (Clear Agent Session State)

## 1. What needs to change
Currently, the AI agent's session state persists across multiple reviews for the same user, causing context leakage from previous sessions. To fix this, I need to clear the Redis-backed session data at the start of a new review. By utilizing the existing `delete()` method in `session_storage.py`, I can wipe the user's specific session key just before a new review is initialized, ensuring the agent starts with a blank slate.

## 2. Specific files and components involved
* `session_storage.py` - Contains the `SessionStore` class, specifically the `delete(self, session_id)` method which interacts with Redis.
* The API/Routing file handling new reviews (likely `api/reviews.py`, `routes.py`, or similar) - This is where the `delete` method needs to be injected.
* The Agent Initialization file (e.g., `agent.py`) - To verify the agent is requesting a fresh state.

## 3. Actionable Sub-tasks
1. **Locate the specific review creation endpoint:** Find the exact API route or controller function that executes when a user clicks "Start New Review".
2. **Inject the cache wipe:** Inside that creation function, import or access the `SessionStore` instance and call `session_store.delete(session_id)` (or the equivalent user-bound session identifier) before generating the new agent context.
3. **Verify Redis clearance:** Add temporary debug logs or check the Redis CLI directly to confirm that `self.redis.delete(key)` successfully removes the old data.
4. **Run sequential tests:** Complete one full review, immediately start a second review, and confirm via the UI that no previous chat history or memory is retained by the agent.

## 4. Inputs, Outputs, Risks, and Unknowns
* **Inputs:** The `session_id` (or `user_id` if they are mapped 1:1) passed to `SessionStore.delete()`.
* **Outputs:** A boolean or `None` from the Redis deletion execution, resulting in an empty state dict for the new review.
* **Risks/Unknowns:** * *Concurrency Risk:* If the `session_id` is actually tied globally to the `user_id`, calling `delete()` might wipe out the state of a *different* review if the user has two active reviews open in separate browser tabs. I need to verify how `session_id` is generated.
  * *Silent Failures:* The `delete()` method in `session_storage.py` uses a generic `except Exception as e:` block that only logs the error. If Redis fails to delete the key, the app won't crash, but the bug will persist silently.

## 5. Concrete Edge Cases to Handle
1. **Mid-review page refreshes:** If a user refreshes their browser page in the middle of a review, the frontend might trigger a mount effect. The state wipe must be strictly bound to *creating* a new review, not just loading the page, otherwise users will lose their progress on refresh.
2. **Expired/Already Deleted Sessions:** If the previous session has already expired via the TTL (`ttl_seconds = 3600`), calling `delete()` on a non-existent key must not throw a 500 server error. The code must handle attempting to clear an already-empty cache gracefully.