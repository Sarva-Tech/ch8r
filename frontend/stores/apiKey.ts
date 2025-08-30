import { defineStore } from 'pinia'
import { useHttpClient } from '@/composables/useHttpClient'
import type {Application} from "~/stores/applications";

export interface APIKeyItem {
  id: number,
  name: string,
  created: string,
  permissions: string[],
  api_key: string
}
export const useAPIKeyStore = defineStore('apiKey', {
  state: () => ({
    appDetails: null as Application | null,
    loading: false,
    apiKeys: [] as APIKeyItem[]
  }),

  actions: {
    async load() {
      const appStore = useApplicationsStore()
      const app = appStore.selectedApplication
      if (!app) return

      this.loading = true

      try {
        const { httpGet } = useHttpClient()
        const response = await httpGet<{apiKeyItem: APIKeyItem[]}>(
          `/applications/${app.uuid}/api-keys/`
        )
        this.appDetails = appStore.selectedApplication
        this.apiKeys = response
      } catch (err: unknown) {
        console.error('Fetch error:', err)
      } finally {
        this.loading = false
      }
    },

    async create(content: object) {
      const appStore = useApplicationsStore()
      const app = appStore.selectedApplication
      let apiKey
      if (!app) return

      this.loading = true

      try {
        const { httpPost } = useHttpClient()
        const response = await httpPost<APIKeyItem>(
          `/applications/${app.uuid}/api-keys/`, content
        )
        this.apiKeys.push(response)
        apiKey = response.api_key
      }
      catch (err: unknown) {
        console.error('Create error:', err)
      } finally {
        this.loading = false
      }
      return apiKey
    },

    async delete(id: number) {
      const appStore = useApplicationsStore()
      const app = appStore.selectedApplication
      if (!app) return

      this.loading = true

      try {
        const { httpDelete } = useHttpClient()
        await httpDelete(
          `/applications/${app.uuid}/api-keys/${id}/`,
        )
        this.apiKeys = this.apiKeys.filter((key) => key.id !== id)
      }
      catch (err: unknown) {
        console.error('Delete error:', err)
      } finally {
        this.loading = false
      }
    },
  },
})
