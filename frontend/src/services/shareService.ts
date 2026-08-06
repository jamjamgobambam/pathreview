const API_BASE = '/api'

export interface ShareLinkResponse {
  share_token: string
  share_url: string
  expires_at: string
}

export async function createShareLink(reviewId: string): Promise<ShareLinkResponse> {
  const token = localStorage.getItem('token')
  const response = await fetch(`${API_BASE}/reviews/${reviewId}/share`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || 'Failed to create share link')
  }

  return response.json()
}
