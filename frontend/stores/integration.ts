import { defineStore } from 'pinia'
import { useHttpClient } from '@/composables/useHttpClient'

export type IntegrationType = "pms" | "crm" | "custom";

export interface Integration {
  id: number;
  uuid: string;
  name: string;
  type: IntegrationType;
  provider: string;
  owner: number;
  metadata?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export type FunctionParameter = {
  type: string;
  description: string;
};

export type FunctionParameters = {
  type: "object";
  properties: Record<string, FunctionParameter>;
  required?: string[];
};

export type IntegrationFunction = {
  name: string;
  description: string;
  parameters: FunctionParameters;
};

export type IntegrationTool = {
  type: string;
  function: IntegrationFunction;
};

export type IntegrationTools = {
  [toolName: string]: IntegrationTool;
};

export type SupportedProviders = {
  [integrationType: string]: string[];
};

export type SupportedIntegrationsResponse = {
  supported_integrations: string[];
  supported_providers: SupportedProviders;
  integration_tools: {
    [key: string]: IntegrationTools;
  };
};

export const useIntegrationStore = defineStore('integration', {
  state: () => ({
    supportedIntegrations: {} as SupportedIntegrationsResponse,
    integrations: [] as Integration[],
  }),

  actions: {
    async load() {
      const { httpGet } = useHttpClient()
      const response = await httpGet<Integration[]>(`/integrations/`)
      this.integrations = response
      return response
    },

    async loadSupportedIntegrations() {
      const { httpGet } = useHttpClient()
      const response = await httpGet<SupportedIntegrationsResponse>(`/supported-integrations/`)
      this.supportedIntegrations = response
      return response
    },

    async create(values: Record<string, unknown>) {
        const { httpPost } = useHttpClient()
        const response = await httpPost<Integration>('/integrations/', {
          name: values.name,
          type: values.type,
          provider: values.provider,
          token: values.token
        })
        this.integrations = [...this.integrations, response]
        return response
    },
  },
})
