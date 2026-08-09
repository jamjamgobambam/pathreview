import { describe, it, expect } from 'vitest'
import { compareReviews, diffLines } from '../diffFormatter'
import type { Review } from '../../types'

function makeReview(overrides: Partial<Review> = {}): Review {
  return {
    id: 'review-1',
    profile_id: 'profile-1',
    status: 'complete',
    overall_score: 0.75,
    sections: [
      {
        section_name: 'Code Quality',
        content: 'Line one.\nLine two.',
        suggestions: ['Add tests.'],
        confidence: 0.8
      }
    ],
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides
  }
}

describe('diffLines', () => {
  it('marks identical strings as all unchanged', () => {
    expect(diffLines('a\nb\nc', 'a\nb\nc')).toEqual([
      { type: 'unchanged', text: 'a' },
      { type: 'unchanged', text: 'b' },
      { type: 'unchanged', text: 'c' }
    ])
  })

  it('marks an appended line as added, keeping the prefix unchanged', () => {
    expect(diffLines('a\nb', 'a\nb\nc')).toEqual([
      { type: 'unchanged', text: 'a' },
      { type: 'unchanged', text: 'b' },
      { type: 'added', text: 'c' }
    ])
  })

  it('handles empty strings without throwing', () => {
    expect(diffLines('', '')).toEqual([{ type: 'unchanged', text: '' }])
  })
})

describe('compareReviews', () => {
  it('reports no diff for identical reviews', () => {
    const older = makeReview()
    const newer = makeReview()
    const result = compareReviews(older, newer)

    expect(result.hasAnyDiff).toBe(false)
    expect(result.sections.every((s) => s.isIdentical)).toBe(true)
  })

  it('computes overallScoreDelta when only the score changed', () => {
    const older = makeReview({ overall_score: 0.75 })
    const newer = makeReview({ overall_score: 0.85 })
    const result = compareReviews(older, newer)

    expect(result.hasAnyDiff).toBe(true)
    expect(result.overallScoreDelta).toBeCloseTo(0.1)
    expect(result.sections.every((s) => s.isIdentical)).toBe(true)
  })

  it('marks a section only present in the newer review as fully added', () => {
    const older = makeReview({ sections: [] })
    const newer = makeReview()
    const result = compareReviews(older, newer)

    const section = result.sections[0]
    expect(section.presentInA).toBe(false)
    expect(section.presentInB).toBe(true)
    expect(section.contentDiff.every((d) => d.type === 'added')).toBe(true)
    expect(section.suggestionsDiff.every((d) => d.type === 'added')).toBe(true)
    expect(section.isIdentical).toBe(false)
  })

  it('marks a section only present in the older review as fully removed', () => {
    const older = makeReview()
    const newer = makeReview({ sections: [] })
    const result = compareReviews(older, newer)

    const section = result.sections[0]
    expect(section.presentInA).toBe(true)
    expect(section.presentInB).toBe(false)
    expect(section.contentDiff.every((d) => d.type === 'removed')).toBe(true)
    expect(section.suggestionsDiff.every((d) => d.type === 'removed')).toBe(true)
    expect(section.isIdentical).toBe(false)
  })

  it('diffs confidence and content when a shared section changes', () => {
    const older = makeReview()
    const newer = makeReview({
      sections: [
        {
          section_name: 'Code Quality',
          content: 'Line one.\nLine three.',
          suggestions: ['Add tests.'],
          confidence: 0.9
        }
      ]
    })
    const result = compareReviews(older, newer)

    const section = result.sections[0]
    expect(section.confidenceDelta).toBeCloseTo(0.1)
    expect(section.contentDiff).toEqual([
      { type: 'unchanged', text: 'Line one.' },
      { type: 'removed', text: 'Line two.' },
      { type: 'added', text: 'Line three.' }
    ])
    expect(section.isIdentical).toBe(false)
  })

  it('leaves overallScoreDelta undefined when a score is missing, without throwing', () => {
    const older = makeReview({ overall_score: undefined })
    const newer = makeReview({ overall_score: 0.8 })

    expect(() => compareReviews(older, newer)).not.toThrow()
    expect(compareReviews(older, newer).overallScoreDelta).toBeUndefined()

    const bothMissing = compareReviews(
      makeReview({ overall_score: undefined }),
      makeReview({ overall_score: undefined })
    )
    expect(bothMissing.overallScoreDelta).toBeUndefined()
  })
})
