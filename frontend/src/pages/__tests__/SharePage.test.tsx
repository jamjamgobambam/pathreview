import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { SharePage } from '../SharePage'

vi.mock('../../services/api', () => ({
  apiClient: {
    getSharedReview: vi.fn()
  }
}))

import { apiClient } from '../../services/api'

const renderSharePage = (token = 'abc') =>
  render(
    <MemoryRouter initialEntries={[`/share/${token}`]}>
      <Routes>
        <Route path="/share/:token" element={<SharePage />} />
      </Routes>
    </MemoryRouter>
  )

describe('SharePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the shared review summary on success', async () => {
    vi.mocked(apiClient.getSharedReview).mockResolvedValue({
      overall_score: 0.81,
      sections: [
        {
          section_name: 'Technical Skills',
          content: 'Strong backend fundamentals.',
          suggestions: ['Add type hints'],
          confidence: 0.9
        }
      ],
      created_at: '2026-07-01T00:00:00Z',
      expires_at: '2026-08-01T00:00:00Z'
    })

    renderSharePage()

    await waitFor(() => {
      expect(screen.getByText('Portfolio Review')).toBeInTheDocument()
    })
    expect(screen.getByText('Technical Skills')).toBeInTheDocument()
    expect(screen.getByText('81/100')).toBeInTheDocument()
  })

  it('shows an error message when the link is expired or invalid', async () => {
    vi.mocked(apiClient.getSharedReview).mockRejectedValue(
      new Error('Share link not found or expired')
    )

    renderSharePage('expired-token')

    await waitFor(() => {
      expect(screen.getByText(/no longer available/i)).toBeInTheDocument()
    })
  })

  it('requests the shared review using the token from the URL', async () => {
    vi.mocked(apiClient.getSharedReview).mockResolvedValue({
      overall_score: 0.5,
      sections: [],
      created_at: '2026-07-01T00:00:00Z',
      expires_at: '2026-08-01T00:00:00Z'
    })

    renderSharePage('my-token-123')

    await waitFor(() => {
      expect(apiClient.getSharedReview).toHaveBeenCalledWith('my-token-123')
    })
  })
})
