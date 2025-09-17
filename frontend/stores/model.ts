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
  },
})
