## Solution plan

**Issue:**  POST /reviews endpoint has no test for when the profile has no ingested documents (https://github.com/ascherj/pathreview/issues/88)

### Understand
The root cause of this issue is that the /reviews endpoint currently lacks a test case for the scenario where a user's profile exists but has no ingested documents, as in the profile may have entirely empty attributes (github username, resume filename, etc. are all empty). This means that if a user with an empty profile attempts to access the /reviews endpoint, the application may not handle this case properly, potentially leading to runtime errors or unexpected behavior.

### Map
routes/reviews.py: This file contains the logic for handling the POST /reviews endpoint. It is responsible for processing requests related to reviews, including checking if a user's profile has ingested documents.
core/models/profile.py: This file defines the Profile model, which represents a user's profile in the application. It includes attributes related to the user's documents.
core/services/review_service.py: This file contains the business logic for handling the _run_ingestion_pipeline function, which is responsible for processing ingested documents and generating reviews. It includes checks for the presence of ingested documents before proceeding with review generation.


### Plan
- Add a route-level guard in the api/routes/reviews.py file to check if the profile has ingested documents before proceeding with the review generation process, as the current implementation does not validate the empty-profile case before starting the review. If the profile has no ingested documents, write a log message warning that indicates this scenario and raise an HTTPException with a 400 status code and an appropriate error message.

- Create a new test file named test_review_routes.py inside the tests/integration directory.
- inside the test file, add a docstring at the very top of the file that describes the purpose of the test file and what it aims to test.
- define the necessary imports and setup for testing the /reviews endpoint.
- define class TestReviewRoutes to group the test cases related to the /reviews endpoint.
- Define any necessary setup methods to create a test client and any required fixtures for simulating user profiles with and without ingested documents.
- Within the TestReviewRoutes class, define a test function named test_post_reviews_no_documents.
- inside the test_post_reviews_no_documents function, simulate a POST request to the /reviews endpoint with a profile that has no ingested documents.
- this test function should assert that the logs return a warning message indicating that there are no documents available for review, and that the response status code is 400.

### Inputs & outputs
For this test function, the input will take in a client request to the /reviews endpoint with a profile that has no ingested documents, and the caplog fixture will be used to capture the log messages generated during the request. The expected output is that the logs should contain a warning message indicating that there are no documents available for review, and the response status code should be 400.

### Risks & unknowns

Though I was unsure that I was going to touch anything else besides making a test file, I realized that I was going to have to make a small change to the api/routes/reviews.py file in order to add a guard clause that checks if the profile has ingested documents before proceeding with the review generation process. This change is necessary to ensure that the endpoint behaves correctly when a user with an empty profile attempts to access it.

### Edge cases

This test will primarily target a classic edge case where a user has a profile but has not ingested any documents. The test will ensure that the /reviews endpoint handles this scenario gracefully by returning an appropriate error message and status code, rather than crashing.