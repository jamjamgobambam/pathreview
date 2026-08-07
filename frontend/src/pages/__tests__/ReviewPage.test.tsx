/**
 * Tests for the "Copy Link" feature on ReviewPage (issue #101).
 *
 * These tests reproduce the missing feature: there is currently only a "Share"
 * button that copies window.location.href. The expected behavior is a "Copy Link"
 * button that calls the backend to generate a time-limited public token URL.
 *
 * All "Copy Link" tests will fail until the feature is implemented.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ReviewPage } from '../ReviewPage';

// --- Module mocks ---

vi.mock('../../hooks/useReviewStatus', () => ({
	useReviewStatus: vi.fn(() => ({
		review: null,
		isPolling: true,
		error: null,
	})),
}));

vi.mock('../../services/api', () => ({
	apiClient: {
		getReview: vi.fn(),
		createShareLink: vi.fn(),
	},
}));

// --- Helpers ---

const REVIEW_ID = 'review-123';

/** Returns an ISO 8601 timestamp 30 days from the time this is called. */
function thirtyDaysFromNow(): string {
	const d = new Date();
	d.setDate(d.getDate() + 30);
	return d.toISOString();
}

const completeReview = {
	id: REVIEW_ID,
	profile_id: 'profile-abc',
	status: 'complete' as const,
	overall_score: 0.85,
	sections: [
		{
			section_name: 'Technical Skills',
			content: 'Strong fundamentals demonstrated across projects.',
			suggestions: ['Add a systems design project'],
			confidence: 0.9,
		},
	],
	created_at: '2026-01-01T00:00:00Z',
	updated_at: '2026-01-01T00:00:00Z',
};

function renderReviewPage() {
	return render(
		<MemoryRouter initialEntries={[`/reviews/${REVIEW_ID}`]}>
			<Routes>
				<Route path="/reviews/:reviewId" element={<ReviewPage />} />
			</Routes>
		</MemoryRouter>,
	);
}

async function renderCompletedReviewPage() {
	const { useReviewStatus } = await import('../../hooks/useReviewStatus');
	vi.mocked(useReviewStatus).mockReturnValue({
		review: completeReview,
		isPolling: false,
		error: null,
	});

	const { apiClient } = await import('../../services/api');
	vi.mocked(apiClient.getReview).mockResolvedValue(completeReview);

	renderReviewPage();

	// Wait for the useEffect to fire apiClient.getReview and render the full review
	await waitFor(() => {
		expect(screen.getByText('Portfolio Review')).toBeInTheDocument();
	});
}

// --- Tests ---

describe('ReviewPage - Copy Link button (issue #101)', () => {
	beforeEach(() => {
		vi.clearAllMocks();

		Object.defineProperty(navigator, 'clipboard', {
			value: { writeText: vi.fn().mockResolvedValue(undefined) },
			writable: true,
			configurable: true,
		});
	});

	describe('Happy path', () => {
		it('renders a "Copy Link" button when the review is complete', async () => {
			await renderCompletedReviewPage();

			expect(screen.getByRole('button', { name: /copy link/i })).toBeInTheDocument();
		});

		it('calls apiClient.createShareLink with the review ID on click', async () => {
			const { apiClient } = await import('../../services/api');
			vi.mocked(apiClient.createShareLink).mockResolvedValue({
				token: 'public-token-abc',
				expires_at: thirtyDaysFromNow(),
			});

			await renderCompletedReviewPage();

			fireEvent.click(screen.getByRole('button', { name: /copy link/i }));

			await waitFor(() => {
				expect(apiClient.createShareLink).toHaveBeenCalledWith(REVIEW_ID);
			});
		});

		it('copies a public token URL (not window.location.href) to the clipboard', async () => {
			const { apiClient } = await import('../../services/api');
			vi.mocked(apiClient.createShareLink).mockResolvedValue({
				token: 'public-token-abc',
				expires_at: thirtyDaysFromNow(),
			});

			await renderCompletedReviewPage();

			fireEvent.click(screen.getByRole('button', { name: /copy link/i }));

			await waitFor(() => {
				expect(navigator.clipboard.writeText).toHaveBeenCalledWith(expect.stringContaining('public-token-abc'));
			});

			// Must NOT just copy the current authenticated URL
			const writtenUrl = vi.mocked(navigator.clipboard.writeText).mock.calls[0][0];
			expect(writtenUrl).not.toBe(window.location.href);
		});

		it('shows user feedback after the link is copied', async () => {
			const { apiClient } = await import('../../services/api');
			vi.mocked(apiClient.createShareLink).mockResolvedValue({
				token: 'public-token-abc',
				expires_at: thirtyDaysFromNow(),
			});

			await renderCompletedReviewPage();

			fireEvent.click(screen.getByRole('button', { name: /copy link/i }));

			await waitFor(() => {
				expect(screen.getByText(/copied|link copied/i)).toBeInTheDocument();
			});
		});
	});

	describe('Edge cases', () => {
		it('does not render "Copy Link" while the review is still processing', () => {
			renderReviewPage(); // default mock: isPolling=true, no fullReview

			expect(screen.queryByRole('button', { name: /copy link/i })).not.toBeInTheDocument();
		});

		it('does not render "Copy Link" when the review has failed', async () => {
			const { useReviewStatus } = await import('../../hooks/useReviewStatus');
			vi.mocked(useReviewStatus).mockReturnValue({
				review: { ...completeReview, status: 'failed', error_message: 'LLM timeout' },
				isPolling: false,
				error: null,
			});

			renderReviewPage();

			expect(screen.queryByRole('button', { name: /copy link/i })).not.toBeInTheDocument();
		});

		it('shows an error message when share link generation fails', async () => {
			const { apiClient } = await import('../../services/api');
			vi.mocked(apiClient.createShareLink).mockRejectedValue(new Error('Server error'));

			await renderCompletedReviewPage();

			fireEvent.click(screen.getByRole('button', { name: /copy link/i }));

			await waitFor(() => {
				expect(screen.getByText(/failed to generate|could not create/i)).toBeInTheDocument();
			});
		});

		it('disables "Copy Link" button while the share link is being generated', async () => {
			const { apiClient } = await import('../../services/api');
			// Never resolves during the test — simulates an in-flight request
			vi.mocked(apiClient.createShareLink).mockReturnValue(new Promise(() => {}));

			await renderCompletedReviewPage();

			const copyButton = screen.getByRole('button', { name: /copy link/i });
			fireEvent.click(copyButton);

			await waitFor(() => {
				expect(copyButton).toBeDisabled();
			});
		});
	});
});
