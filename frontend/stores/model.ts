import { defineStore } from 'pinia'
import { useHttpClient } from '@/composables/useHttpClient'

export type LLMModelType = 'text' | 'embedding' | 'image' | 'rerank' | 'other'

export interface LLMModel {
  id: number
  uuid: string

  owner: number

  name: string
  api_key?: string | null
  base_url?: string | null
  model_name: string

  model_type: LLMModelType
  is_default: boolean

  created_at: string
}

export const useModelStore = defineStore('model', {
  state: () => ({
    models: [] as LLMModel[],
  }),

  actions: {
    async load() {
      const { httpGet } = useHttpClient()
      const response = await httpGet<LLMModel[]>(`/models/`)
      this.models = response
      return response
    },

    async create(values: Record<string, unknown>) {
        const { httpPost } = useHttpClient()
        const response = await httpPost<LLMModel>('/models/', {
          name: values.name,
          api_key: values.api_key,
          base_url: values.base_url,
          model_name: values.model_name,
          model_type: values.model_type,
        })
        this.models = [...this.models, response]
        return response
    },

    async update(values: Record<string, unknown>) {
      const { httpPatch } = useHttpClient()

      const body: Record<string, unknown> = {
        name: values.name,
        base_url: values.base_url,
        model_name: values.model_name,
      }

      if (values.api_key) {
        body.api_key = values.api_key
      }

      const response = await httpPatch<LLMModel>(`/models/${values.uuid}/`, body)

      const index = this.models.findIndex(m => m.uuid === values.uuid)
      if (index !== -1 && response?.name) {
        this.models[index] = { ...this.models[index], ...response }
      }

      return response
    },

    async delete(uuid: string) {
      const { httpDelete } = useHttpClient()

      const response = await httpDelete<{detail: string}>(`/models/${uuid}/`)

      if (response?.detail === 'Deleted') {
        this.models = this.models.filter((m) => m.uuid !== uuid)
      }

      return response
    },
  },
})
