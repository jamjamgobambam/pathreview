import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
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

vi.mock('../../services/shareService', () => ({
  createShareLink: vi.fn(async () => ({
    share_token: 'test-token',
    share_url: 'http://localhost/shared/test-token',
    expires_at: '2024-02-01T00:00:00Z',
  })),
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

  it('renders a "Copy link" button on a completed review', async () => {
    renderReviewPage()
    expect(await screen.findByRole('button', { name: /copy link/i })).toBeInTheDocument()
  })

  it('copies the share URL to clipboard when "Copy link" is clicked', async () => {
    renderReviewPage()
    const btn = await screen.findByRole('button', { name: /copy link/i })
    btn.click()
    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('http://localhost/shared/test-token')
    })
  })

  it('shows "Copied!" feedback after clicking "Copy link"', async () => {
    renderReviewPage()
    const btn = await screen.findByRole('button', { name: /copy link/i })
    await userEvent.click(btn)
    expect(await screen.findByRole('button', { name: /copied!/i })).toBeInTheDocument()
  })
})
