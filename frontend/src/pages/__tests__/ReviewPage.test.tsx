import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ReviewPage } from '../ReviewPage'
import { Review } from '../../types'

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useParams: () => ({ reviewId: 'review-123' }),
    useNavigate: () => vi.fn()
  }
})

vi.mock('../../hooks/useReviewStatus', () => ({
  useReviewStatus: vi.fn()
}))

describe('ReviewPage progress indicator (issue #97)', () => {
  const baseReview: Review = {
    id: 'review-123',
    profile_id: 'profile-123',
    status: 'processing',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z'
  }

  it('shows a queued label and 0% for a pending review', async () => {
    const { useReviewStatus } = await import('../../hooks/useReviewStatus')
    vi.mocked(useReviewStatus).mockReturnValue({
      review: { ...baseReview, status: 'pending', progress_pct: 0 },
      isPolling: true,
      error: null
    })

    render(<ReviewPage />)

    expect(screen.getByText('Queued for review...')).toBeInTheDocument()
    expect(screen.getByText('0%')).toBeInTheDocument()
  })

  it('shows an advancing percentage while processing', async () => {
    const { useReviewStatus } = await import('../../hooks/useReviewStatus')
    vi.mocked(useReviewStatus).mockReturnValue({
      review: { ...baseReview, status: 'processing', progress_pct: 50 },
      isPolling: true,
      error: null
    })

    render(<ReviewPage />)

    expect(screen.getByText('Analyzing your portfolio...')).toBeInTheDocument()
    expect(screen.getByText('50%')).toBeInTheDocument()
  })

  it('renders the progress bar width proportional to progress_pct', async () => {
    const { useReviewStatus } = await import('../../hooks/useReviewStatus')
    vi.mocked(useReviewStatus).mockReturnValue({
      review: { ...baseReview, status: 'processing', progress_pct: 75 },
      isPolling: true,
      error: null
    })

    const { container } = render(<ReviewPage />)

    const bar = container.querySelector('.bg-blue-600.transition-all') as HTMLElement
    expect(bar).toHaveStyle({ width: '75%' })
  })

  it('does not show the polling card once the review fails', async () => {
    const { useReviewStatus } = await import('../../hooks/useReviewStatus')
    vi.mocked(useReviewStatus).mockReturnValue({
      review: { ...baseReview, status: 'failed', progress_pct: 50, error_message: 'boom' },
      isPolling: false,
      error: null
    })

    render(<ReviewPage />)

    expect(screen.queryByText('Analyzing your portfolio...')).not.toBeInTheDocument()
    expect(screen.getByText('Review Failed')).toBeInTheDocument()
  })
})
