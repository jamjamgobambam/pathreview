import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { formatDate } from '../dateFormatters'

/**
 * Reproduction for issue #93 — Review history displays dates in UTC instead of
 * the user's local timezone.
 * https://github.com/jamjamgobambam/pathreview/issues/93
 *
 * Root cause (two parts):
 *   1. The backend serializes `created_at` from `datetime.utcnow()`, which is a
 *      NAIVE datetime, so the JSON has no timezone suffix, e.g.
 *      "2026-07-12T04:00:00" (note: no trailing "Z").
 *   2. `new Date("2026-07-12T04:00:00")` parses an offset-less string as LOCAL
 *      time, not UTC. So a review created at 11:00 PM EST (= 04:00 UTC the next
 *      day) is rendered on the wrong calendar day.
 *
 * These tests assert the EXPECTED (correct) behavior, so they currently FAIL —
 * that failure IS the reproduction. The Week 9 fix will make them pass.
 *
 * Note: this file forces a fixed non-UTC timezone so the assertions are
 * deterministic regardless of the machine running the suite.
 */

const ORIGINAL_TZ = process.env.TZ

beforeAll(() => {
  // America/New_York is UTC-5 (EST) / UTC-4 (EDT); a late-evening local time
  // crosses the UTC date boundary, which is where the bug shows up.
  process.env.TZ = 'America/New_York'
})

afterAll(() => {
  process.env.TZ = ORIGINAL_TZ
})

describe('formatDate — issue #93 timezone reproduction', () => {
  it('renders a naive-UTC timestamp on the correct LOCAL calendar day', () => {
    // Review created 2026-07-11 23:00 America/New_York == 2026-07-12 03:00 UTC.
    // The API returns the UTC instant WITHOUT an offset suffix:
    const apiCreatedAt = '2026-07-12T03:00:00'

    // Expected: the user in New_York created it on Jul 11, so it must show Jul 11.
    // Actual (bug): naive string parsed as local -> shows Jul 12.
    expect(formatDate(apiCreatedAt)).toBe('Jul 11, 2026')
  })

  it('treats an explicit-UTC ("Z") timestamp the same as the naive one', () => {
    // Once fixed, the naive form must be interpreted as UTC — identical to the
    // "Z"-suffixed form — and rendered in local time.
    const naive = '2026-07-12T03:00:00'
    const explicitUtc = '2026-07-12T03:00:00Z'

    expect(formatDate(naive)).toBe(formatDate(explicitUtc))
  })
})
