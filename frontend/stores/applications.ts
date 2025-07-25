import { defineStore } from 'pinia'
import { useHttpClient } from '~/composables/useHttpClient'
import type { SOURCE_TYPE, StatusType } from '~/lib/consts'

export interface KnowledgeBaseItem {
  id: number;
  uuid: string;
  application_id: number;
  path: string;
  metadata: {
    content: string
    filename: string
    [key: string]: unknown
  }
  source_type: SOURCE_TYPE
  status: StatusType
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
      const { httpGet } = useHttpClient()

      this.loading = true
      this.error = null

      try {
        this.applications = await httpGet<Application[]>('/applications/')

        if (!this.selectedApplication && this.applications.length > 0) {
          this.selectedApplication = this.applications[0]
        }
      } catch (err: any) {
        console.error('Fetch error:', err)
        this.error = err?.message || 'Failed to load applications'
      } finally {
        this.loading = false
      }
    },

    async createApplication(name: string): Promise<Application | null> {
      const { httpPost } = useHttpClient()
      this.loading = true
      this.error = null

      try {
        const newApp = await httpPost<Application>('/applications/', { name })
        this.applications.push(newApp)
        return newApp
      } catch (err: any) {
        console.error('Create error:', err)
        this.error = err?.message || 'Failed to create application'
        return null
      } finally {
        this.loading = false
      }
    },

    selectApplication(app: Application) {
      this.selectedApplication = app
    },
  },
})
