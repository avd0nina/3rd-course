import axios, { AxiosError } from 'axios'
import { getAuthToken } from './auth'

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
  timeout: 20000,
})

http.interceptors.request.use(config => {
  const token = getAuthToken()
  if (!token) {
    return config
  }
  config.headers = config.headers ?? {}
  config.headers.Authorization = `Basic ${token}`
  return config
})

type ErrorPayload = {
  error?: string
  message?: string
  details?: string[]
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const payload = error.response?.data as ErrorPayload | undefined
    if (payload?.details?.length) {
      return `${payload.error ?? 'Request error'}\n${payload.details.join('\n')}`
    }
    if (payload?.error) {
      return payload.error
    }
    if (payload?.message) {
      return payload.message
    }
    return error.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'Unexpected error'
}
