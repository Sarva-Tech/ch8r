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
          'http://localhost:8000/api/applications/',
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

    selectApplication(app: Application) {
      this.selectedApplication = app
    },
  },
})
