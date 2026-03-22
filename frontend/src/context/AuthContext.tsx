import React, { createContext, useState, useContext, useEffect } from 'react'
import { User } from '../types'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    const userEmail = localStorage.getItem('userEmail')

    if (token && userEmail) {
      setUser({
        id: userEmail,
        email: userEmail
      })
    }

    setIsLoading(false)
  }, [])

  const login = async (email: string, password: string) => {
    const { apiClient } = await import('../services/api')
    const token = await apiClient.login(email, password)
    localStorage.setItem('token', token)
    localStorage.setItem('userEmail', email)
    setUser({ id: email, email })
  }

  const register = async (email: string, password: string) => {
    const { apiClient } = await import('../services/api')
    const token = await apiClient.register(email, password)
    localStorage.setItem('token', token)
    localStorage.setItem('userEmail', email)
    setUser({ id: email, email })
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('userEmail')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
