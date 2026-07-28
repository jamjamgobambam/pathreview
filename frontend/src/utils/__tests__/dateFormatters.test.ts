import { describe, it, expect } from 'vitest'
import { formatDate, formatRelativeDate } from '../dateFormatters'

/**
 * Tests for issue #93 — Review history displayed dates in UTC instead of the
 * user's local timezone.
 * https://github.com/jamjamgobambam/pathreview/issues/93
 *
 * Root cause (two parts):
 *   1. The backend serializes `created_at` from `datetime.utcnow()`, which is a
 *      NAIVE datetime, so the JSON has no timezone suffix, e.g.
 *      "2026-07-12T03:00:00" (note: no trailing "Z").
 *   2. `new Date("2026-07-12T03:00:00")` parses an offset-less string as LOCAL
 *      time, not UTC. So a review created at 11:00 PM EST (= 03:00 UTC the next
 *      day) was rendered on the wrong calendar day.
 *
 * The fix parses timezone-less strings as UTC (see `parseIsoAsUtc`) before
 * formatting in the viewer's local zone. These tests lock in that behavior.
 *
 * The assertions are written to be timezone-agnostic: they check the invariant
 * that a naive string is treated as UTC (i.e. identical to the same string with
 * an explicit "Z"), which holds in every timezone. The V8 engine reads the TZ
 * env var only at process start, so a per-suite `process.env.TZ` override is
 * unreliable — we deliberately avoid depending on the runner's zone.
 */

// The exact naive-UTC shape the API returns (from datetime.utcnow(), no "Z").
const NAIVE = '2026-07-12T03:00:00'
const EXPLICIT_UTC = '2026-07-12T03:00:00Z'

// The local calendar day the fix should produce, derived from the SAME zone the
// code runs in — so this expectation is correct on any machine.
const expectedLocalDay = new Date(EXPLICIT_UTC).toLocaleDateString('en-US', {
  year: 'numeric',
  month: 'short',
  day: 'numeric'
})

describe('formatDate — issue #93 timezone handling', () => {
  it('parses a naive-UTC timestamp as UTC (not local) and formats in local zone', () => {
    // The bug rendered the naive string as local time, shifting the day.
    // After the fix it must match the explicit-UTC instant's local day.
    expect(formatDate(NAIVE)).toBe(expectedLocalDay)
  })

  it('treats the naive form identically to the explicit-"Z" form', () => {
    expect(formatDate(NAIVE)).toBe(formatDate(EXPLICIT_UTC))
  })

  it('does not double-adjust a string that already carries a "Z"', () => {
    // Idempotence: a "Z" string must be parsed once, matching a plain UTC parse.
    const viaFormatter = formatDate('2026-03-15T12:00:00Z')
    const viaDirect = new Date('2026-03-15T12:00:00Z').toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
    expect(viaFormatter).toBe(viaDirect)
  })

  it('respects an explicit +hh:mm offset without re-adjusting it', () => {
    // Must reflect the exact instant the offset denotes, not have "Z" appended.
    const withOffset = '2026-07-12T01:00:00+05:30'
    const viaDirect = new Date(withOffset).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
    expect(formatDate(withOffset)).toBe(viaDirect)
  })
})

describe('formatRelativeDate — issue #93 timezone handling', () => {
  it('parses a naive-UTC timestamp as UTC, landing in the right bucket', () => {
    // A UTC instant 2 hours before now. If misparsed as local, the age would be
    // off by the local offset and could fall in a different bucket.
    const twoHoursAgoUtc = new Date(Date.now() - 2 * 3600 * 1000)
    const naive = twoHoursAgoUtc.toISOString().replace(/\.\d+Z$/, '')
    expect(formatRelativeDate(naive)).toBe('2 hours ago')
  })

  it('gives the same result for naive and "Z"-suffixed forms', () => {
    const threeDaysAgoUtc = new Date(Date.now() - 3 * 86400 * 1000)
    const withZ = threeDaysAgoUtc.toISOString()
    const naive = withZ.replace(/\.\d+Z$/, '')
    expect(formatRelativeDate(naive)).toBe(formatRelativeDate(withZ))
  })
})
