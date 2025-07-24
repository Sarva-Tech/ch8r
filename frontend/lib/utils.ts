import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { STATUS_LABELS } from '~/lib/consts'
import type { StatusType } from '~/lib/consts'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function getStatusLabel(status: string): string {
  return STATUS_LABELS[status as StatusType] || ''
}
