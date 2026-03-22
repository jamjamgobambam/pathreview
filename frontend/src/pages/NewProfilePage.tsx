import React from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { ProfileForm } from '../components/ProfileForm'
import { apiClient } from '../services/api'

export const NewProfilePage: React.FC = () => {
  const navigate = useNavigate()

  const handleProfileCreated = async (profileId: string) => {
    try {
      const review = await apiClient.createReview(profileId)
      navigate(`/reviews/${review.id}`)
    } catch (err) {
      console.error('Failed to create review:', err)
      navigate('/dashboard')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <button
          onClick={() => navigate('/dashboard')}
          className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-8 font-medium"
        >
          <ArrowLeft className="w-5 h-5" />
          Back to Dashboard
        </button>

        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Start Your Review</h1>
          <p className="text-gray-600 mt-2">
            Provide your GitHub profile, resume, and portfolio for a comprehensive AI-powered review
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-8">
          <ProfileForm onSuccess={handleProfileCreated} />
        </div>
      </div>
    </div>
  )
}
