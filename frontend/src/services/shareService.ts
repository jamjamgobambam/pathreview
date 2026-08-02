import { apiClient } from './api'

/**
 * Create (or reuse) a share link for a review and return the absolute share URL.
 * The backend returns the same non-expired link on repeat calls, so clicking
 * Share twice does not mint duplicate tokens.
 */
export async function createShareLink(reviewId: string): Promise<string> {
  const result = await apiClient.createShareLink(reviewId)
  return result.share_url
}

/**
 * Copy text to the clipboard. Throws if the Clipboard API is unavailable or the
 * browser rejects the write (for example outside a secure context), so callers
 * can surface a failure state instead of a false "Copied" confirmation.
 */
export async function copyToClipboard(text: string): Promise<void> {
  if (!navigator.clipboard) {
    throw new Error('Clipboard API is not available')
  }
  await navigator.clipboard.writeText(text)
}
