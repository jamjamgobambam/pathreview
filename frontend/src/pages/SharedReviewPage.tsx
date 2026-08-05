import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Loader } from 'lucide-react'

import { ReviewSection } from '../components/ReviewSection'
import { apiClient } from '../services/api'
import type { PublicReview } from '../types'

export default function SharedReviewPage() {
  const { shareToken } = useParams<{ shareToken: string }>()
  const [review, setReview] = useState<PublicReview | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadReview = async () => {
      if (!shareToken) {
        setError('Invalid share link')
        setLoading(false)
        return
      }

      try {
        const publicReview = await apiClient.getPublicReview(shareToken)
        setReview(publicReview)
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load shared review'
        )
      } finally {
        setLoading(false)
      }
    }

    loadReview()
  }, [shareToken])

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex items-center gap-2">
          <Loader className="h-5 w-5 animate-spin" />
          <span>Loading shared review...</span>
        </div>
      </div>
    )
  }

  if (error || !review) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12">
        <h1 className="mb-2 text-2xl font-bold">
          Shared Review Unavailable
        </h1>

        <p className="text-gray-600">
          {error || 'This shared review could not be found.'}
        </p>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">
          Shared Portfolio Review
        </h1>

        <p className="mt-2 text-gray-600">
          This is a read-only shared review.
        </p>
      </div>

      {review.overall_score !== null && (
        <div className="mb-8 rounded-lg border p-6">
          <h2 className="text-lg font-semibold">
            Overall Score
          </h2>

          <p className="mt-2 text-3xl font-bold">
            {review.overall_score}
          </p>
        </div>
      )}

      {review.sections && review.sections.length > 0 ? (
        <div className="space-y-6">
          {review.sections.map((section, index) => (
            <ReviewSection
              key={`${section.section_name}-${index}`}
              section={section}
            />
          ))}
        </div>
      ) : (
        <p>No review sections are available.</p>
      )}
    </div>
  )
}