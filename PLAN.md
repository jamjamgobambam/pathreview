## Solution plan

**Issue:** [#101 — Add a "Copy link" button to share a public review summary](https://github.com/jamjamgobambam/pathreview/issues/101)

### Understand

The review page already includes a Share button, but the current implementation only copies `window.location.href`. This produces the normal authenticated review URL rather than a public sharing link.

When the copied URL is opened in an Incognito window, the review cannot be viewed without logging in. The backend `GET /reviews/{review_id}` route requires the current authenticated user and only returns reviews owned by that user.

The expected behavior is for a signed-in review owner to generate a separate public link for a completed review. Anyone with that link should be able to view a read-only review summary without logging in. The public link should stop working 30 days after it is generated.

### Map

The following files and modules are involved:

* `frontend/src/pages/ReviewPage.tsx`

  * Contains the current Share button.
  * Contains `handleShare()`, which currently copies the private browser URL.
  * Will need to call the sharing API and copy the generated public URL.
  * Will need loading, success, and error feedback.

* `frontend/src/services/api.ts`

  * Contains the existing frontend API client.
  * Will need a method for generating a public share link.
  * May need a method for retrieving a shared review without authentication.

* `frontend/src/services/shareService.ts`

  * Listed in the issue but does not appear in the files currently inspected.
  * May need to be created if the project expects sharing logic to live in a separate service.

* `api/routes/reviews.py`

  * Contains the authenticated review routes.
  * Will need an authenticated endpoint that allows the owner to generate a share link.
  * May need a separate public endpoint that does not use `get_current_user`.

* `core/models/review.py`

  * Must be inspected to determine whether share tokens and expiration timestamps should be added to the existing review model.

* Database migration files

  * May need a migration if the review model stores a share token and expiration date.

* Frontend routing files

  * Must be inspected to add a public route such as `/shared-reviews/:token`.

* Review-related backend tests

  * Must be inspected and updated with tests for creating and opening share links.

* Frontend tests

  * Must be inspected for existing page and service test patterns.

### Plan

1. Inspect the existing review data flow and project conventions.

   * Read `core/models/review.py`, `core/services/review_service.py`, `api/schemas/review.py`, the frontend router, Alembic migrations, and related tests.
   * Confirm how ownership, completion status, authentication, timestamps, and API responses are currently handled.
   * Determine whether `frontend/src/services/shareService.ts` should be created or whether sharing should remain in `api.ts`.

2. Design and implement backend share-link persistence and creation.

   * Choose between adding share fields to the existing review model or creating a separate share-link model based on current repository patterns.
   * Add the required migration if persistent fields are introduced.
   * Add an authenticated endpoint that verifies ownership and confirms the review status is `complete`.
   * Generate a unique, hard-to-guess token and store an expiration time 30 days after creation.
   * Decide whether an existing active link should be reused or replaced.

3. Implement public read-only review access.

   * Add a public endpoint that accepts a share token without using `get_current_user`.
   * Validate that the token exists, has not expired, and belongs to a completed review.
   * Return a limited public response containing only the fields required to display the review summary.
   * Return appropriate errors for invalid, expired, deleted, failed, or incomplete reviews.

4. Update the frontend sharing and public-view flow.

   * Replace the current `window.location.href` behavior in `ReviewPage.tsx`.
   * Call the share-link endpoint and copy the generated public URL.
   * Add loading, success, clipboard-failure, and API-error feedback.
   * Add an unauthenticated public route and read-only page that loads a review using the share token.
   * Handle invalid and expired links with a clear error state.

5. Add tests and run project checks.

   * Test link creation by the review owner.
   * Test rejection for another user’s review and for failed, pending, or incomplete reviews.
   * Test public access without authentication.
   * Test invalid and expired tokens.
   * Test that public responses do not expose private fields.
   * Test the frontend API method and Share button behavior.
   * Run `make check` and `make test-unit` before implementation is submitted.

### Inputs & outputs

#### Inputs

* An authenticated user.
* A review ID belonging to that user.
* A review with status `complete`.
* A public share token when opening the shared page.

#### Outputs

* A generated public link containing a unique share token.
* A link expiration time 30 days after generation.
* Clipboard confirmation after the frontend copies the URL.
* A read-only public review summary that works without login.
* An appropriate error response for expired, invalid, unauthorized, or non-complete reviews.

### Risks & unknowns

* The correct storage location for the share token and expiration timestamp is not yet confirmed. These values may belong on the `Review` model or in a separate share-link model.

* It is not yet clear whether generating a new link should reuse an existing active token or invalidate the old link and create a new one.

* The exact public frontend route has not been confirmed. A route such as `/shared-reviews/:token` may fit the issue, but the existing router conventions must be inspected first.

* The public API response must avoid exposing private user, profile, or internal processing data.

* The issue lists `frontend/src/services/shareService.ts`, but the current frontend uses `api.ts`. The repository should be checked to determine whether `shareService.ts` exists on another branch or is expected to be created.

* Adding database fields may require an Alembic migration. Existing migration conventions must be followed.

* Clipboard access can fail if the browser blocks permissions or the page is not running in a secure context.

### Edge cases

* The review ID does not exist.
* The authenticated user does not own the review.
* The review is still pending or processing.
* The review has a failed status.
* The review has no sections or no overall score.
* The share token is invalid.
* The share token has expired.
* The share token has been replaced or revoked.
* Two users attempt to generate links for the same review.
* The user clicks the Share button multiple times.
* The clipboard API fails.
* The public endpoint exposes more data than the read-only page requires.
* A review is deleted after a share link has been created.
* The system clock or timezone causes incorrect expiration behavior.
