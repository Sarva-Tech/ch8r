import { ref } from 'vue'
import type { FormContext } from 'vee-validate'
import { setBackendErrors } from '~/lib/utils'

export interface FormError {
  error?: string
  details?: string
}

export function useApiErrorHandling() {
  const apiError = ref<FormError | null>(null)

  const handleError = (
    error: unknown,
    form?: FormContext<any>,
    unexpectedErrorMessage?: string
  ) => {
    const err = error as {
      errors?: Record<string, string[] | string> | { error?: string; details?: string }
    }

    if (err.errors && typeof err.errors === 'object' && 'error' in err.errors) {
      const errorObj = err.errors as { error?: string; details?: string }
      apiError.value = {
        error: errorObj.error,
        details: errorObj.details
      }
    } else if (err.errors && typeof err.errors === 'object' && form) {
      setBackendErrors(form, err.errors as Record<string, string[] | string>)
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
