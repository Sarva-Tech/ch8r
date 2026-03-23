import { defineStore } from 'pinia'
import { useHttpClient } from '@/composables/useHttpClient'
import { useApplicationsStore } from '~/stores/applications'

export interface APIKeyItem {
  id: number
  name: string
  created: string
  permissions: string[]
  api_key: string
  owner: number
}

export const useAPIKeyStore = defineStore('apiKey', {
  state: () => ({
    apiKeys: [] as APIKeyItem[],
    newAPIKey: null as APIKeyItem | null,
  }),

  actions: {
    async load() {
      const appStore = useApplicationsStore()
      const app = appStore.selectedApplication
      if (!app) return

      const { httpGet } = useHttpClient()
      const response = await httpGet<APIKeyItem[]>(
        `/applications/${app.uuid}/api-keys/`
      )
      this.apiKeys = response
      return response
    },

    async create(values: { name: string, permissions: string[] }) {
      const appStore = useApplicationsStore()
      const app = appStore.selectedApplication
      if (!app) return null

      const { httpPost } = useHttpClient()
      const response = await httpPost<APIKeyItem>(
        `/applications/${app.uuid}/api-keys/`, values
      )
      this.apiKeys = [...this.apiKeys, response]
      return response
    },
    async delete(id: number) {
      const appStore = useApplicationsStore()
      const app = appStore.selectedApplication
      if (!app) return

      const { httpDelete } = useHttpClient()
      const response = await httpDelete<{ detail: string }>(`/applications/${app.uuid}/api-keys/${id}/`)
      if (response?.detail === 'deleted') {
        this.apiKeys = this.apiKeys.filter(key => key.id !== id)
      }

      return response
    },
  },
})
