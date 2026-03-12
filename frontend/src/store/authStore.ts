import { create } from 'zustand'

interface User {
  id: string
  email: string
  full_name: string
  role: 'student' | 'employer' | 'admin'
  profile_picture: string | null
  bio: string
  university: string
  graduation_year: number | null
  is_active: boolean
  date_joined: string
  profile?: {
    target_role: string
    phone: string
    linkedin_url: string
    github_url: string
  }
}

interface AuthState {
  user: User | null
  accessToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  setAuth: (user: User, accessToken: string) => void
  clearAuth: () => void
  updateUser: (user: Partial<User>) => void
  setAccessToken: (token: string) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
}

export const useAuthStore = create<AuthState>()((set) => ({
  user: null,
  accessToken: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  setAuth: (user, accessToken) =>
    set({ user, accessToken, isAuthenticated: true, error: null }),
  clearAuth: () =>
    set({ user: null, accessToken: null, isAuthenticated: false, error: null }),
  updateUser: (updatedUser) =>
    set((state) => ({
      user: state.user ? { ...state.user, ...updatedUser } : null,
    })),
  setAccessToken: (token) => set({ accessToken: token }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}))
