import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { ReviewPage } from '../ReviewPage'
import { Review } from '../../types'

const mockReview: Review = {
  id: 'review-123',
  profile_id: 'profile-456',
  status: 'complete',
  overall_score: 0.82,
  sections: [
    {
      section_name: 'Code Quality',
      content: 'Well structured code.',
      suggestions: ['Add more tests'],
      confidence: 0.9,
    },
  ],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

vi.mock('../../hooks/useReviewStatus', () => ({
  useReviewStatus: vi.fn(() => ({
    review: mockReview,
    isPolling: false,
    error: null,
  })),
}))

vi.mock('../../services/api', () => ({
  apiClient: {
    getReview: vi.fn(async () => mockReview),
  },
}))

const renderReviewPage = () =>
  render(
    <MemoryRouter initialEntries={['/reviews/review-123']}>
      <Routes>
        <Route path="/reviews/:reviewId" element={<ReviewPage />} />
      </Routes>
    </MemoryRouter>
  )

describe('ReviewPage — Copy link button (issue #101)', () => {
  beforeEach(() => {
    Object.assign(navigator, {
      clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
    })
  })

  // REPRODUCTION: This test fails because the "Copy link" button does not exist.
  // The current Share button uses alert() and has no dedicated "Copy link" label
  // or inline confirmation. Fix: replace/augment with a proper Copy link button.
  it('renders a "Copy link" button on a completed review', async () => {
    renderReviewPage()
    expect(await screen.findByRole('button', { name: /copy link/i })).toBeInTheDocument()
  })

  it('copies the current URL to clipboard when "Copy link" is clicked', async () => {
    renderReviewPage()
    const btn = await screen.findByRole('button', { name: /copy link/i })
    btn.click()
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(window.location.href)
  })
})
