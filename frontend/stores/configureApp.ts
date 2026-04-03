import { defineStore } from 'pinia'
import { useHttpClient } from '~/composables/useHttpClient'
import type { LLMModel } from '~/stores/model'
import type { IntegrationTools, SupportedIntegrationsResponse, SupportedProviders } from '~/stores/integration'
import type { SelectOption } from '~/lib/types'

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
  notification_profiles: NotificationProfile[]
}

export interface PromptConfig {
  tone: 'professional' | 'friendly' | 'formal' | 'casual'
  response_style: 'balanced' | 'concise' | 'detailed' | 'step_by_step'
  custom_instructions: string
  role: string
  behavior: string
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

    notifications: [] as NotificationProfile[] | [],
    promptConfig: {
      tone: 'professional',
      response_style: 'balanced',
      custom_instructions: '',
      role: 'customer service assistant',
      behavior: 'answer user questions politely and competently',
    } as PromptConfig,
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

      this.notifications = appConfig.notification_profiles

      await this.loadPromptConfig()
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

    async loadPromptConfig(): Promise<void> {
      const appStore = useApplicationsStore()
      const app = appStore.selectedApplication
      if (!app) return
      const { httpGet } = useHttpClient()
      const config = await httpGet<PromptConfig>(`applications/${app.uuid}/prompt-config/`)
      this.promptConfig = config
    },

    async savePromptConfig(config: PromptConfig): Promise<void> {
      const appStore = useApplicationsStore()
      const app = appStore.selectedApplication
      if (!app) return
      const { httpPatch } = useHttpClient()
      const updated = await httpPatch<PromptConfig>(`applications/${app.uuid}/prompt-config/`, config)
      if (updated) {
        this.promptConfig = updated
      }
    },

    async saveNotifications(profiles: SelectOption[]) {
      const appStore = useApplicationsStore()
      const app = appStore.selectedApplication
      if (!app) return

      const { httpPatch } = useHttpClient()
      const response = await httpPatch<AppConfig>(
        `applications/${app.uuid}/app-notification-update/`,
        {
          profile_uuids: profiles.map((profile) => profile.value)
        },
      )
      if (response?.notification_profiles) {
        this.notifications = response.notification_profiles
      }

      return response
    },
  },
})
