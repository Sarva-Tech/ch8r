import { defineStore } from 'pinia'
import { useHttpClient } from '@/composables/useHttpClient'

export interface WidgetResponse {
  token: string;
  widget_url: string;
  status?: string;
}

export const useWidgetStore = defineStore('widget', {
  state: () => ({
    widget: null as WidgetResponse | null
  }),

  actions: {
    async load() {
      const appStore = useApplicationsStore()
      const app = appStore.selectedApplication
      if (!app) return

      const { httpGet } = useHttpClient()
      const response = await httpGet<WidgetResponse>(`applications/${app.uuid}/widget/`)
      this.widget = response
      return response
    },

    async enable() {
      const appStore = useApplicationsStore()
      const app = appStore.selectedApplication
      if (!app) return

      const { httpPost } = useHttpClient()
      const response = await httpPost<WidgetResponse>(
        `applications/${app.uuid}/widget/`,
        {},
      )
      this.widget = response
      return response
    },
  },
})
