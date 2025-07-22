import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message
  if (typeof error === 'string') return error
  if (typeof error === 'object' && error !== null) {
    const e = error as {
      data?: { message?: string; detail?: string }
      message?: string
      statusMessage?: string
    }
    return e.data?.message || e.data?.detail || e.message || e.statusMessage || 'API request failed'
  }
  return 'Unknown error'
}
