import { useUserStore } from '~/stores/user'
import { getErrorMessage } from '~/lib/utils'

type Method = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
type Body = BodyInit | Record<string, any> | null | undefined

export const useHttpClient = () => {
  const config = useRuntimeConfig()
  const userStore = useUserStore()
  const baseURL = config.public.apiBaseUrl

  const request = async <T>(
    method: Method,
    url: string,
    {
      body,
      params,
      auth = true,
      headers = {}
    }: {
      body?: Body
      params?: Record<string, any>
      auth?: boolean
      headers?: HeadersInit
    } = {}
  ): Promise<T> => {
    const normalizedHeaders = Object.fromEntries(
      Object.entries(headers instanceof Headers ? Object.fromEntries(headers.entries()) : headers || {})
    ) as Record<string, string>

    if (auth) {
      const token = userStore.getToken?.value
      if (!token) throw new Error('Authentication token missing')
      normalizedHeaders.Authorization = `Token ${token}`
    }

    if (body instanceof FormData && normalizedHeaders['Content-Type']) {
      delete normalizedHeaders['Content-Type']
    }

    try {
      return await $fetch<T>(url, {
        baseURL,
        method,
        body,
        params,
        headers: normalizedHeaders,
      })
    } catch (error) {
      throw new Error(getErrorMessage(error))
    }
  }

  return {
    httpGet: <T>(url: string, params?: never, auth = true) =>
      request<T>('GET', url, { params, auth }),

    httpPost: <T>(url: string, body?: Body, auth = true) =>
      request<T>('POST', url, { body, auth }),

    httpPut: <T>(url: string, body?: Body, auth = true) =>
      request<T>('PUT', url, { body, auth }),

    httpPatch: <T>(url: string, body?: Body, auth = true) =>
      request<T>('PATCH', url, { body, auth }),

    httpDelete: <T>(url: string, auth = true) =>
      request<T>('DELETE', url, { auth }),

    httpPostForm: <T>(url: string, formData: FormData, auth = true) =>
      request<T>('POST', url, { body: formData, auth }),
  }
}
