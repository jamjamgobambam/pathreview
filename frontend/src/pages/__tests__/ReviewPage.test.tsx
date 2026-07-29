import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ReviewPage } from '../ReviewPage'
import { useReviewStatus } from '../../hooks/useReviewStatus'

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
})
