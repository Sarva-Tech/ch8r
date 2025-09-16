import { clsx } from 'clsx'
import type {ClassValue} from 'clsx';
import { twMerge } from 'tailwind-merge'
import type { FormContext } from 'vee-validate'

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
    return e.data?.message || e.data?.detail || e.message || e.statusMessage || 'Request failed'
  }
  return 'Unknown error'
}

export function setBackendErrors(form: FormContext, errors: Record<string, string[] | string>) {
  const formInstance = form
  if (!formInstance) return

  applyBackendErrors(formInstance, errors)
}

export function applyBackendErrors(
  formInstance: FormContext,
  errors: Record<string, string[] | string> | string
) {
  if (typeof errors === 'string') {
    formInstance.setFieldError('__form__', errors);
    return;
  }

  Object.entries(errors).forEach(([field, messages]) => {
    formInstance.setFieldError(
      field,
      Array.isArray(messages) ? messages.join(', ') : messages
    );
  });
}
