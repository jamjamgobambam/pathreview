export interface User {
  id: string
  email: string
}

export interface Profile {
  id: string
  github_username: string
  resume_url?: string
  portfolio_url?: string
  created_at: string
  updated_at: string
}

export interface FeedbackSection {
  section_name: string
  content: string
  suggestions: string[]
  confidence: number
}

export interface Review {
  id: string
  profile_id: string
  status: 'pending' | 'processing' | 'complete' | 'failed'
  overall_score?: number
  sections?: FeedbackSection[]
  error_message?: string
  created_at: string
  updated_at: string
}

export interface ReviewListResponse {
  items: Review[]
  total: number
  page: number
  page_size: number
}

export interface AuthResponse {
  access_token: string
  token_type: string
}

export interface ShareLink {
  share_url: string
  token: string
  expires_at: string
}

export interface PublicReview {
  status: 'pending' | 'processing' | 'complete' | 'failed'
  overall_score?: number
  sections?: FeedbackSection[]
  created_at: string
}

export interface ApiError extends Error {
  status?: number
}
