import { defineStore } from 'pinia'
import { useHttpClient } from '~/composables/useHttpClient'
import { useKBDraftStore } from '~/stores/kbDraft'

export interface KnowledgeBaseItem {
  id: number
  uuid: string
  application_id: number
  path: string
  metadata: {
    content: string
    filename: string
    [key: string]: unknown
  }
  source_type: string
  status: string
}

export interface Application {
  id: number
  uuid: string
  name: string
  owner_id: number
  knowledge_base: KnowledgeBaseItem[]
}

export const useApplicationsStore = defineStore('applications', {
  state: () => ({
    applications: [] as Application[],
    selectedApplication: null as Application | null,
  }),

  actions: {
    async fetchApplications() {
      const { httpGet } = useHttpClient()
      this.applications = await httpGet<Application[]>('/applications/')

      if (!this.selectedApplication && this.applications.length > 0) {
        this.selectedApplication = this.applications[0]
      }
    },

    async createApplicationWithKB(values: { name: string }) {
      const kbDraft = useKBDraftStore()
      const kbItems = kbDraft.items

      const formData = new FormData()
      formData.append('name', values.name.trim())

      kbItems.forEach((item, index) => {
        formData.append(`items[${index}].type`, item.type)
        if (item.type === 'file') {
          formData.append(`items[${index}].file`, item.value)
        } else {
          formData.append(`items[${index}].value`, item.value)
        }
      })

      const { httpPost } = useHttpClient()
      const response = await httpPost<Application>('/applications/', formData)

      this.applications.push(response)
      this.selectedApplication = response

      return response
    },

    selectApplication(app: Application) {
      this.selectedApplication = app
    },
  },
})
