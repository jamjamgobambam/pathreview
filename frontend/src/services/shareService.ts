import { SharedReview } from '../types'
import { apiClient } from './api'

export async function generateShareLink(reviewId: string): Promise<{ shareUrl: string; expiresAt: string }> {
  const { share_url, expires_at } = await apiClient.createShareLink(reviewId)
  return {
    shareUrl: `${window.location.origin}${share_url}`,
    expiresAt: expires_at,
  }
}

export async function getSharedReview(token: string): Promise<SharedReview> {
  return apiClient.getSharedReview(token)
}
