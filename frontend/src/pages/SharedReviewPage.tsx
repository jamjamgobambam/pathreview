import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Loader } from 'lucide-react'
import { ReviewSection } from '../components/ReviewSection'
import { apiClient } from '../services/api'
import { PublicReview } from '../types'

/**
 * Public, read-only view of a shared review summary.
 *
 * Rendered at `/shared/:shareToken` outside the authenticated area so anyone
 * with the link can view a sanitized review without logging in.
 */
export const SharedReviewPage: React.FC = () => {
  const { shareToken } = useParams<{ shareToken: string }>()
  const [review, setReview] = useState<PublicReview | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchSharedReview = async () => {
      if (!shareToken) return
      try {
        const data = await apiClient.getSharedReview(shareToken)
        setReview(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'This shared review is not available')
      } finally {
        setIsLoading(false)
      }
    }
    fetchSharedReview()
  }, [shareToken])

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {isLoading && (
          <div className="mb-12 p-8 bg-white rounded-lg shadow text-center">
            <Loader className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
            <p className="text-gray-900 font-semibold">Loading shared review...</p>
          </div>
        )}

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {review && review.status === 'complete' && (
          <>
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900">Portfolio Review</h1>
              <p className="text-gray-600 text-sm mt-1">Shared read-only summary</p>
            </div>

            {review.overall_score !== undefined && (
              <div className="mb-8 bg-white rounded-lg shadow p-8">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Overall Score</h2>
                <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                  <div
                    className="h-full bg-blue-600 transition-all"
                    style={{ width: `${review.overall_score * 100}%` }}
                  ></div>
                </div>
                <p className="mt-2 text-2xl font-bold text-blue-600">
                  {Math.round(review.overall_score * 100)}/100
                </p>
              </div>
            )}

            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-900">Feedback</h2>
              {review.sections && review.sections.length > 0 ? (
                review.sections.map((section, index) => (
                  <ReviewSection key={index} section={section} />
                ))
              ) : (
                <p className="text-gray-600">No feedback sections available</p>
              )}
            </div>
          </>
        )}

        {review && review.status !== 'complete' && !error && (
          <div className="mb-12 p-8 bg-white rounded-lg shadow text-center">
            <p className="text-gray-900 font-semibold">This review is not ready to view yet.</p>
          </div>
        )}
      </div>
    </div>
  )
}
