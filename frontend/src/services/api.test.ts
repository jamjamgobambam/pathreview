import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { apiClient } from './api'

describe('apiClient share methods', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
    localStorage.clear()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('createShareLink POSTs to the review share endpoint', async () => {
    const mockFetch = vi.mocked(fetch)
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ token: 'tok-1', expires_at: '2026-08-01T00:00:00Z' })
    } as Response)

    const result = await apiClient.createShareLink('rev-1')

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/reviews/rev-1/share',
      expect.objectContaining({ method: 'POST' })
    )
    expect(result).toEqual({ token: 'tok-1', expires_at: '2026-08-01T00:00:00Z' })
  })

  it('getSharedReview GETs the public share endpoint (no token in storage)', async () => {
    const mockFetch = vi.mocked(fetch)
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        overall_score: 0.5,
        sections: [],
        created_at: '2026-07-01T00:00:00Z',
        expires_at: '2026-08-01T00:00:00Z'
      })
    } as Response)

    const result = await apiClient.getSharedReview('tok-9')

    expect(mockFetch).toHaveBeenCalledWith('/api/share/tok-9', expect.any(Object))
    expect(result.overall_score).toBe(0.5)
  })

  it('throws with the server detail message when a share link is not found', async () => {
    const mockFetch = vi.mocked(fetch)
    mockFetch.mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'Share link not found or expired' })
    } as Response)

    await expect(apiClient.getSharedReview('bad')).rejects.toThrow(
      'Share link not found or expired'
    )
  })
})
