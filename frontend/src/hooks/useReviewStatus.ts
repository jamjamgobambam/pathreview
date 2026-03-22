import { useState, useEffect } from 'react'
import { apiClient } from '../services/api'
import { Review } from '../types'

interface UseReviewStatusReturn {
  review: Review | null
  isPolling: boolean
  error: string | null
}

export function useReviewStatus(reviewId: string): UseReviewStatusReturn {
  const [review, setReview] = useState<Review | null>(null)
  const [isPolling, setIsPolling] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null

    const fetchStatus = async () => {
      try {
        const data = await apiClient.getReviewStatus(reviewId)
        setReview(data)
        setError(null)

        if (data.status === 'complete' || data.status === 'failed') {
          setIsPolling(false)
          if (interval) clearInterval(interval)
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to fetch review status'
        setError(message)
      }
    }

    if (isPolling) {
      fetchStatus()
      interval = setInterval(fetchStatus, 3000)
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [reviewId, isPolling])

  return { review, isPolling, error }
}
