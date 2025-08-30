import { defineStore } from 'pinia'
import { useHttpClient } from '@/composables/useHttpClient'
import type { LLMModel, LLMModelType } from '~/stores/model'


export const useAppModelStore = defineStore('appModel', {
  state: () => ({
    textModel: null as LLMModel | null,
    embeddingModel: null as LLMModel | null
  }),

  actions: {
    async setModel(llmModelUUID: string, modelType: LLMModelType) {
      const appStore = useApplicationsStore()
      const app = appStore.selectedApplication
      if (!app) return

      const { httpPost } = useHttpClient()
        const response = await httpPost<LLMModel>(`applications/${app.uuid}/configure-model/`, {
          llm_model: llmModelUUID,
          model_type: modelType
        })
        if (modelType === 'text') {
          this.textModel = response
        }
        if (modelType === 'embedding') {
          this.embeddingModel = response
        }
        return response
    },
  },
})
