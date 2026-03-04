import { defineStore } from 'pinia'
import { useHttpClient } from '@/composables/useHttpClient'

export type AIProviderType = 'text' | 'embedding' | 'image' | 'rerank' | 'other'

export interface AIProvider {
  id: number
  uuid: string

  owner: number

  name: string
  provider_api_key?: string | null
  base_url?: string | null
  provider: string

  is_builtin: boolean

  created_at: string
}

export interface SupportedAIProvider {
  id: string
  label: string
  base_url: string
}

export interface AIProvidersResponse {
  count: number
  next: string | null
  previous: string | null
  results: AIProvider[]
  supported_ai_providers: SupportedAIProvider[]
}

export const useAIProviderStore = defineStore('aiProvider', {
  state: () => ({
    AIProviders: [] as AIProvider[],
    supportedAIProviders: [] as SupportedAIProvider[],
  }),

  actions: {
    async load() {
      const { httpGet } = useHttpClient()
      const response = await httpGet<AIProvidersResponse>(`/ai-providers/`)
      this.AIProviders = response.results
      this.supportedAIProviders = response.supported_ai_providers
      return response
    },

    async create(values: Record<string, unknown>) {
        const { httpPost } = useHttpClient()
        const response = await httpPost<AIProvider>('/ai-providers/', {
          name: values.name,
          provider_api_key: values.provider_api_key,
          base_url: values.base_url,
          provider: values.provider,
        })
        this.AIProviders = [...this.AIProviders, response]
        return response
    },

    async update(values: Record<string, unknown>) {
      const { httpPatch } = useHttpClient()

      const body: Record<string, unknown> = {
        name: values.name,
        base_url: values.base_url,
        model_name: values.model_name,
      }

      if (values.provider_api_key) {
        body.provider_api_key = values.provider_api_key
      }

      const response = await httpPatch<AIProvider>(`/ai-providers/${values.uuid}/`, body)

      const index = this.AIProviders.findIndex(p => p.uuid === values.uuid)
      if (index !== -1 && response?.name) {
        this.AIProviders[index] = { ...this.AIProviders[index], ...response }
      }

      return response
    },

    async delete(uuid: string) {
      const { httpDelete } = useHttpClient()

      const response = await httpDelete<{detail: string}>(`/ai-providers/${uuid}/`)

      if (response?.detail === 'Deleted') {
        this.AIProviders = this.AIProviders.filter((p) => p.uuid !== uuid)
      }

      return response
    },
  },
})
