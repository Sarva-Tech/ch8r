import { defineStore } from 'pinia'
import { useHttpClient } from '@/composables/useHttpClient'

export interface WidgetResponse {
  token: string;
  widget_url: string;
  status?: string;
  rate_limit_count?: number;
  rate_limit_period?: number;
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

    async toggle() {
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

    async updateRateLimit(rateLimitCount: number, rateLimitPeriod: number) {
      const appStore = useApplicationsStore()
      const app = appStore.selectedApplication
      if (!app) return

      const { httpPatch } = useHttpClient()
      const response = await httpPatch<WidgetResponse>(
        `applications/${app.uuid}/widget/`,
        {
          rate_limit_count: rateLimitCount,
          rate_limit_period: rateLimitPeriod,
        },
      )
      this.widget = response
      return response
    },
  },
})
