import { defineStore } from 'pinia'
import { useHttpClient } from '@/composables/useHttpClient'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { z } from 'zod'
import { applyBackendErrors } from '~/lib/utils'

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


const schema = z.object({
  name: z.string().nonempty({ message: 'Required' }).min(1).max(255),
  type: z.string().nonempty({ message: 'Required' }).min(1).max(255),
  provider: z
    .string()
    .nonempty({ message: 'Required' })
    .min(1)
    .max(255),
  token: z.string().optional()
}).refine(
  (data) =>
    !(data.provider === "github") || !!data.token,
  {
    message: "Token is required for GitHub integrations",
    path: ["token"],
  }
);


type FormValues = z.infer<typeof schema>
const typedSchema = toTypedSchema(schema)

export const useIntegrationStore = defineStore('integration', {
  state: () => ({
    form: shallowRef<ReturnType<typeof useForm<FormValues>> | null>(null),
    supportedIntegrations: {} as SupportedIntegrationsResponse,
    integrations: [] as Integration[],
  }),

  actions: {
    initForm() {
      if (!this.form) {
        this.form = useForm<FormValues>({
          validationSchema: typedSchema,
          initialValues: {
            name: '',
            type: '',
            provider: '',
            token: ''
          },
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

    async create() {
      if (!this.form) return

      const { handleSubmit } = this.form

      return handleSubmit(async (values: FormValues) => {
        const { httpPost } = useHttpClient()
        const response = await httpPost<Integration>('/integrations/', {
          name: values.name,
          type: values.type,
          provider: values.provider,
          token: values.token
        })
        this.integrations = [...this.integrations, response]
        return response
      })()
    },
  },
})
