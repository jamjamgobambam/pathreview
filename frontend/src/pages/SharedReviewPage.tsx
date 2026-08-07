import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Loader } from 'lucide-react'
import { getSharedReview } from '../services/shareService'
import { ReviewSection } from '../components/ReviewSection'
import { SharedReview } from '../types'

export const SharedReviewPage: React.FC = () => {
  const { shareToken } = useParams<{ shareToken: string }>()
  const [review, setReview] = useState<SharedReview | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!shareToken) return
    getSharedReview(shareToken)
      .then(setReview)
      .catch((err) => setError(err instanceof Error ? err.message : 'This link is invalid or has expired'))
      .finally(() => setLoading(false))
  }, [shareToken])

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {loading && (
          <div className="mb-12 p-8 bg-white rounded-lg shadow text-center">
            <Loader className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
            <p className="text-gray-900 font-semibold">Loading portfolio review...</p>
          </div>
        )}

        {error && !loading && (
          <div className="mb-12 p-8 bg-red-50 border border-red-200 rounded-lg text-center">
            <p className="text-red-800 font-semibold">Share link not found</p>
            <p className="text-red-600 text-sm mt-2">{error}</p>
          </div>
        )}

        {review && !loading && (
          <>
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900">Portfolio Review</h1>
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
                <p className="mt-2 text-2xl font-bold text-blue-600">{Math.round(review.overall_score * 100)}/100</p>
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
      </div>
    </div>
  )
}
