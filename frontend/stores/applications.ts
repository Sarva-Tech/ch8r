import { defineStore } from 'pinia'
import { useHttpClient } from '~/composables/useHttpClient'

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

    async createApplicationWithKB(name: string, kbItems: any[]): Promise<Application | null> {
      const { httpPostForm } = useHttpClient()
      this.loading = true
      this.error = null

      try {
        const formData = new FormData()
        formData.append('name', name.trim())

        kbItems.forEach((item, index) => {
          formData.append(`items[${index}].type`, item.type)
          if (item.type === 'file') {
            formData.append(`items[${index}].file`, item.value)
          } else {
            formData.append(`items[${index}].value`, item.value)
          }
        })

        const newApp = await httpPostForm<Application>('/applications/', formData)
        this.applications.push(newApp)
        return newApp
      } catch (err: any) {
        console.error('Create with KB error:', err)
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
