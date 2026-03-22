import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, TrendingUp, Calendar } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { apiClient } from '../services/api'
import { Review } from '../types'
import { StatusBadge } from '../components/StatusBadge'
import { formatDate, formatRelativeDate } from '../utils/dateFormatters'

export const DashboardPage: React.FC = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [reviews, setReviews] = useState<Review[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchReviews = async () => {
      try {
        const response = await apiClient.listReviews(1, 5)
        setReviews(response.reviews)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load reviews')
      } finally {
        setIsLoading(false)
      }
    }

    fetchReviews()
  }, [])

  const lastReviewDate = reviews.length > 0 ? reviews[0].created_at : null
  const completedCount = reviews.filter(r => r.status === 'complete').length

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Welcome back, {user?.email}
          </h1>
          <p className="text-gray-600">
            Get AI-powered feedback on your portfolio and career trajectory
          </p>
        </div>

        <button
          onClick={() => navigate('/profiles/new')}
          className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors mb-12"
        >
          <Plus className="w-5 h-5" />
          Start a New Review
        </button>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm font-medium">Total Reviews</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{reviews.length}</p>
              </div>
              <TrendingUp className="w-10 h-10 text-blue-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm font-medium">Completed</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{completedCount}</p>
              </div>
              <TrendingUp className="w-10 h-10 text-green-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm font-medium">Last Review</p>
                <p className="text-lg font-bold text-gray-900 mt-1">
                  {lastReviewDate ? formatRelativeDate(lastReviewDate) : 'Never'}
                </p>
              </div>
              <Calendar className="w-10 h-10 text-purple-500" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Recent Reviews</h2>
          </div>

          {error && (
            <div className="p-6 text-center">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          {isLoading ? (
            <div className="p-6 text-center">
              <p className="text-gray-600">Loading reviews...</p>
            </div>
          ) : reviews.length === 0 ? (
            <div className="p-12 text-center">
              <p className="text-gray-600 mb-4">No reviews yet</p>
              <button
                onClick={() => navigate('/profiles/new')}
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                Start your first review
              </button>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {reviews.map((review) => (
                <button
                  key={review.id}
                  onClick={() => navigate(`/reviews/${review.id}`)}
                  className="w-full px-6 py-4 hover:bg-gray-50 transition-colors text-left"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900">Review #{review.id.slice(0, 8)}</p>
                      <p className="text-sm text-gray-600">{formatDate(review.created_at)}</p>
                    </div>
                    <StatusBadge status={review.status} />
                  </div>
                </button>
              ))}
            </div>
          )}

          {reviews.length > 0 && (
            <div className="px-6 py-4 border-t border-gray-200">
              <button
                onClick={() => navigate('/reviews')}
                className="text-blue-600 hover:text-blue-700 font-medium text-sm"
              >
                View all reviews →
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
