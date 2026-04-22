/**
 * Auth Context
 * File: outreachx/frontend/lib/auth-context.tsx
 */

'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { useRouter } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface User {
  id: string
  email: string
  name: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser]       = useState<User | null>(null)
  const [token, setToken]     = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const storedToken = localStorage.getItem('outreachx_token')
    const storedUser  = localStorage.getItem('outreachx_user')
    if (storedToken && storedUser) {
      try {
        setToken(storedToken)
        setUser(JSON.parse(storedUser))
      } catch {}
    }
    setLoading(false)
  }, [])

  async function login(email: string, password: string) {
    // OAuth2 requires application/x-www-form-urlencoded — NOT FormData/JSON
    const body = new URLSearchParams()
    body.append('username', email)   // OAuth2 spec: field is "username" not "email"
    body.append('password', password)

    const res = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: body.toString(),
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Invalid email or password')
    }

    const data = await res.json()
    _saveSession(data.access_token, data.user)
    router.push('/dashboard')
  }

  async function register(email: string, password: string, name: string) {
    const res = await fetch(`${API_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, name }),
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Registration failed')
    }

    const data = await res.json()
    _saveSession(data.access_token, data.user)
    router.push('/dashboard')
  }

  function _saveSession(accessToken: string, userData: User) {
    setToken(accessToken)
    setUser(userData)
    localStorage.setItem('outreachx_token', accessToken)
    localStorage.setItem('outreachx_user', JSON.stringify(userData))
    // Also set cookie so Next.js middleware can read it
    document.cookie = `outreachx_token=${accessToken}; path=/; max-age=${30 * 24 * 60 * 60}; SameSite=Lax`
  }

  function logout() {
    setToken(null)
    setUser(null)
    localStorage.removeItem('outreachx_token')
    localStorage.removeItem('outreachx_user')
    document.cookie = 'outreachx_token=; path=/; max-age=0'
    router.push('/login')
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}