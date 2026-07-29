import { PublicReview, ShareLinkResult } from '../types'

const API_BASE = '/api'

function authHeader(): Record<string, string> {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

/**
 * Mint a public, 30-day share link for a review the current user owns.
 * Requires authentication. Returns the full public URL (built from the
 * returned token) and the link's expiry.
 */
export async function mintShareLink(reviewId: string): Promise<ShareLinkResult> {
  const response = await fetch(`${API_BASE}/reviews/${reviewId}/share`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeader(),
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || 'Failed to create share link')
  }

  const data = await response.json()
  return {
    url: `${window.location.origin}/shared/${data.token}`,
    expiresAt: data.expires_at,
  }
}

/**
 * Fetch the read-only view of a shared review by token. This is the public
 * endpoint, so it intentionally sends NO auth header — a logged-out visitor
 * must be able to call it. Throws on 404 (unknown/expired) or 410 (expired).
 */
export async function getSharedReview(token: string): Promise<PublicReview> {
  const response = await fetch(`${API_BASE}/reviews/shared/${token}`)

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || 'Failed to load shared review')
  }

  return response.json()
}
