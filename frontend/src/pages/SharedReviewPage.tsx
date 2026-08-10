import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Loader, Clock } from 'lucide-react'
import { ReviewSection } from '../components/ReviewSection'
import { apiClient } from '../services/api'
import { Review } from '../types'

export const SharedReviewPage: React.FC = () => {
  const { reviewId } = useParams<{ reviewId: string }>()
  const [review, setReview] = useState<Review | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!reviewId) return

    const fetchSharedReview = async () => {
      try {
        const data = await apiClient.getSharedReview(reviewId)
        setReview(data)
      } catch (err) {
        setError(
          err instanceof Error ? err.message : 'This review is private or the link has expired'
        )
      } finally {
        setIsLoading(false)
      }
    }

    fetchSharedReview()
  }, [reviewId])

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {isLoading && (
          <div className="mb-12 p-8 bg-white rounded-lg shadow text-center">
            <Loader className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
            <p className="text-gray-900 font-semibold">Loading shared review...</p>
          </div>
        )}

        {!isLoading && error && (
          <div className="p-8 bg-red-50 border border-red-200 rounded-lg text-center">
            <p className="text-red-800 font-semibold">Review Unavailable</p>
            <p className="text-red-600 text-sm mt-2">{error}</p>
          </div>
        )}

        {!isLoading && review && (
          <>
            <div className="mb-6">
              <h1 className="text-3xl font-bold text-gray-900">Portfolio Review</h1>
              {review.share_expires_at && (
                <p className="mt-2 flex items-center gap-2 text-sm text-gray-500">
                  <Clock className="w-4 h-4" />
                  Shared link expires on {new Date(review.share_expires_at).toLocaleDateString()}
                </p>
              )}
            </div>

            {review.status === 'failed' && (
              <div className="mb-12 p-8 bg-red-50 border border-red-200 rounded-lg text-center">
                <p className="text-red-800 font-semibold">Review Failed</p>
                <p className="text-red-600 text-sm mt-2">{review.error_message || 'An error occurred'}</p>
              </div>
            )}

            {review.status === 'complete' && (
              <>
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
          </>
        )}
      </div>
    </div>
  )
}
