import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Loader } from 'lucide-react'
import { ReviewSection } from '../components/ReviewSection'
import { apiClient } from '../services/api'
import { ApiError, PublicReview } from '../types'

type LoadState = 'loading' | 'notfound' | 'expired' | 'ready'

export const SharedReviewPage: React.FC = () => {
  const { token } = useParams<{ token: string }>()
  const [review, setReview] = useState<PublicReview | null>(null)
  const [loadState, setLoadState] = useState<LoadState>('loading')

  useEffect(() => {
    const fetchSharedReview = async () => {
      try {
        const data = await apiClient.getSharedReview(token || '')
        setReview(data)
        setLoadState('ready')
      } catch (err) {
        // 410 means the token existed but expired; anything else is treated as not found.
        const status = (err as ApiError).status
        setLoadState(status === 410 ? 'expired' : 'notfound')
      }
    }
    fetchSharedReview()
  }, [token])

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {loadState === 'loading' && (
          <div className="p-8 bg-white rounded-lg shadow text-center">
            <Loader className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
            <p className="text-gray-900 font-semibold">Loading shared review...</p>
          </div>
        )}

        {loadState === 'expired' && (
          <div className="p-8 bg-white rounded-lg shadow text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">This link has expired</h1>
            <p className="text-gray-600">
              Shared review links are valid for 30 days. Ask the owner to generate a new one.
            </p>
          </div>
        )}

        {loadState === 'notfound' && (
          <div className="p-8 bg-white rounded-lg shadow text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Review not found</h1>
            <p className="text-gray-600">This shared link is invalid or is no longer available.</p>
          </div>
        )}

        {loadState === 'ready' && review && (
          <>
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900">Portfolio Review</h1>
              <p className="text-gray-600 mt-1">Shared read-only view</p>
            </div>

            {review.status !== 'complete' && (
              <div className="mb-8 p-8 bg-white rounded-lg shadow text-center">
                <p className="text-gray-900 font-semibold">
                  {review.status === 'failed'
                    ? 'This review could not be completed.'
                    : 'This review is still being generated. Check back soon.'}
                </p>
              </div>
            )}

            {review.status === 'complete' && (
              <>
                {review.overall_score != null && (
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
