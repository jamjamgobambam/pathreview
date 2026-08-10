## Solution plan

**Issue:** Add a "Copy link" button to share a public review summary
https://github.com/ascherj/pathreview/issues/101

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

The main feature of the issue is not implemented. The share button's link should be publicly viewable and should generate a link that expires. As of right now, the link is not publicly viewable as the user needs to be signed in to at least view a review page. Additionally, there is not any logic that handles link expiry. The link should be different than the href link as the main user still needs to be able to access after expiration.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

reviews.py -- need to implement public/private setting and removing expiring links
ReviewPage.tsx -- link is already generated, but needs to handle privacy
App.tsx -- need to be able to handle user privacy. ie user needs to login to view review page

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. Implement public sharable link by adding privacy row to review table, with expiration date (30 days)
2. Ensure page is viewable by any user (not logged in)
3. Write test cases and ensure that link is properly destroyed.
4. Ensure original user is able to view the page. (review is not entirely destroyed)

### Inputs & outputs
What does your fix take as input? What should it produce or change?

The fix takes the user's input to the share button of the current review as the input. This should change the review schema's privacy row to public and generate an expiry date. When the page has expired and any user attempts to view the page, the expiry date will be checked and the privacy setting will be set to false. The generated link will be destroyed as a result.

### Risks & unknowns
What could go wrong? What are you still unsure about?

The link needs to be unique, thus there needs to be checks to ensure links are not duplicated between href and the generated links. I'm unsure about if generating a new link is neccesary. I'm also unsure about how to handle the privacy issue. The time stamps need to be standardized at ONE time zone I think also to help eliminate time-related issues. 

### Edge cases
What inputs or states should your fix handle gracefully?

The current date needs to be handled gracefully. The privacy setting should also be handled also. Additionally, when the user re-prompts to share the link, the link should stay the same and a new link should not be regenerated.