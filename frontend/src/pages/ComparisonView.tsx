import React, { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { apiClient } from '../services/api'
import { Review } from '../types'
import { StatusBadge } from '../components/StatusBadge'
import { ComparisonSection } from '../components/ComparisonSection'
import { formatDate } from '../utils/dateFormatters'
import { compareReviews, ReviewComparison } from '../utils/diffFormatter'

const BackLink: React.FC = () => {
  const navigate = useNavigate()
  return (
    <button
      onClick={() => navigate('/reviews')}
      className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-8 font-medium"
    >
      <ArrowLeft className="w-5 h-5" />
      Back to Review History
    </button>
  )
}

const Message: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="p-8 bg-white rounded-lg shadow text-center">
    <p className="text-gray-700">{children}</p>
  </div>
)

export const ComparisonView: React.FC = () => {
  const [searchParams] = useSearchParams()
  const idA = searchParams.get('a')
  const idB = searchParams.get('b')

  const [reviewA, setReviewA] = useState<Review | null>(null)
  const [reviewB, setReviewB] = useState<Review | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!idA || !idB || idA === idB) {
      setIsLoading(false)
      return
    }

    const fetchReviews = async () => {
      try {
        const [a, b] = await Promise.all([apiClient.getReview(idA), apiClient.getReview(idB)])
        setReviewA(a)
        setReviewB(b)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load reviews')
      } finally {
        setIsLoading(false)
      }
    }

    fetchReviews()
  }, [idA, idB])

  let content: React.ReactNode

  if (!idA || !idB) {
    content = <Message>Select two reviews to compare.</Message>
  } else if (idA === idB) {
    content = <Message>Select two different reviews to compare.</Message>
  } else if (isLoading) {
    content = <Message>Loading comparison...</Message>
  } else if (error) {
    content = <Message>{error}</Message>
  } else if (reviewA && reviewB) {
    const incomplete = [reviewA, reviewB].filter((r) => r.status !== 'complete')
    if (incomplete.length > 0) {
      content = (
        <Message>
          Both reviews must be complete to compare. {incomplete.length} review
          {incomplete.length > 1 ? 's are' : ' is'} not yet complete.
        </Message>
      )
    } else {
      const [older, newer] =
        new Date(reviewA.created_at).getTime() <= new Date(reviewB.created_at).getTime()
          ? [reviewA, reviewB]
          : [reviewB, reviewA]
      const comparison: ReviewComparison = compareReviews(older, newer)
      const olderPct =
        comparison.older.overall_score !== undefined
          ? Math.round(comparison.older.overall_score * 100)
          : undefined
      const newerPct =
        comparison.newer.overall_score !== undefined
          ? Math.round(comparison.newer.overall_score * 100)
          : undefined
      const deltaPct =
        comparison.overallScoreDelta !== undefined ? Math.round(comparison.overallScoreDelta * 100) : undefined

      content = (
        <>
          <div className="mb-8 bg-white rounded-lg shadow p-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <p className="text-sm text-gray-600">Older review</p>
                <p className="font-medium text-gray-900">{formatDate(older.created_at)}</p>
                <StatusBadge status={older.status} />
              </div>
              <div>
                <p className="text-sm text-gray-600">Newer review</p>
                <p className="font-medium text-gray-900">{formatDate(newer.created_at)}</p>
                <StatusBadge status={newer.status} />
              </div>
            </div>

            <div className="mt-6 pt-6 border-t border-gray-200 flex items-center gap-4">
              <div>
                <p className="text-sm text-gray-600">Overall score</p>
                <p className="text-2xl font-bold text-gray-900">
                  {olderPct ?? '—'} → {newerPct ?? '—'}
                </p>
              </div>
              {deltaPct !== undefined && (
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium ${
                    deltaPct > 0
                      ? 'bg-green-100 text-green-800'
                      : deltaPct < 0
                        ? 'bg-red-100 text-red-800'
                        : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {deltaPct > 0 ? '+' : ''}
                  {deltaPct}
                </span>
              )}
            </div>
          </div>

          {!comparison.hasAnyDiff ? (
            <Message>No changes between these reviews.</Message>
          ) : (
            <div className="space-y-6">
              {comparison.sections.map((section) => (
                <ComparisonSection key={section.section_name} diff={section} />
              ))}
            </div>
          )}
        </>
      )
    }
  } else {
    content = null
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <BackLink />
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Compare Reviews</h1>
          <p className="text-gray-600 mt-2">See how your portfolio review changed over time</p>
        </div>
        {content}
      </div>
    </div>
  )
}
