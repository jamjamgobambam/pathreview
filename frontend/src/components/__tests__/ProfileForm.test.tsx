import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ProfileForm } from '../ProfileForm'

vi.mock('../../hooks/useProfileSubmit', () => ({
  useProfileSubmit: vi.fn(() => ({
    submit: vi.fn(async () => ({ id: 'profile-123' })),
    isLoading: false,
    error: null
  }))
}))

describe('ProfileForm', () => {
  const mockOnSuccess = vi.fn()

  beforeEach(() => {
    mockOnSuccess.mockClear()
  })

  it('renders all form fields', () => {
    render(<ProfileForm onSuccess={mockOnSuccess} />)
    expect(screen.getByLabelText(/GitHub Username/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Resume/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Portfolio URL/i)).toBeInTheDocument()
  })

  it('disables submit button while loading', async () => {
    const { useProfileSubmit } = await import('../../hooks/useProfileSubmit')
    vi.mocked(useProfileSubmit).mockReturnValueOnce({
      submit: vi.fn(),
      isLoading: true,
      error: null
    })

    render(<ProfileForm onSuccess={mockOnSuccess} />)
    const submitButton = screen.getByRole('button', { name: /Submitting/i })
    expect(submitButton).toBeDisabled()
  })

  it('shows loading indicator during submission', async () => {
    const { useProfileSubmit } = await import('../../hooks/useProfileSubmit')
    vi.mocked(useProfileSubmit).mockReturnValueOnce({
      submit: vi.fn(),
      isLoading: true,
      error: null
    })

    render(<ProfileForm onSuccess={mockOnSuccess} />)
    expect(screen.getByText(/Submitting/i)).toBeInTheDocument()
  })

  it('displays error message on submission failure', async () => {
    const { useProfileSubmit } = await import('../../hooks/useProfileSubmit')
    vi.mocked(useProfileSubmit).mockReturnValueOnce({
      submit: vi.fn(),
      isLoading: false,
      error: 'Failed to create profile'
    })

    render(<ProfileForm onSuccess={mockOnSuccess} />)
    expect(screen.getByText('Failed to create profile')).toBeInTheDocument()
  })

  it('updates character count for portfolio URL', async () => {
    const user = userEvent.setup()
    render(<ProfileForm onSuccess={mockOnSuccess} />)

    const portfolioInput = screen.getByPlaceholderText(/https:\/\/yourportfolio.com/i)
    await user.type(portfolioInput, 'https://example.com')

    expect(screen.getByText(/19\/500 characters/)).toBeInTheDocument()
  })

  it('requires GitHub username', async () => {
    render(<ProfileForm onSuccess={mockOnSuccess} />)
    const submitButton = screen.getByRole('button', { name: /Start Review/i })
    await fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/GitHub username is required/i)).toBeInTheDocument()
    })
  })

  it('requires resume file', async () => {
    render(<ProfileForm onSuccess={mockOnSuccess} />)
    const githubInput = screen.getByPlaceholderText(/octocat/i)
    await fireEvent.change(githubInput, { target: { value: 'testuser' } })

    const submitButton = screen.getByRole('button', { name: /Start Review/i })
    await fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Resume file is required/i)).toBeInTheDocument()
    })
  })

  it('validates portfolio URL character limit', async () => {
    const user = userEvent.setup()
    render(<ProfileForm onSuccess={mockOnSuccess} />)

    const portfolioInput = screen.getByPlaceholderText(/https:\/\/yourportfolio.com/i) as HTMLTextAreaElement
    const longUrl = 'a'.repeat(501)
    await user.type(portfolioInput, longUrl)

    const submitButton = screen.getByRole('button', { name: /Start Review/i })
    await fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Portfolio URL must be 500 characters or less/i)).toBeInTheDocument()
    })
  })
})
