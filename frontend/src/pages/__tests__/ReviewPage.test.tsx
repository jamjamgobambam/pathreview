import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ReviewPage } from '../ReviewPage'

vi.mock('react-router-dom', () => ({
  useParams: vi.fn(() => ({ reviewId: 'test-review-123' })),
  useNavigate: vi.fn(() => vi.fn()),
}))

vi.mock('../../hooks/useReviewStatus', () => ({
  useReviewStatus: vi.fn(() => ({
    review: null,
    isPolling: false,
    error: null,
    progress: 0,
  })),
}))

vi.mock('../../services/api', () => ({
  apiClient: {
    getReview: vi.fn(),
  },
}))

describe('ReviewPage — progress indicator', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows a progress bar while polling', async () => {
    const { useReviewStatus } = await import('../../hooks/useReviewStatus')
    vi.mocked(useReviewStatus).mockReturnValueOnce({
      review: null,
      isPolling: true,
      error: null,
      progress: 45,
    })

    render(<ReviewPage />)

    const bar = document.querySelector('[style*="width: 45%"]')
    expect(bar).toBeInTheDocument()
  })

  it('shows the correct percentage label while polling', async () => {
    const { useReviewStatus } = await import('../../hooks/useReviewStatus')
    vi.mocked(useReviewStatus).mockReturnValueOnce({
      review: null,
      isPolling: true,
      error: null,
      progress: 45,
    })

    render(<ReviewPage />)

    expect(screen.getByText('45%')).toBeInTheDocument()
  })

  it('does not show a progress bar when not polling', async () => {
    const { useReviewStatus } = await import('../../hooks/useReviewStatus')
    vi.mocked(useReviewStatus).mockReturnValueOnce({
      review: null,
      isPolling: false,
      error: null,
      progress: 0,
    })

    render(<ReviewPage />)

    const bar = document.querySelector('[style*="width: 0%"]')
    expect(bar).not.toBeInTheDocument()
  })

  it('progress bar width reflects progress value', async () => {
    const { useReviewStatus } = await import('../../hooks/useReviewStatus')
    vi.mocked(useReviewStatus).mockReturnValueOnce({
      review: null,
      isPolling: true,
      error: null,
      progress: 75,
    })

    render(<ReviewPage />)

    const bar = document.querySelector('[style*="width: 75%"]')
    expect(bar).toBeInTheDocument()
  })
})
