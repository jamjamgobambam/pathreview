import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ShareModal } from '../ShareModal'

describe('ShareModal', () => {
  const baseProps = {
    isOpen: true,
    onClose: () => {},
    shareUrl: 'http://localhost:5173/shared/abc123',
    isLoading: false,
    error: ''
  }

  const stubClipboard = (writeText: () => Promise<void>) => {
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: vi.fn(writeText) },
      configurable: true,
      writable: true
    })
  }

  beforeEach(() => {
    stubClipboard(() => Promise.resolve())
  })

  it('renders nothing when closed', () => {
    const { container } = render(<ShareModal {...baseProps} isOpen={false} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('shows a loading state while the link is being generated', () => {
    render(<ShareModal {...baseProps} isLoading={true} shareUrl={null} />)
    expect(screen.getByText('Generating share link...')).toBeInTheDocument()
  })

  it('shows an error message when link creation failed', () => {
    render(<ShareModal {...baseProps} shareUrl={null} error="Failed to create share link" />)
    expect(screen.getByText('Failed to create share link')).toBeInTheDocument()
  })

  it('displays the share url in a read-only field', () => {
    render(<ShareModal {...baseProps} />)
    const input = screen.getByLabelText('Share link') as HTMLInputElement
    expect(input.value).toBe('http://localhost:5173/shared/abc123')
    expect(input.readOnly).toBe(true)
  })

  it('copies the url and flips the button to Copied', async () => {
    render(<ShareModal {...baseProps} />)
    fireEvent.click(screen.getByText('Copy'))
    await waitFor(() => expect(screen.getByText('Copied')).toBeInTheDocument())
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      'http://localhost:5173/shared/abc123'
    )
  })

  it('shows a manual-copy message when the clipboard write fails', async () => {
    stubClipboard(() => Promise.reject(new Error('blocked')))
    render(<ShareModal {...baseProps} />)
    fireEvent.click(screen.getByText('Copy'))
    await waitFor(() => expect(screen.getByText(/copy it manually/i)).toBeInTheDocument())
    expect(screen.queryByText('Copied')).not.toBeInTheDocument()
  })

  it('calls onClose when the close button is clicked', () => {
    const onClose = vi.fn()
    render(<ShareModal {...baseProps} onClose={onClose} />)
    fireEvent.click(screen.getByLabelText('Close'))
    expect(onClose).toHaveBeenCalled()
  })
})
