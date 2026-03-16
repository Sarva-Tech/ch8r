import { toast } from 'vue-sonner'
import { getErrorMessage, setBackendErrors } from './utils'

interface StandardError {
  success: false
  error_type: string
  message: string
  details?: string
  errors?: Record<string, any>
  status_code: number
}

function isStandardError(error: any): error is StandardError {
  return error &&
    typeof error === 'object' &&
    error.success === false &&
    error.error_type &&
    error.message
}

function extractErrorMessage(error: StandardError): string {
  if (error.errors) {
    const firstField = Object.keys(error.errors)[0]
    if (firstField) {
      const fieldError = error.errors[firstField]
      if (typeof fieldError === 'string') return fieldError
      if (typeof fieldError === 'object' && fieldError !== null) {
        const nestedField = Object.keys(fieldError)[0]
        if (nestedField) return String(fieldError[nestedField])
      }
      if (Array.isArray(fieldError)) return fieldError.join(', ')
    }
  }
  return error.details || error.message
}

export function showError(error: any, customMessage?: string) {
  if (isStandardError(error)) {
    toast.error(customMessage || extractErrorMessage(error))
    return
  }

  // Handle nested config errors (e.g. { config: { webhookUrl: '...' } })
  if (error.errors?.config) {
    if (typeof error.errors.config === 'object' && error.errors.config.webhookUrl) {
      toast.error(customMessage || error.errors.config.webhookUrl)
      return
    }
    if (typeof error.errors.config === 'string') {
      toast.error(customMessage || error.errors.config)
      return
    }
    if (Array.isArray(error.errors.config)) {
      toast.error(customMessage || error.errors.config.join(', '))
      return
    }
  }

  if (error.errors?.type) { toast.error(customMessage || error.errors.type); return }
  if (error.errors?.name) { toast.error(customMessage || error.errors.name); return }
  if (typeof error.errors === 'string') { toast.error(customMessage || error.errors); return }

  toast.error(customMessage || getErrorMessage(error) || 'Operation failed')
}

export function handleFormError(error: any, form: any, customMessage?: string) {
  if (error.errors && form) {
    setBackendErrors(form, error.errors)
  }
  showError(error, customMessage)
}
