export const AUTH_TOKEN_KEY = "costsheet_web_token"

export function authToken(): string | null {
  return localStorage.getItem(AUTH_TOKEN_KEY)
}

export async function apiFetch(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers)
  const token = authToken()
  if (token) headers.set("Authorization", `Bearer ${token}`)

  const response = await fetch(input, { ...init, headers })
  if (response.status === 401 && !String(input).includes("/api/auth/login")) {
    localStorage.removeItem(AUTH_TOKEN_KEY)
    window.dispatchEvent(new Event("costsheet:unauthorized"))
  }
  return response
}
