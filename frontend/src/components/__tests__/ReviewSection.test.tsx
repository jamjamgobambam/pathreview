import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ReviewSection } from '../ReviewSection'
import { FeedbackSection } from '../../types'

describe('ReviewSection', () => {
  const mockSection: FeedbackSection = {
    section_name: 'Code Quality',
    content: 'Your code is well-structured and follows best practices.',
    suggestions: [
      {
        title: 'Add More Comments',
        description: 'Consider adding inline comments for complex logic'
      },
      {
        title: 'Improve Error Handling',
        description: 'Add try-catch blocks for async operations'
      }
    ],
    confidence: 0.85
  }

  const lowConfidenceSection: FeedbackSection = {
    ...mockSection,
    confidence: 0.25
  }

  it('renders section name and confidence score', () => {
    render(<ReviewSection section={mockSection} />)
    expect(screen.getByText('Code Quality')).toBeInTheDocument()
    expect(screen.getByText('85%')).toBeInTheDocument()
  })

  it('shows low confidence badge when confidence < 0.3', () => {
    render(<ReviewSection section={lowConfidenceSection} />)
    expect(screen.getByText('Low confidence')).toBeInTheDocument()
  })

  it('does not show low confidence badge when confidence >= 0.3', () => {
    render(<ReviewSection section={mockSection} />)
    expect(screen.queryByText('Low confidence')).not.toBeInTheDocument()
  })

  it('starts collapsed and expands on click', () => {
    render(<ReviewSection section={mockSection} />)
    const content = screen.getByText('Your code is well-structured and follows best practices.')
    expect(content.parentElement).not.toHaveClass('block')

    const button = screen.getByRole('button')
    fireEvent.click(button)
    expect(screen.getByText('Your code is well-structured and follows best practices.')).toBeInTheDocument()
  })

  it('expands on Enter key press', () => {
    render(<ReviewSection section={mockSection} />)
    const button = screen.getByRole('button')
    fireEvent.keyPress(button, { key: 'Enter', code: 'Enter', charCode: 13 })
    expect(screen.getByText('Your code is well-structured and follows best practices.')).toBeInTheDocument()
  })

  it('expands on Space key press', () => {
    render(<ReviewSection section={mockSection} />)
    const button = screen.getByRole('button')
    fireEvent.keyPress(button, { key: ' ', code: 'Space', charCode: 32 })
    expect(screen.getByText('Your code is well-structured and follows best practices.')).toBeInTheDocument()
  })

  it('renders all suggestions when expanded', () => {
    render(<ReviewSection section={mockSection} />)
    const button = screen.getByRole('button')
    fireEvent.click(button)

    expect(screen.getByText('Add More Comments')).toBeInTheDocument()
    expect(screen.getByText('Consider adding inline comments for complex logic')).toBeInTheDocument()
    expect(screen.getByText('Improve Error Handling')).toBeInTheDocument()
    expect(screen.getByText('Add try-catch blocks for async operations')).toBeInTheDocument()
  })

  it('sets aria-expanded correctly', () => {
    render(<ReviewSection section={mockSection} />)
    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('aria-expanded', 'false')

    fireEvent.click(button)
    expect(button).toHaveAttribute('aria-expanded', 'true')
  })

  it('has aria-controls attribute', () => {
    render(<ReviewSection section={mockSection} />)
    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('aria-controls', `section-${mockSection.section_name}`)
  })

  it('preserves line breaks in content', () => {
    const sectionWithLineBreaks: FeedbackSection = {
      ...mockSection,
      content: 'Line 1\nLine 2\nLine 3'
    }
    render(<ReviewSection section={sectionWithLineBreaks} />)
    const button = screen.getByRole('button')
    fireEvent.click(button)

    const contentElement = screen.getByText(/Line 1/)
    expect(contentElement).toHaveClass('whitespace-pre-wrap')
  })
})
