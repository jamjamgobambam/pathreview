## Solution plan


**Issue:** [Add a safety event count to the health check endpoint #68 https://github.com/ascherj/pathreview/issues/68]

### Understand
The `/health` API endpoint currently returns service status and does not surface safety metrics. The expected behavior  for the endpoint is to include a `safety_events_last_hour` field, so that operators can monitor safety system activity without having to additionally query the monitoring dashboard directly for the metrics.

### Map
*   `api/routes/health.py`
*   `safety/monitoring.py`

### Plan
1.  Inspect `safety/monitoring.py` to identify / implement a function that retrieves the count of safety events from the last hour.
2.  Update `api/routes/health.py` to import the created monitoring function.
3.  Modify the JSON response in `api/routes/health.py` to execute the function and assign its return value to the `safety_events_last_hour` key.
4.  Finally update the relevant unit tests in the `tests/` directory to verify the health endpoint properly returns the new field.

### Inputs & outputs
*   **Input**: A GET request to the `/health` endpoint. (standard)
*   **Output**: A JSON response containing the standard health status alongside `"safety_events_last_hour": <integer>`.

### Risks & unknowns
*   Performance degradation is possible if the safety event query in `safety/monitoring.py` is unreasonably computationally heavy or database-intensive on a high-frequency occuring health check endpoint.
*   Uncertainty on whether `safety/monitoring.py` currently tracks event timestamps well enough to filter by the last hour.

### Edge cases
*   If the safety monitoring system is temporarily unreachable or fails to calculate the count, the `/health` endpoint must handle the exception (e.g., returning `null` or `0` for the field) as opposed to failing the entire health check.