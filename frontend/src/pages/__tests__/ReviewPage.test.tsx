import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import React from 'react'
import { ReviewPage } from '../ReviewPage'

// Mock react-router-dom
vi.mock('react-router-dom', () => ({
  useParams: () => ({ reviewId: 'test-review-id' }),
  useNavigate: () => vi.fn()
}))

// Mock useReviewStatus hook
const mockUseReviewStatus = vi.fn()
vi.mock('../../hooks/useReviewStatus', () => ({
  useReviewStatus: (id: string) => mockUseReviewStatus(id)
}))

// Mock apiClient
vi.mock('../../services/api', () => ({
  apiClient: {
    getReview: vi.fn()
  }
}))

describe('ReviewPage progress bar', () => {
  it('renders progress bar with correct percentage when polling', () => {
    mockUseReviewStatus.mockReturnValue({
      review: {
        id: 'test-review-id',
        status: 'processing',
        progress_pct: 45
      },
      isPolling: true,
      error: null
    })

    render(<ReviewPage />)

    // Check loading text and percentage
    expect(screen.getByText('Analyzing your portfolio...')).toBeInTheDocument()
    expect(screen.getByText('45%')).toBeInTheDocument()

    // Check progressbar role and accessibility values
    const progressbar = screen.getByRole('progressbar')
    expect(progressbar).toBeInTheDocument()
    expect(progressbar).toHaveAttribute('aria-valuenow', '45')
    expect(progressbar).toHaveAttribute('aria-valuemin', '0')
    expect(progressbar).toHaveAttribute('aria-valuemax', '100')
  })

  it('defaults to 0% progress when progress_pct is undefined', () => {
    mockUseReviewStatus.mockReturnValue({
      review: {
        id: 'test-review-id',
        status: 'pending'
      },
      isPolling: true,
      error: null
    })

    render(<ReviewPage />)

    expect(screen.getByText('0%')).toBeInTheDocument()
    const progressbar = screen.getByRole('progressbar')
    expect(progressbar).toHaveAttribute('aria-valuenow', '0')
  })
})
