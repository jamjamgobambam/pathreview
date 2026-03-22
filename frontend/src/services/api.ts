import { AuthResponse, Profile, Review, ReviewListResponse } from '../types'

const API_BASE = '/api'

class ApiClient {
  private getAuthHeader(): { Authorization: string } | {} {
    const token = localStorage.getItem('token')
    if (!token) return {}
    return { Authorization: `Bearer ${token}` }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE}${endpoint}`
    const headers = {
      'Content-Type': 'application/json',
      ...this.getAuthHeader(),
      ...options.headers
    }

    const response = await fetch(url, {
      ...options,
      headers
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.detail || `Request failed with status ${response.status}`)
    }

    return response.json()
  }

  async login(email: string, password: string): Promise<string> {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)

    const response = await fetch(`${API_BASE}/token`, {
      method: 'POST',
      body: formData,
      headers: {
        'Accept': 'application/json'
      }
    })

    if (!response.ok) {
      throw new Error('Invalid email or password')
    }

    const data: AuthResponse = await response.json()
    return data.access_token
  }

  async register(email: string, password: string): Promise<string> {
    const response = await fetch(`${API_BASE}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.detail || 'Registration failed')
    }

    const data: AuthResponse = await response.json()
    return data.access_token
  }

  async createProfile(formData: FormData): Promise<Profile> {
    const url = `${API_BASE}/profiles`
    const headers = this.getAuthHeader()

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.detail || 'Failed to create profile')
    }

    return response.json()
  }

  async getProfile(id: string): Promise<Profile> {
    return this.request(`/profiles/${id}`)
  }

  async createReview(profileId: string): Promise<Review> {
    return this.request('/reviews', {
      method: 'POST',
      body: JSON.stringify({ profile_id: profileId })
    })
  }

  async getReview(id: string): Promise<Review> {
    return this.request(`/reviews/${id}`)
  }

  async getReviewStatus(id: string): Promise<Review> {
    return this.request(`/reviews/${id}/status`)
  }

  async listReviews(page: number = 1, pageSize: number = 10): Promise<ReviewListResponse> {
    return this.request(`/reviews?page=${page}&page_size=${pageSize}`)
  }

  async deleteProfile(id: string): Promise<void> {
    return this.request(`/profiles/${id}`, { method: 'DELETE' })
  }
}

export const apiClient = new ApiClient()
