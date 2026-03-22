import { useState } from 'react'
import { apiClient } from '../services/api'
import { Profile } from '../types'

interface UseProfileSubmitReturn {
  submit: (formData: FormData) => Promise<Profile>
  isLoading: boolean
  error: string | null
}

export function useProfileSubmit(): UseProfileSubmitReturn {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async (formData: FormData): Promise<Profile> => {
    setIsLoading(true)
    setError(null)

    try {
      const profile = await apiClient.createProfile(formData)
      return profile
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create profile'
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  return { submit, isLoading, error }
}
