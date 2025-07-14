import { defineStore } from 'pinia'
import { $fetch } from 'ofetch'
import { useUserStore } from '~/stores/user'

export interface KnowledgeBaseItem {
  id: number;
  uuid: string;
  application_id: number;
  path: string;
  metadata: Record<string, unknown> | null;
}

export type Application = {
  id: number
  uuid: string
  name: string
  owner_id: number
  owner: User
  knowledge_base: KnowledgeBaseItem[]
} | undefined

export const useApplicationsStore = defineStore('applications', {
  state: () => ({
    applications: [] as Application[],
    selectedApplication: null as Application | null,
    error: null as string | null,
    loading: false,
  }),

  actions: {
    async fetchApplications() {
      const config = useRuntimeConfig()
      this.loading = true
      this.error = null

      const userStore = useUserStore()
      const token = userStore.getToken
      if (!token.value) {
        this.error = 'No auth token found'
        this.loading = false
        return
      }

      try {
        this.applications = await $fetch<Application[]>(
          `${config.public.apiBaseUrl}/applications/`,
          {
            method: 'GET',
            headers: {
              Authorization: `Token ${token.value}`,
              'Content-Type': 'application/json',
            },
          },
        )

        if (!this.selectedApplication && this.applications.length > 0) {
          this.selectedApplication = this.applications[0]
        }
      } catch (err) {
        console.error('Fetch error:', err)
        this.error = 'Failed to load applications'
      } finally {
        this.loading = false
      }
    },

    async createApplication(name: string) {
      const config = useRuntimeConfig()
      const userStore = useUserStore()
      const token = userStore.getToken

      if (!token.value) {
        this.error = 'No auth token found'
        return
      }

      this.loading = true
      this.error = null

      try {
        const newApp = await $fetch<Application>(
          `${config.public.apiBaseUrl}/applications/`,
          {
            method: 'POST',
            headers: {
              Authorization: `Token ${token.value}`,
              'Content-Type': 'application/json',
            },
            body: {
              name,
            },
          }
        )

        this.applications.push(newApp)

        if (!this.selectedApplication) {
          this.selectedApplication = newApp
        }
      } catch (err) {
        console.error('Create error:', err)
        this.error = 'Failed to create application'
      } finally {
        this.loading = false
      }
    },

    selectApplication(app: Application) {
      this.selectedApplication = app
    },
  },
})
