import { apiClient } from './api'

/**
 * Call POST /reviews/{reviewId}/share to generate (or retrieve an existing
 * active) share token and return the full public URL ready to paste.
 */
export async function generateShareLink(reviewId: string): Promise<string> {
  const response = await apiClient.createShareToken(reviewId)
  return response.share_url
}
