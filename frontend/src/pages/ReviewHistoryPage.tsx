import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, ChevronLeft, ChevronRight } from 'lucide-react'
import { apiClient } from '../services/api'
import { Review } from '../types'
import { StatusBadge } from '../components/StatusBadge'
import { formatDate } from '../utils/dateFormatters'

export const ReviewHistoryPage: React.FC = () => {
  const navigate = useNavigate()
  const [reviews, setReviews] = useState<Review[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const pageSize = 10

  useEffect(() => {
    const fetchReviews = async () => {
      try {
        const response = await apiClient.listReviews(currentPage, pageSize)
        setReviews(response.reviews)
        setTotal(response.total)
        setError('')
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load reviews')
      } finally {
        setIsLoading(false)
      }
    }

    fetchReviews()
  }, [currentPage])

  const filteredReviews = reviews.filter((review) => {
    const searchLower = searchTerm.toLowerCase()
    return (
      review.id.toLowerCase().includes(searchLower) ||
      review.profile_id.toLowerCase().includes(searchLower) ||
      review.status.toLowerCase().includes(searchLower)
    )
  })

  const totalPages = Math.ceil(total / pageSize)
  const hasNextPage = currentPage < totalPages
  const hasPrevPage = currentPage > 1

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Review History</h1>
          <p className="text-gray-600 mt-2">View and manage all your portfolio reviews</p>
        </div>

        <div className="mb-6 relative">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search by review ID, profile ID, or status..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        <div className="bg-white rounded-lg shadow overflow-hidden">
          {isLoading ? (
            <div className="p-12 text-center">
              <p className="text-gray-600">Loading reviews...</p>
            </div>
          ) : filteredReviews.length === 0 ? (
            <div className="p-12 text-center">
              <p className="text-gray-600 mb-4">
                {searchTerm ? 'No reviews match your search' : 'No reviews yet'}
              </p>
              {!searchTerm && (
                <button
                  onClick={() => navigate('/profiles/new')}
                  className="text-blue-600 hover:text-blue-700 font-medium"
                >
                  Start your first review
                </button>
              )}
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Review ID</th>
                      <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Profile ID</th>
                      <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Status</th>
                      <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Score</th>
                      <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Date</th>
                      <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {filteredReviews.map((review) => (
                      <tr key={review.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4 text-sm font-medium text-gray-900">{review.id.slice(0, 12)}...</td>
                        <td className="px-6 py-4 text-sm text-gray-600">{review.profile_id.slice(0, 12)}...</td>
                        <td className="px-6 py-4">
                          <StatusBadge status={review.status} />
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600">
                          {review.overall_score !== undefined ? `${review.overall_score}/100` : '—'}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600">{formatDate(review.created_at)}</td>
                        <td className="px-6 py-4 text-sm">
                          <button
                            onClick={() => navigate(`/reviews/${review.id}`)}
                            className="text-blue-600 hover:text-blue-700 font-medium"
                          >
                            View
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {totalPages > 1 && (
                <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
                  <p className="text-sm text-gray-600">
                    Showing page {currentPage} of {totalPages}
                  </p>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                      disabled={!hasPrevPage}
                      className="inline-flex items-center gap-1 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      <ChevronLeft className="w-4 h-4" />
                      Previous
                    </button>
                    <button
                      onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                      disabled={!hasNextPage}
                      className="inline-flex items-center gap-1 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      Next
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
