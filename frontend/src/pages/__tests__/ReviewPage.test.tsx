import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { axe } from 'jest-axe'
import { ReviewPage } from '../ReviewPage'
import { useReviewStatus } from '../../hooks/useReviewStatus'
import { Review } from '../../types'

const failedReview: Review = {
  id: 'review-123',
  profile_id: 'profile-123',
  status: 'failed',
  error_message: 'The analysis service timed out.',
  created_at: '2026-07-01T00:00:00Z',
  updated_at: '2026-07-01T00:05:00Z'
}

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useParams: () => ({ reviewId: 'review-123' }),
    useNavigate: () => vi.fn()
  }
})

vi.mock('../../hooks/useReviewStatus')

vi.mock('../../services/api', () => ({
  apiClient: {
    getReview: vi.fn()
  }
}))

const mockUseReviewStatus = vi.mocked(useReviewStatus)

describe('ReviewPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the polling state', () => {
    mockUseReviewStatus.mockReturnValue({ review: null, isPolling: true, error: null })

    render(<ReviewPage />)

    expect(screen.getByText('Analyzing your portfolio...')).toBeInTheDocument()
  })

  it('has no accessibility violations in the polling state', async () => {
    mockUseReviewStatus.mockReturnValue({ review: null, isPolling: true, error: null })

    const { container } = render(<ReviewPage />)

    expect(await axe(container)).toHaveNoViolations()
  })

  it('has no accessibility violations in the failed state', async () => {
    mockUseReviewStatus.mockReturnValue({ review: failedReview, isPolling: false, error: null })

    const { container } = render(<ReviewPage />)

    expect(screen.getByText('Review Failed')).toBeInTheDocument()
    expect(await axe(container)).toHaveNoViolations()
  })
})
