import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Loader } from 'lucide-react'
import { ReviewSection } from '../components/ReviewSection'
import { apiClient } from '../services/api'
import { Review } from '../types'

export const SharedReviewPage: React.FC = () => {
  const { token } = useParams<{ token: string }>()
  const [review, setReview] = useState<Review | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token) return

    const fetchSharedReview = async () => {
      try {
        const data = await apiClient.getSharedReview(token)
        setReview(data)
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'This link is invalid or has expired.'
        )
      } finally {
        setIsLoading(false)
      }
    }

    fetchSharedReview()
  }, [token])

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Portfolio Review</h1>
          <p className="text-sm text-gray-500 mt-1">Shared read-only summary</p>
        </div>

        {isLoading && (
          <div className="mb-12 p-8 bg-white rounded-lg shadow text-center">
            <Loader className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
            <p className="text-gray-900 font-semibold">Loading shared review...</p>
          </div>
        )}

        {error && (
          <div className="mb-6 p-8 bg-red-50 border border-red-200 rounded-lg text-center">
            <p className="text-red-800 font-semibold">Unable to load this review</p>
            <p className="text-red-600 text-sm mt-2">{error}</p>
          </div>
        )}

        {review && review.status === 'complete' && (
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

        {review && review.status !== 'complete' && (
          <div className="mb-12 p-8 bg-white rounded-lg shadow text-center">
            <p className="text-gray-900 font-semibold">This review isn't ready yet</p>
            <p className="text-gray-600 text-sm mt-2">
              Check back once the owner's review has finished processing.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}