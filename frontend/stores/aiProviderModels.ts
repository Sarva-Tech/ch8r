import { defineStore } from 'pinia'
import { useHttpClient } from '@/composables/useHttpClient'
import type { AIProvider } from './aiProvider'

export interface AIProviderModels {
  id: number
  models_data: Array<Record<string, string>>
  created_at: string
  updated_at: string
}

export interface AIProviderWithModels {
  ai_provider: AIProvider
  ai_provider_models: AIProviderModels
}

export interface AIProviderModelsResponse {
  providers: AIProviderWithModels[]
}

export const useAIProviderModelsStore = defineStore('aiProviderModels', {
  state: () => ({
    providerModels: [] as AIProviderWithModels[],
  }),

  actions: {
    async load() {
      const { httpGet } = useHttpClient()
      const response = await httpGet<AIProviderModelsResponse>(`/ai-providers/all_models/`)
      this.providerModels = response.providers || []
      return response
    },
  },
})
