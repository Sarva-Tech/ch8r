import { defineStore } from 'pinia'
import { useHttpClient } from '@/composables/useHttpClient'
import type { PaginatedResponse } from '~/lib/types'
import type { AIProvider } from './aiProvider'

export interface AppAIProvider {
  id: number
  uuid: string
  ai_provider: AIProvider
  context: string
  capability: string
  priority: number
  external_model_id: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AppAIProviderGroupedResponse {
  [providerId: string]: AppAIProvider[]
}

export const useAppAIProviderStore = defineStore('appAIProvider', {
  state: () => ({
    loading: false,
    error: null as string | null,
    existingAppAIProviderConfigs: [] as AppAIProvider[]
  }),

  actions: {
    async fetchAppAIProviderConfigs(applicationUuid: string) {
      this.loading = true
      this.error = null

      try {
        const { httpGet } = useHttpClient()
        const response = await httpGet<PaginatedResponse<AppAIProvider>>(
          `/applications/${applicationUuid}/ai-providers/`,
        )
        this.existingAppAIProviderConfigs = response.results
        return response.results
      }
      catch (err) {
        this.error = err instanceof Error ? err.message : 'Failed to fetch app AI provider configs'
        throw err
      }
      finally {
        this.loading = false
      }
    },

    async addAppModel(applicationUuid: string, aiProviderId: number, modelName: string, context: string = 'response', capability: string = 'text') {
      const { httpPost } = useHttpClient()

      let finalModelName = modelName
      if (modelName.startsWith('model/')) {
        finalModelName = modelName.substring(6)
      }

      return httpPost(`/applications/${applicationUuid}/ai-providers/`, {
        ai_provider_id: aiProviderId,
        context,
        capability,
        external_model_id: finalModelName,
      })
    },

    clearData() {
      this.error = null
    },
  },
})
