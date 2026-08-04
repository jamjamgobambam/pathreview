# Solution plan

**Issue:** Review history page displays dates in UTC instead of the user's local timezone — https://github.com/jamjamgobambam/pathreview/issues/93

### Understand

**Expected:** A review's date on the Review History page reflects the calendar
day/time in the *viewer's* local timezone.

**Actual:** The date can be off by up to a day. A review created at 11:00 PM EST
is shown as the next calendar day.

**Root cause (a two-part chain, confirmed by reproduction):**

1. The backend stores/returns `created_at` from `datetime.utcnow()`
   (`core/models/review.py`), which is a **naive** datetime. Pydantic's
   `ReviewResponse` (`api/schemas/review.py`) serializes it to an ISO string
   with **no timezone suffix**, e.g. `"2026-07-12T03:00:00"` — no trailing `Z`.
2. On the frontend, `formatDate` in `frontend/src/utils/dateFormatters.ts` does
   `new Date(isoString)`. Per the ECMAScript spec, a date-time string **without**
   an offset is parsed as **local time**, not UTC. So the UTC instant is
   misinterpreted, shifting the rendered calendar day in any non-UTC timezone.

The primary, self-contained fix is on the frontend: interpret the incoming
timestamp as UTC before formatting. The backend emitting an explicit `Z` is a
complementary correctness improvement (see Risks).

### Map

Files involved:

- `frontend/src/utils/dateFormatters.ts` — **primary fix.** `formatDate` and
  `formatRelativeDate` both call `new Date(isoString)` on an offset-less string.
- `frontend/src/pages/ReviewHistoryPage.tsx` — the consumer (calls
  `formatDate(review.created_at)` at the Date column). Likely no change needed,
  but it's where the bug is user-visible.
- `frontend/src/utils/__tests__/dateFormatters.test.ts` — reproduction tests
  (added in Week 8); will be extended to lock in correct behavior.
- `frontend/src/pages/DashboardPage.tsx` — also uses `formatDate`; benefits from
  the same fix (verify no regression).
- *(Optional / backend)* `core/models/review.py`, `api/schemas/review.py` — make
  the API emit timezone-aware UTC (`...Z`). Considered but scoped as secondary.

### Plan

1. **Normalize input to UTC in `dateFormatters.ts`.** Add a small helper that,
   when an ISO string carries no timezone designator (no `Z` and no `±hh:mm`),
   appends `Z` so `new Date(...)` parses it as UTC. Route both `formatDate` and
   `formatRelativeDate` through it. Then `toLocaleDateString` renders in the
   browser's local zone as intended.
2. **Extend tests.** Keep the reproduction assertions and add cases for:
   already-`Z` strings, strings with an explicit `±hh:mm` offset (must not be
   double-adjusted), and `formatRelativeDate`. Pin `TZ` for determinism.
3. **Verify consumers.** Run the app + suite; confirm Review History and
   Dashboard both show the expected local day, including a late-evening
   boundary case.
4. **Decide on the backend change.** Evaluate switching the model default to
   timezone-aware UTC and/or serializing with a `Z`. If low-risk, include it so
   the API is correct for any client; otherwise document as a follow-up.
5. **Changelog / issue note.** Summarize the fix and link the failing→passing
   tests in the PR.

### Inputs & outputs

- **Input:** an ISO-8601 timestamp string as returned by the API
  (currently offset-less UTC, e.g. `"2026-07-12T03:00:00"`; possibly `Z`- or
  offset-suffixed after the backend change).
- **Output:** a human-readable date string (`formatDate`) / relative phrase
  (`formatRelativeDate`) that reflects the **viewer's local timezone**,
  identical whether the same instant arrives naive, `Z`-suffixed, or with an
  explicit offset.

### Risks & unknowns

- **Double-adjustment:** naively appending `Z` to a string that *already* has an
  offset would corrupt it. The helper must only append when no designator is
  present.
- **Backend coupling:** if the backend is later changed to emit `Z`, the
  frontend must still be correct (the "no designator → append Z" guard makes it
  idempotent, so both are safe).
- **Test flakiness by machine TZ:** assertions must pin `TZ`; a bare
  `new Date()` in tests would vary by runner.
- **Other timestamp consumers:** need to confirm every place that formats a date
  goes through these helpers (grep for `new Date(`), so nothing is missed.
- **Malformed/empty input:** current code returns `Invalid Date`; decide whether
  to guard.

### Edge cases

- Offset-less UTC string (the bug case) — must render local day correctly.
- String already ending in `Z` — must be unchanged in meaning.
- String with explicit `±hh:mm` offset — must not be re-adjusted.
- Late-evening / early-morning times that cross the UTC↔local date boundary.
- Viewer exactly in UTC (offset 0) — must still be correct.
- Empty string / `null` / invalid input — should degrade gracefully, not throw.
