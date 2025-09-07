import { defineStore } from 'pinia'
import { useHttpClient } from '~/composables/useHttpClient'
import type { LLMModel } from '~/stores/model'
import type { IntegrationTools, SupportedIntegrationsResponse, SupportedProviders } from '~/stores/integration'

export interface AvailableConfig {
  llm_models: LLMModel[]
  integrations: Integration[]
  supported_integrations: string[]
  supported_providers: SupportedProviders;
  integration_tools: {
    [key: string]: IntegrationTools;
  };
}

export interface AppConfig {
  llm_models: LLMModel[]
  integrations: Integration[]
}

export const useAppConfigurationStore = defineStore('appConfiguration', {
  state: () => ({
    textModels: [] as LLMModel[] | [],
    embeddingModels: [] as LLMModel[] | [],
    selectedTextModel: null as LLMModel | null,
    selectedEmbeddingModel: null as LLMModel | null,

    PMSProfiles: [] as Integration[] | [],
    selectedPMS: null as Integration | null,
    configuredPMS: null as Integration | null,

    supportedIntegrations: {} as SupportedIntegrationsResponse,
  }),

  actions: {
    async initialize() {
      const appStore = useApplicationsStore()
      const app = appStore.selectedApplication
      if (!app) return

      const { httpGet } = useHttpClient()
      const availableConfig = await httpGet<AvailableConfig>(
        'available-configurations/',
      )
      const appConfig = await httpGet<AppConfig>(
        `applications/${app.uuid}/load-app-configurations/`,
      )

      this.textModels = availableConfig.llm_models.filter(
        (model) => model.model_type === 'text',
      )
      this.selectedTextModel =
        appConfig.llm_models?.find((model) => model.model_type === 'text') ||
        null

      this.embeddingModels = availableConfig.llm_models.filter(
        (model) => model.model_type === 'embedding',
      )
      this.selectedEmbeddingModel =
        appConfig.llm_models?.find(
          (model) => model.model_type === 'embedding',
        ) || null

      this.PMSProfiles = availableConfig.integrations.filter((integration) => integration.type === 'pms')
      this.selectedPMS =
        appConfig.integrations?.find(
          (integration) => integration.type === 'pms',
        ) || null
      this.configuredPMS = this.selectedPMS

      this.supportedIntegrations = {
        supported_integrations: availableConfig.supported_integrations,
        integration_tools: availableConfig.integration_tools,
        supported_providers: availableConfig.supported_providers
      }
    },

    async saveModels() {
      const appStore = useApplicationsStore()
      const app = appStore.selectedApplication
      if (!app) return

      const { httpPost } = useHttpClient()
      return await httpPost<AppConfig>(
        `applications/${app.uuid}/configure-app-models/`,
        {
          models: [
            {
              model_type: 'text',
              llm_model: this.selectedTextModel?.uuid,
            },
            {
              model_type: 'embedding',
              llm_model: this.selectedEmbeddingModel?.uuid,
            },
          ],
        },
      )
    },
  },
})
