import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react"
import { API_BASE_URL } from "./lib/apiBase"
import { apiFetch, AUTH_TOKEN_KEY } from "./lib/authFetch"

export type AuthUser = {
  id: string
  username: string
  email: string
  full_name: string
  role: string
  active: boolean
  must_change_password: boolean
  customer_id?: string | null
}

type AuthContextValue = {
  user: AuthUser | null
  ready: boolean
  login: (email: string, password: string) => Promise<AuthUser>
  logout: () => void
  refreshUser: () => Promise<AuthUser>
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

async function errorMessage(response: Response): Promise<string> {
  const body = await response.json().catch(() => ({}))
  const detail = body?.detail ?? `Request failed (${response.status})`
  return typeof detail === "string" ? detail : JSON.stringify(detail)
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [ready, setReady] = useState(false)

  const logout = useCallback(() => {
    localStorage.removeItem(AUTH_TOKEN_KEY)
    setUser(null)
  }, [])

  const refreshUser = useCallback(async () => {
    const response = await apiFetch(`${API_BASE_URL}/api/auth/me`)
    if (!response.ok) throw new Error(await errorMessage(response))
    const currentUser = (await response.json()) as AuthUser
    setUser(currentUser)
    return currentUser
  }, [])

  useEffect(() => {
    let mounted = true
    const token = localStorage.getItem(AUTH_TOKEN_KEY)
    const onUnauthorized = () => {
      if (mounted) setUser(null)
    }
    window.addEventListener("costsheet:unauthorized", onUnauthorized)

    if (!token) {
      setReady(true)
    } else {
      void refreshUser()
        .catch(() => {
          localStorage.removeItem(AUTH_TOKEN_KEY)
          if (mounted) setUser(null)
        })
        .finally(() => {
          if (mounted) setReady(true)
        })
    }

    return () => {
      mounted = false
      window.removeEventListener("costsheet:unauthorized", onUnauthorized)
    }
  }, [refreshUser])

  const login = useCallback(async (email: string, password: string) => {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    })
    if (!response.ok) throw new Error(await errorMessage(response))
    const result = (await response.json()) as { token: string; user: AuthUser }
    localStorage.setItem(AUTH_TOKEN_KEY, result.token)
    setUser(result.user)
    return result.user
  }, [])

  const changePassword = useCallback(async (currentPassword: string, newPassword: string) => {
    const response = await apiFetch(`${API_BASE_URL}/api/auth/change-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    })
    if (!response.ok) throw new Error(await errorMessage(response))
  }, [])

  return (
    <AuthContext.Provider value={{ user, ready, login, logout, refreshUser, changePassword }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext)
  if (!value) throw new Error("AuthProvider is missing")
  return value
}
