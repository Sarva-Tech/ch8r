import { defineStore } from 'pinia'
import { useHttpClient } from '~/composables/useHttpClient'
import { useKBDraftStore } from '~/stores/kbDraft'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { z } from 'zod'
import { applyBackendErrors } from '~/lib/utils'

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
  llm_models: any[]
}

const schema = z.object({
  name: z.string().nonempty({ message: 'Required' }).min(1).max(255),
})
export type FormValues = z.infer<typeof schema>
const typedSchema = toTypedSchema(schema)

export const useApplicationsStore = defineStore('applications', {
  state: () => ({
    applications: [] as Application[],
    selectedApplication: null as Application | null,
    selectedTextModel: null as any | null,
    selectedEmbeddingModel: null as any | null,
    form: shallowRef<ReturnType<typeof useForm<FormValues>> | null>(null),
  }),

  actions: {
    initForm() {
      if (!this.form) {
        this.form = useForm<FormValues>({
          validationSchema: typedSchema,
          initialValues: { name: '' },
        })
      }
      return this.form
    },

    getFormInstance() {
      return this.initForm()
    },

    setBackendErrors(errors: Record<string, string[] | string>) {
      const formInstance = this.getFormInstance()
      if (!formInstance) return
      applyBackendErrors(formInstance, errors)
    },

    async fetchApplications() {
      const { httpGet } = useHttpClient()
      this.applications = await httpGet<Application[]>('/applications/')

      if (!this.selectedApplication && this.applications.length > 0) {
        this.selectedApplication = this.applications[0]
        const models = this.selectedApplication.llm_models || []
        this.selectedTextModel =
          models.find((m: any) => m.model_type === 'text') || null
        this.selectedEmbeddingModel =
          models.find((m: any) => m.model_type === 'embedding') || null
      }
    },

    async createApplicationWithKB(values: FormValues) {
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
