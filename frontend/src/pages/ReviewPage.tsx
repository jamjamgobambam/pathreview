import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Share2, Download, ArrowLeft, Loader } from 'lucide-react'
import { useReviewStatus } from '../hooks/useReviewStatus'
import { ReviewSection } from '../components/ReviewSection'
import { apiClient } from '../services/api'
import { Review } from '../types'

export const ReviewPage: React.FC = () => {
  const { reviewId } = useParams<{ reviewId: string }>()
  const navigate = useNavigate()
  const [fullReview, setFullReview] = useState<Review | null>(null)
  const { review: statusReview, isPolling, error } = useReviewStatus(reviewId || '')
  const [fetchError, setFetchError] = useState('')

  useEffect(() => {
    if (!isPolling && statusReview?.status === 'complete') {
      const fetchFullReview = async () => {
        try {
          const data = await apiClient.getReview(reviewId || '')
          setFullReview(data)
        } catch (err) {
          setFetchError(err instanceof Error ? err.message : 'Failed to load review')
        }
      }
      fetchFullReview()
    }
  }, [isPolling, statusReview?.status, reviewId])

  const currentReview = fullReview || statusReview

  // Clamp the reported progress into 0-100 so a missing, out-of-range or
  // non-finite value from the API can never produce a broken bar width, and
  // snap to 100 once the review is complete so the bar never freezes partway.
  const rawProgress = statusReview?.progress_pct
  const progressPct =
    statusReview?.status === 'complete'
      ? 100
      : typeof rawProgress === 'number' && Number.isFinite(rawProgress)
        ? Math.min(100, Math.max(0, Math.round(rawProgress)))
        : 0

  const handleShare = () => {
    const url = window.location.href
    navigator.clipboard.writeText(url).then(() => {
      alert('Review link copied to clipboard!')
    })
  }

  const handleExport = () => {
    if (!fullReview || !fullReview.sections) return

    const text = `PathReview - Portfolio Review Report
=====================================

Score: ${fullReview.overall_score !== undefined ? Math.round(fullReview.overall_score * 100) : 'N/A'}/100

${fullReview.sections
  .map(
    (section) =>
      `${section.section_name} (Confidence: ${(section.confidence * 100).toFixed(0)}%)
---
${section.content}

Suggestions:
${section.suggestions.map((s) => `- ${s}`).join('\n')}
`
  )
  .join('\n\n')}`

    const blob = new Blob([text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `pathreview-${reviewId}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <button
          onClick={() => navigate('/dashboard')}
          className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-8 font-medium"
        >
          <ArrowLeft className="w-5 h-5" />
          Back to Dashboard
        </button>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {fetchError && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">{fetchError}</p>
          </div>
        )}

        {isPolling && (
          <div className="mb-12 p-8 bg-white rounded-lg shadow text-center">
            <p className="text-gray-900 font-semibold">Analyzing your portfolio...</p>
            {typeof statusReview?.progress_pct === 'number' ? (
              <>
                <div
                  className="mt-4 w-full bg-gray-200 rounded-full h-4 overflow-hidden"
                  role="progressbar"
                  aria-label="Review progress"
                  aria-valuenow={progressPct}
                  aria-valuemin={0}
                  aria-valuemax={100}
                >
                  <div
                    className="h-full bg-blue-600 transition-all"
                    style={{ width: `${progressPct}%` }}
                  ></div>
                </div>
                <p className="mt-2 text-sm font-medium text-blue-600">{progressPct}% complete</p>
              </>
            ) : (
              <Loader className="w-8 h-8 animate-spin text-blue-600 mx-auto mt-4" />
            )}
            <p className="text-gray-600 text-sm mt-2">This may take a few moments</p>
          </div>
        )}

        {currentReview?.status === 'failed' && (
          <div className="mb-12 p-8 bg-red-50 border border-red-200 rounded-lg text-center">
            <p className="text-red-800 font-semibold">Review Failed</p>
            <p className="text-red-600 text-sm mt-2">{currentReview.error_message || 'An error occurred'}</p>
          </div>
        )}

        {fullReview && fullReview.status === 'complete' && (
          <>
            <div className="mb-8 flex items-center justify-between">
              <h1 className="text-3xl font-bold text-gray-900">Portfolio Review</h1>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleShare}
                  className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium rounded-lg transition-colors"
                >
                  <Share2 className="w-5 h-5" />
                  Share
                </button>
                <button
                  onClick={handleExport}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
                >
                  <Download className="w-5 h-5" />
                  Export
                </button>
              </div>
            </div>

            {fullReview.overall_score !== undefined && (
              <div className="mb-8 bg-white rounded-lg shadow p-8">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Overall Score</h2>
                <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                  <div
                    className="h-full bg-blue-600 transition-all"
                    style={{ width: `${fullReview.overall_score * 100}%` }}
                  ></div>
                </div>
                <p className="mt-2 text-2xl font-bold text-blue-600">{Math.round(fullReview.overall_score * 100)}/100</p>
              </div>
            )}

            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-900">Feedback</h2>
              {fullReview.sections && fullReview.sections.length > 0 ? (
                fullReview.sections.map((section, index) => (
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
