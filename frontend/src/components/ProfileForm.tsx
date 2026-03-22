import React, { useState } from 'react'
import { Loader } from 'lucide-react'
import { useProfileSubmit } from '../hooks/useProfileSubmit'

interface ProfileFormProps {
  onSuccess: (profileId: string) => void
}

export const ProfileForm: React.FC<ProfileFormProps> = ({ onSuccess }) => {
  const [github, setGithub] = useState('')
  const [portfolioUrl, setPortfolioUrl] = useState('')
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const { submit, isLoading, error } = useProfileSubmit()

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!github.trim()) {
      newErrors.github = 'GitHub username is required'
    }

    if (!resumeFile) {
      newErrors.resume = 'Resume file is required'
    } else if (!['application/pdf', 'text/markdown', 'text/plain'].includes(resumeFile.type)) {
      newErrors.resume = 'Resume must be a PDF or Markdown file'
    } else if (resumeFile.size > 10 * 1024 * 1024) {
      newErrors.resume = 'Resume file must be under 10MB'
    }

    if (portfolioUrl && portfolioUrl.length > 500) {
      newErrors.portfolio = 'Portfolio URL must be 500 characters or less'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) return

    try {
      const formData = new FormData()
      formData.append('github_username', github)
      if (resumeFile) {
        formData.append('resume', resumeFile)
      }
      if (portfolioUrl) {
        formData.append('portfolio_url', portfolioUrl)
      }

      const profile = await submit(formData)
      onSuccess(profile.id)
    } catch (err) {
      console.error('Form submission failed:', err)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl">
      <div>
        <label htmlFor="github" className="block text-sm font-medium text-gray-900 mb-2">
          GitHub Username
        </label>
        <input
          id="github"
          type="text"
          value={github}
          onChange={(e) => setGithub(e.target.value)}
          placeholder="octocat"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        {errors.github && <p className="mt-1 text-sm text-red-600">{errors.github}</p>}
      </div>

      <div>
        <label htmlFor="resume" className="block text-sm font-medium text-gray-900 mb-2">
          Resume (PDF or Markdown, max 10MB)
        </label>
        <input
          id="resume"
          type="file"
          onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
          accept=".pdf,.md,.txt"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        {errors.resume && <p className="mt-1 text-sm text-red-600">{errors.resume}</p>}
        {resumeFile && <p className="mt-1 text-sm text-gray-600">{resumeFile.name}</p>}
      </div>

      <div>
        <label htmlFor="portfolio" className="block text-sm font-medium text-gray-900 mb-2">
          Portfolio URL (optional)
        </label>
        <textarea
          id="portfolio"
          value={portfolioUrl}
          onChange={(e) => setPortfolioUrl(e.target.value)}
          placeholder="https://yourportfolio.com"
          rows={3}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <p className="mt-1 text-xs text-gray-500">
          {portfolioUrl.length}/500 characters
        </p>
        {errors.portfolio && <p className="mt-1 text-sm text-red-600">{errors.portfolio}</p>}
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      <button
        type="submit"
        disabled={isLoading}
        className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold rounded-lg transition-colors"
      >
        {isLoading && <Loader className="w-5 h-5 animate-spin" />}
        {isLoading ? 'Submitting...' : 'Start Review'}
      </button>
    </form>
  )
}
