import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Loader } from 'lucide-react'
import { ReviewSection } from '../components/ReviewSection'
import { apiClient } from '../services/api'
import { PublicReviewResponse } from '../types'

type PageError = 'expired' | 'not_found' | 'error'

export const PublicReviewPage: React.FC = () => {
  const { token } = useParams<{ token: string }>()
  const [review, setReview] = useState<PublicReviewResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [pageError, setPageError] = useState<PageError | null>(null)

  useEffect(() => {
    if (!token) {
      setPageError('not_found')
      setIsLoading(false)
      return
    }
    const fetchReview = async () => {
      try {
        const data = await apiClient.getPublicReview(token)
        setReview(data)
      } catch (err) {
        if (err instanceof Error && err.message === 'EXPIRED') {
          setPageError('expired')
        } else if (err instanceof Error && err.message === 'NOT_FOUND') {
          setPageError('not_found')
        } else {
          setPageError('error')
        }
      } finally {
        setIsLoading(false)
      }
    }
    fetchReview()
  }, [token])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    )
  }

  if (pageError === 'expired') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-sm">
          <h1 className="text-2xl font-bold text-gray-900">This link has expired</h1>
          <p className="text-gray-600 mt-2">
            Share links are valid for 30 days. Ask the owner to generate a new one.
          </p>
        </div>
      </div>
    )
  }

  if (pageError) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-sm">
          <h1 className="text-2xl font-bold text-gray-900">Review not found</h1>
          <p className="text-gray-600 mt-2">
            This link is invalid or no longer exists.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Portfolio Review</h1>

        {review?.overall_score !== undefined && (
          <div className="mb-8 bg-white rounded-lg shadow p-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Overall Score</h2>
            <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
              <div
                className="h-full bg-blue-600 transition-all"
                style={{ width: `${review.overall_score * 100}%` }}
              />
            </div>
            <p className="mt-2 text-2xl font-bold text-blue-600">
              {Math.round(review.overall_score * 100)}/100
            </p>
          </div>
        )}

        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-gray-900">Feedback</h2>
          {review?.sections && review.sections.length > 0 ? (
            review.sections.map((section, index) => (
              <ReviewSection key={index} section={section} />
            ))
          ) : (
            <p className="text-gray-600">No feedback sections available</p>
          )}
        </div>
      </div>
    </div>
  )
}
