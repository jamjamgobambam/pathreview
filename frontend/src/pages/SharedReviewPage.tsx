import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Loader } from 'lucide-react'
import { ReviewSection } from '../components/ReviewSection'
import { getSharedReview } from '../services/shareService'
import { PublicReview } from '../types'

export const SharedReviewPage: React.FC = () => {
  const { token } = useParams<{ token: string }>()
  const [review, setReview] = useState<PublicReview | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const data = await getSharedReview(token || '')
        setReview(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load shared review')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [token])

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {loading && (
          <div className="p-8 bg-white rounded-lg shadow text-center">
            <Loader className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
            <p className="text-gray-900 font-semibold">Loading shared review...</p>
          </div>
        )}

        {error && !loading && (
          <div className="p-8 bg-red-50 border border-red-200 rounded-lg text-center">
            <p className="text-red-800 font-semibold">This link isn&apos;t available</p>
            <p className="text-red-600 text-sm mt-2">{error}</p>
          </div>
        )}

        {review && !loading && (
          <>
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900">Portfolio Review</h1>
              <p className="text-gray-600 text-sm mt-1">Shared read-only view</p>
            </div>

            {typeof review.overall_score === 'number' && (
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
      </div>
    </div>
  )
}
