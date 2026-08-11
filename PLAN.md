## Solution plan

**Issue:** 

Implement a webhook system that notifies users when their review is ready.
https://github.com/ascherj/pathreview/issues/87

### Understand

#### Background

For long running reviews, clients currently need to poll against `GET "/{review_id}/status"` in order to get the status of a review. Instead of constant polling, setting up a webhook allows for a hands off approach where the webhook is responsible for notifying the callback URL once a review is completed and all the client needs to do is provide a callback URL to which the webhook sends the notifications to.

#### Investigation into webhooks

FastAPI does not have a standard way of defining a webhook and leaves it to the developer. Looking into`review_service.py`, it already uses `async await` for processing reviews in the background and since these webhooks are meant to be asynchronous anyway, these patterns can be used here as well since callbacks are standard I/O operations done by the webhook where notifications sent may not be reliably received or received at all by the client. The following are the basic components needed for a functioning webhook: 

***Registration***

    FastAPI provides a way to document the schema of a webhook for clients to use, using the decorator @app.webhooks

        ``` python
        @app.webhooks.post("new-subscription")
        def new_subscription(body: Subscription):
        """
        When a new user subscribes to your service we'll send you a POST request with this
        data to the URL that you register for the event `new-subscription` in the dashboard.
        """
        ```
    Note that this is not a template for setting up the webhooks.

    The basic requirements to register a URL requires accepting a callback URL and storing it into a database along with a cache for faster processing.
    Depending on who the notifications needs to be sent to and what needs to be sent, these URLs can be created and monitored at that level.

***Event Source***

    The webhook requires a schema that defines what events the webhook listens for i.e CRUD operations on a database, operation statuses etc.

***Retries and error handling***

    Since there are two delivery endpoints i.e webhook and callback URL, errors are possible when sending and receiving notifications. We should assume that neither are reliable and handle accordingly. The goal is to allow the system to retry failed attempts, but not indefintely to the point that the system cannot recover i.e Retries with backoff and jitter with a timeout.

***Idempotency handling***

    In order to allow the callback URL to handle duplicated requests resulting from system or network failures, the webhook should provide an idempotency key for the callback URL to provide idempotency on their end. This key should include stable identifiers that would not change for each call.

### Map

api/routes/ (new webhooks.py defining routes for registering callback URLs)
api/schemas/ (new Callback and Notification Schemas)
core/services/ (new webhook_service.py for monitoring review status and sending notifications to the callback URL)
core/models/ (new Callback and Notification models for storing callback URL details)
tests/unit/ (new tests for webhooks, callbacks in test_review_service.py and test_callback.py)

### Plan

This section will discuss the scope and the step by step plan. The aim is to setup a basic webhook that can register and store callback URLs, send notifications as payloads to the callback URL for the user and handle errors with a simple retry with limited attempts, with a timeout for each attempt. 

#### Scope

Webhook:
- Simple retry with limit and timeout.
- Database for storing callback details. Updates are not allowed, but deletes are.
- Error handling for timeout, retries.
- Idempotency handling to allow clients to manage duplicated or missing payloads.
- Documentation.

Callback:
- URLs are preset
- Testing end to end from registration to notification.
- Documentation.

Advanced features like caching URLs, payload verification at callback, advanced retry methods can be scoped out into future work as these are more complex to implement (i.e cache refresh, cache eviction methods, setting up secret keys for signing, testing retries with backoff depending on latencies etc) and require extensive testing, which is beyond the scope and time mentioned in the issue.

#### Step by Step

1. Read `api/routes/review.py` and `core/services/review_service.py` to understand how to setup a route and a service asynchronously, and how to setup error handling.
2. Read  `tests/unit/test_review_service` to understand how the tests are setup for mocking and relevant test cases.
3. Read  `api/schemas` to understand how the Pydantic models are setup for API responses.
4. Run `make test-unit` before making any changes. 
4. In `core/models`, create Callback and Notification as `Callback.py` and `Notification.py`.
5. In `api/routes`, create a `webhook.py` route.
6. In `core/services`, create a `webhook_service.py` service.
7. In `tests/test_review_service`, setup tests for webhooks. Create a new `test_callback.py` file to do the callback testing only(not implementation).
8. Run `make test-unit` to make sure the new changes work.
9. Run `make check` to verify lint, formatting, and types are clean.
10. Document new webhook changes and an example for setting up a webhook in `API.md`, followed by a simple client setup to get notifications.

### Inputs & outputs

#### Callback and Notification Data model

Callback:

callback_id: <uuid generated>
user_id: <get from client>
profile_id: <get from client>
url: <string given by the client through the API>
created: <date>

Notification:

notification_id: <user_id + profile_id + review_id>
callback_id: <from Callback Model>
review_id: <get directly from process_review>
created: <date>
last_sent: <date>
last_ack: <date>
delivery_status: <success, fail, retry>

#### Pydantic Models

Callback

Notification

#### Webhook Route

The new route has the following methods:

1. register_callback(user_id, profile_id, url):

This gets the url from the client along with the user_id and profile id, calls set_callback_url to update the Callback record and returns a response based on success or failure. 
2. set_callback_url(user_id, profile_id, url):

This creates a Callback record with the user_id, profile_id, url provided, commits to the database and return a response.
3. delete_callback_url(user_id, profile_id):

This deletes the callback record associated with the above parameters.

#### Webhook Service

##### Functions

1. notify_callback_on_review_completed(user_id, profile_id, review_id):

This webhook service gets invoked from `process_reviews` in `review_service.py`, where the service is awaited without blocking process_reviews. 
This fetches the user_id based on the review_id and profile_id and looks up the Callback record for the URL.
It then calls `create_notification` to create the Notification Record. 
It then calls `send_notification` to send notifications to the callback URL.

2. create_notification(callback_id, review_id, notification_id):

This creates the Notification record with the above parameters and sets all the fields except `last_ack`.

3. send_notification(Notification, callback_url):

This sends the Notification record as a payload as a POST request to the callback_url. It also handles retries with timeouts.

##### Error classes

A separate error class is implemented with the following:
TimeoutError - When the timeout value has reached. 
RetriesExceededError - When the number of retries has exceeded.

#### Unit tests for callback and webhook

Webhook

1. register_callback on success
2. register_callback on error
3. set_callback_url on success
4. set_callback_url on error
5. notify_callback_on_review_completed on success
6. notify_callback_on_review_completed on error
7. send_notification retry
8. send_notification timeout

Callback

1. notify_client_on_review_completed duplicated
2. notify_client_on_review_completed success

#### Documentation for callback and webhook

Document the new webhook changes, with an example of how client can do a callback in `API.md`.

### Risks & unknowns

Asynchronous implementations are more unpredictable to test and debug issues for. In addition there are other issues:

1. Recreate a long running review test case reliably.
2. No payload signing - not in scope.
3. No caching layer yet - not in scope.
4. Retry storms under partial outages - not in scope.
5. Testing async fire-and-forget reliably — awaited without blocking `process_review`.
6. No manual-send path for when Retries exceed - current implementation has it try again later.

### Edge cases

1. When the webhook doesn't get any acknowledgment from the client and sends a duplicate - same `notification_id` reused on resend.
2. When the webhook fails to create a callback URL — failure response, no Callback row persisted.
3. When the client gets a duplicated notification - deduplication mechanism provided by webhook but handled by client. An example will be provided. 
4. When send_notification exhausts retries (RetriesExceededError) - Ask to try again later.
5. When a client re-registers a new callback URL for the same user_id/profile_id - not allowed. They can delete a callback if needed.
6. When the same review triggers multiple completion events - Handled by design (no re-invocation path today).
7. When a user has multiple profiles with reviews completing concurrently. Handled — key includes profile_id, not just user_id.



