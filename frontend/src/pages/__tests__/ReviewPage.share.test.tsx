import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { ReviewPage } from '../ReviewPage'

const completeReview = {
  id: 'rev-1',
  profile_id: 'prof-1',
  status: 'complete' as const,
  overall_score: 0.81,
  sections: [
    {
      section_name: 'Technical Skills',
      content: 'Strong fundamentals.',
      suggestions: ['Add tests'],
      confidence: 0.9
    }
  ],
  created_at: '2026-07-01T00:00:00Z',
  updated_at: '2026-07-01T00:00:00Z'
}

vi.mock('../../hooks/useReviewStatus', () => ({
  useReviewStatus: vi.fn(() => ({
    review: completeReview,
    isPolling: false,
    error: ''
  }))
}))

vi.mock('../../services/api', () => ({
  apiClient: {
    getReview: vi.fn(),
    createShareLink: vi.fn()
  }
}))

import { apiClient } from '../../services/api'

const renderReviewPage = () =>
  render(
    <MemoryRouter initialEntries={['/reviews/rev-1']}>
      <Routes>
        <Route path="/reviews/:reviewId" element={<ReviewPage />} />
      </Routes>
    </MemoryRouter>
  )

describe('ReviewPage share button', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(apiClient.getReview).mockResolvedValue(completeReview)
    Object.assign(navigator, {
      clipboard: { writeText: vi.fn().mockResolvedValue(undefined) }
    })
  })

  it('requests a public share link and copies it, then confirms', async () => {
    vi.mocked(apiClient.createShareLink).mockResolvedValue({
      token: 'tok-abc',
      expires_at: '2026-08-01T00:00:00Z'
    })

    renderReviewPage()

    const shareButton = await screen.findByRole('button', { name: /share/i })
    fireEvent.click(shareButton)

    await waitFor(() => {
      expect(apiClient.createShareLink).toHaveBeenCalledWith('rev-1')
    })

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      `${window.location.origin}/share/tok-abc`
    )
    await waitFor(() => {
      expect(screen.getByText(/link copied/i)).toBeInTheDocument()
    })
  })

  it('shows an error message if creating the share link fails', async () => {
    vi.mocked(apiClient.createShareLink).mockRejectedValue(
      new Error('Failed to create share link')
    )

    renderReviewPage()

    const shareButton = await screen.findByRole('button', { name: /share/i })
    fireEvent.click(shareButton)

    await waitFor(() => {
      expect(screen.getByText('Failed to create share link')).toBeInTheDocument()
    })
  })
})
