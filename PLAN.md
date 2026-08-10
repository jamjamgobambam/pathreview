## Solution plan

**Issue:** Add a safety event count to the health check endpoint
 #68, https://github.com/ascherj/pathreview/issues/68

### Understand
The issue states the `/health` endpoint reports service status but not safety-system
activity, forcing operators to check a separate monitoring dashboard to see if the
safety system has flagged anything recently. Expected behavior: `/health` should
include a `safety_events_last_hour` field showing a live count of safety events
from the last hour.

**Note from reproduction:** the field is already present in the current response
(`"safety_events_last_hour":0`), which doesn't match the issue's premise. Before
writing any fix, I need to determine which of these is actually true:
- (a) the field is fully implemented and querying real data... meaning the "0" I saw
  is legitimate (no safety events happened in the last hour), and there's no bug, or
- (b) the field exists but is a hardcoded/stubbed placeholder that always returns 0
  regardless of actual safety activity, meaning the real work is wiring it up
  properly, not adding it from scratch.

### Map
- `api/routes/health.py` — where the `/health` response dict is built; need to see
  exactly how `safety_events_last_hour` is currently populated (literal value vs.
  function call).
- `safety/monitoring.py` — where safety events are presumably logged/stored; need to
  check whether a function exists here that can return an accurate "count of events
  in the last hour," and if so, whether `health.py` actually calls it.

### Plan
1. Read `api/routes/health.py` to see exactly how `safety_events_last_hour` is
   currently populated (hardcoded vs. computed).
2. Read `safety/monitoring.py` to see what safety event data is actually stored and
   whether a real "count events since timestamp" query is possible/exists.
3. If the field is a stub: implement a real query function in `safety/monitoring.py`
   (e.g. `get_event_count(since=one_hour_ago)`), and update `health.py` to call it.
4. If the field is already correctly wired: instead confirm this with a manual test
   (trigger a real safety event, then re-check `/health` count increases), and treat
   this issue as effectively already resolved — document that finding instead of
   writing new code.
5. Add/update a test asserting `safety_events_last_hour` reflects actual event
   counts (not just field presence), to prevent future regression to a stub value.

### Inputs & outputs
- **Input:** a GET request to `/health`; implicitly, the current time and the set
  of safety events logged in `safety/monitoring.py` within the last hour.
- **Output:** the existing `/health` JSON response, with `safety_events_last_hour`
  accurately reflecting the real count of safety events in the trailing 60 minutes
  (not a static/stubbed value).

### Risks & unknowns
- Unsure yet whether `safety/monitoring.py` even has a data store capable of
  answering "how many events in the last hour" efficiently — may need to add
  indexing or a time-bounded query if events are just appended to a list/log.
- The 503 status (Postgres/Redis unhealthy) may block me from getting a clean
  "healthy" test locally — need to confirm this is a local env issue and not
  something that changes how `/health` should behave when dependencies are down
  (e.g., should safety_events_last_hour still populate correctly even if postgres/
  redis are down, or does the current code short-circuit before reaching that logic?).
- Possible mismatch between "issue as filed" and "issue as it exists in code today" —
  need to loop in whoever filed it if my findings contradict the description.

### Edge cases
- No safety events in the last hour → should return `0`, not `null` or an error.
- Safety event store/monitoring backend itself unavailable → `/health` should
  probably still respond (perhaps with `safety_events_last_hour: null` or omitted,
  plus a flag), rather than crashing the whole health check.
- Postgres/Redis unhealthy (as seen in repro) → confirm safety event count logic is
  independent of those dependencies and still returns a real number in that case.
- Very high event volume → confirm the query performs reasonably and doesn't scan
  an unbounded log on every health check call.