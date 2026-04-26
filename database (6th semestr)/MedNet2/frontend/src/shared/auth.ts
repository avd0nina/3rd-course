import type { AuthMe } from './types'

const TOKEN_KEY = 'mednet-auth-token'
const USER_KEY = 'mednet-auth-user'

export function getAuthToken(): string {
  return localStorage.getItem(TOKEN_KEY) ?? ''
}

export function setAuthToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearAuthToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

export function getStoredUser(): AuthMe | null {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) {
    return null
  }
  try {
    return JSON.parse(raw) as AuthMe
  } catch {
    return null
  }
}

export function setStoredUser(user: AuthMe): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function clearStoredUser(): void {
  localStorage.removeItem(USER_KEY)
}

export function clearAuthState(): void {
  clearAuthToken()
  clearStoredUser()
}
