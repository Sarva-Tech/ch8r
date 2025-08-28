import { defineStore } from 'pinia'
import { useHttpClient } from '~/composables/useHttpClient'
import type { SOURCE_TYPE, StatusType } from '~/lib/consts'
import { useKBDraftStore } from '~/stores/kbDraft'

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
  llm_models: LLMModel[]
} | undefined


export const useApplicationsStore = defineStore('applications', {
  state: () => ({
    applications: [] as Application[],
    selectedApplication: null as Application | null,
    selectedTextModel: null as LLMModel | null,
    selectedEmbeddingModel: null as LLMModel | null,
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
          const models = this.selectedApplication.llm_models
          this.selectedTextModel = models.find((model) => model.model_type === 'text')
          this.selectedEmbeddingModel = models.find((model) => model.model_type === 'embedding')
        }
      } catch (err: unknown) {
        console.error('Fetch error:', err)
        this.error = err?.message || 'Failed to load applications'
      } finally {
        this.loading = false
      }
    },

    async createApplicationWithKB(name: string): Promise<Application | null> {
      const { httpPostForm } = useHttpClient()
      this.loading = true
      this.error = null
      const kbDraft = useKBDraftStore()
      const kbItems = kbDraft.items;

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
