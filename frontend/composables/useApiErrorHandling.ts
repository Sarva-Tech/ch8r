import { ref } from 'vue'
import type { FormContext } from 'vee-validate'
import { setBackendErrors } from '~/lib/utils'

export interface FormError {
  error?: string
  details?: string
}

export function useApiErrorHandling<T extends Record<string, unknown> = Record<string, unknown>>() {
  const apiError = ref<FormError | null>(null)

  const handleError = (
    error: unknown,
    form?: FormContext<T>,
    unexpectedErrorMessage?: string
  ) => {
    const err = error as {
      errors?: Record<string, unknown> | { error?: string, details?: string }
    }

    if (err.errors && typeof err.errors === 'object') {
      if ('error' in err.errors) {
        const errorObj = err.errors as { error?: string, details?: string }
        apiError.value = {
          error: errorObj.error,
          details: errorObj.details
        }
      } else if ('non_field_errors' in err.errors) {
        const nfe = (err.errors as Record<string, unknown>).non_field_errors
        const first = Array.isArray(nfe) ? nfe[0] : nfe
        if (first && typeof first === 'object' && 'error' in (first as object)) {
          const e = first as { error?: string, details?: string }
          apiError.value = { error: e.error, details: e.details }
        } else {
          apiError.value = { error: String(first) }
        }
      } else if (form) {
        setBackendErrors(form, err.errors as Record<string, string[] | string>)
      } else {
        apiError.value = {
          error: 'Unexpected Error',
          details: unexpectedErrorMessage || 'An unexpected error occurred'
        }
      }
    } else {
      apiError.value = {
        error: 'Unexpected Error',
        details: unexpectedErrorMessage || 'An unexpected error occurred'
      }
    }
  }

  const clearError = () => {
    apiError.value = null
  }

  return {
    apiError,
    handleError,
    clearError
  }
}
