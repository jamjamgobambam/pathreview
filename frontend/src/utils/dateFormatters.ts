/**
 * Parse an ISO-8601 timestamp into a Date, interpreting timezone-less strings
 * as UTC.
 *
 * The API serializes timestamps from Python's `datetime.utcnow()`, which is a
 * naive datetime and produces an ISO string with no timezone designator, e.g.
 * "2026-07-12T03:00:00". `new Date()` parses such offset-less strings as *local*
 * time, which shifts the displayed day for any user not in UTC (issue #93).
 *
 * If the string already carries a designator (a trailing "Z" or a "+hh:mm" /
 * "-hh:mm" offset), it is left untouched, so this is safe to apply to any ISO
 * value and is idempotent.
 */
function parseIsoAsUtc(isoString: string): Date {
  const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/.test(isoString)
  return new Date(hasTimezone ? isoString : `${isoString}Z`)
}

export function formatDate(isoString: string): string {
  const date = parseIsoAsUtc(isoString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

export function formatRelativeDate(isoString: string): string {
  const date = parseIsoAsUtc(isoString)
  const now = new Date()
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)

  if (seconds < 60) return 'just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`
  if (seconds < 604800) return `${Math.floor(seconds / 86400)} days ago`
  if (seconds < 2592000) return `${Math.floor(seconds / 604800)} weeks ago`
  if (seconds < 31536000) return `${Math.floor(seconds / 2592000)} months ago`
  return `${Math.floor(seconds / 31536000)} years ago`
}
