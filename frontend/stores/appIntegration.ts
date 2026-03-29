import { defineStore } from 'pinia'
import { useHttpClient } from '@/composables/useHttpClient'
import type { PaginatedResponse } from '~/lib/types'
import type { Integration } from './integration'

export interface AppIntegration {
  uuid: string
  integration: Integration
  integration_type: string
  metadata?: Record<string, unknown> | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export const useAppIntegrationStore = defineStore('appIntegration', {
  state: () => ({
    appIntegrations: [] as AppIntegration[],
  }),

  actions: {
    async load(applicationUuid: string) {
      const { httpGet } = useHttpClient()
      const response = await httpGet<PaginatedResponse<AppIntegration>>(
        `/applications/${applicationUuid}/integrations/`,
      )
      this.appIntegrations = response.results
      return response
    },

    async create(applicationUuid: string, values: Record<string, unknown>) {
      const { httpPost } = useHttpClient()
      const response = await httpPost<AppIntegration>(
        `/applications/${applicationUuid}/integrations/`,
        values,
      )
      const index = this.appIntegrations.findIndex(
        i => i.integration_type === values.integration_type,
      )
      if (index !== -1) {
        this.appIntegrations[index] = response
      }
      else {
        this.appIntegrations = [...this.appIntegrations, response]
      }
      return response
    },

    async delete(applicationUuid: string, uuid: string) {
      const { httpDelete } = useHttpClient()
      const response = await httpDelete<{ detail: string }>(
        `/applications/${applicationUuid}/integrations/${uuid}/`,
      )
      if (response?.detail === 'deleted') {
        this.appIntegrations = this.appIntegrations.filter(i => i.uuid !== uuid)
      }
      return response
    },
  },
})
