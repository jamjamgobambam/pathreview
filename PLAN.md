## Solution plan

**Issue:**
- Issue Title: "Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x"
- Issue Link: https://github.com/ascherj/pathreview/issues/154

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

The root cause of this issue is in `api/routes/health.py` on line 31. The current line is `await db.execute("SELECT 1")`, which causes an error since the `execute` method does not accept a raw string as a query. As mentioned in the issue description, SQLAlchemy 2.x requires a text SQL query to be wrapped with the `sqlalchemy.text()` method. 

Actual behavior: Since the current code does not use the wrapper method, an error is raised, which is caught in the try/except block. In the except branch, the health status of Postgres is then updated to "unhealthy", which happens in line 36 (`health_status["dependencies"]["postgres"] = "unhealthy"`). This results in the response from the /health endpoint falsely reporting that the Postgres service is down.

The expected behavior is for the /health endpoint to correctly report the status of the Postgres service. For that to occur, false exceptions should not occur, so the `sqlalchemy.text()` wrapper method should be implemented.


### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

The files and functions involved are:
- `api/routes/health.py`: the function `health_check` needs to be modified to implement the `sqlalchemy.text()` wrapper method.
- `tests/unit` directory: a new file will have to be added to include unit tests for the GET health endpoint, since no existing unit tests are related to this API endpoint

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. Read documentation on `sqlalchemy.text()` and `sqlalchemy.execute()` to ensure that the usage matches up with the SQLAlchemy version currently used in the codebase.
2. Implement the fix in `api/routes/health.py`, wrapping the SQL query text with the `sqlalchemy.text()` method on line 31.
3. Write unit test(s) to check that the status of Postgres is correctly reported, using `Mock()` and `AsyncMock()` objects to imitate a failed and successful DB query. If such tests pass, then the fix works for both the happy path (DB is up, endpoint reports service as healthy) and the failure path (DB is actually down, endpoint reports service as unhealthy). The resulting status/error codes can be checked within these unit tests.
4. Run the application and use `curl` commands and/or the Postman client to make a real request to the GET health endpoint, and ensure that the reported service status for Postgres is correct.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

**Function to Change:** `async def health_check(db=Depends(get_db))`
- Takes no no inputs
- Returns a dictionary containing the status of services (where the key is ["dependencies][< service name >])  along with other metadata

**Changed/Correct Behavior:**
- Correctly report the up status of the Postgres DB service, and to avoid the error `ArgumentError: Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')` from appearing in the terminal output.

### Risks & unknowns
What could go wrong? What are you still unsure about?

I am still unsure whether the fix requires just the implementation of the `sqlalchemy.text()` method, or whether other changes need to be made that might occur as side effects. Through reading documentation and understanding the current flow of paths in the function will help mitigate unwanted cascading issues.

### Edge cases
What inputs or states should your fix handle gracefully?

The fix should handle:
- A true positive: The Postgres service is up, so the GET health endpoint should correctly report the Postgres status as "healthy"
- A true negative: The Postgres service is down, so the GET health endpoint should correctly report the Postgres status

Currently, without the fix, false negatives are the problem (the service is truly up, but the endpoint falsely reports the Postgres status as "unhealthy").

After the proposed fix, no false positives or false negatives should occur. This will be verified with a mix of AP requests and unit testing.

