import { defineStore } from 'pinia'
import { useHttpClient } from '@/composables/useHttpClient'
import { useApplicationsStore  } from '~/stores/applications'
import type {Application} from '~/stores/applications';
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { z } from 'zod'
import { applyBackendErrors } from '~/lib/utils'

export interface APIKeyItem {
  id: number
  name: string
  created: string
  permissions: string[]
  api_key: string
}

const apiKeySchema = z.object({
  name: z.string().nonempty({ message: 'required' }),
  permissions: z.array(z.string()).min(1, { message: 'At least one permission is required' }),
})


export type APIKeyFormValues = z.infer<typeof apiKeySchema>
const typedApiKeySchema = toTypedSchema(apiKeySchema)

export const useAPIKeyStore = defineStore('apiKey', {
  state: () => ({
    appDetails: null as Application | null,
    loading: false,
    apiKeys: [] as APIKeyItem[],
    newAPIKey: null as APIKeyItem | null
  }),

  actions: {
    initForm() {
      if (!this.form) {
        this.form = useForm<APIKeyFormValues>({
          validationSchema: typedApiKeySchema,
          initialValues: {
            name: '',
            permissions: [],
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
      const appStore = useApplicationsStore()
      const app = appStore.selectedApplication
      if (!app) return

      const { httpGet } = useHttpClient()
      const response = await httpGet<APIKeyItem[]>(
        `/applications/${app.uuid}/api-keys/`
      )
      this.appDetails = app
      this.apiKeys = response
    },

    async create(values: { name: string, permissions: string[] }) {
      const appStore = useApplicationsStore()
      const app = appStore.selectedApplication
      if (!app) return null

      const { httpPost } = useHttpClient()
      const response = await httpPost<APIKeyItem>(
        `/applications/${app.uuid}/api-keys/`, values
      )
      this.apiKeys.push(response)
      return response
    },
    async delete(id: number) {
      const appStore = useApplicationsStore()
      const app = appStore.selectedApplication
      if (!app) return

      const { httpDelete } = useHttpClient()
      await httpDelete(`/applications/${app.uuid}/api-keys/${id}/`)
      this.apiKeys = this.apiKeys.filter((key) => key.id !== id)
    },
  },
})
