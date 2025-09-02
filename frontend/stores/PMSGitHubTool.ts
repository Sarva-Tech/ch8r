import { defineStore } from 'pinia'
import { useForm } from 'vee-validate'
import { z } from 'zod'
import { toTypedSchema } from '@vee-validate/zod'
import { applyBackendErrors } from '~/lib/utils'
import { useHttpClient } from '~/composables/useHttpClient'
import type { LLMModel } from '~/stores/model'

const schema = z.object({
  branch_name: z.string().nonempty({ message: 'Required' }).min(1).max(255),
})

type FormValues = z.infer<typeof schema>
const typedSchema = toTypedSchema(schema)

export const usePMSGitHubToolStore = defineStore('PMSGitHubTool', {
  state: () => ({
    form: shallowRef<ReturnType<typeof useForm<FormValues>> | null>(null),
  }),

  actions: {
    initForm() {
      if (!this.form) {
        this.form = useForm<FormValues>({
          validationSchema: typedSchema,
          initialValues: {
            branch_name: '',
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
    async create(integrationUUID: string, integrationType: string) {
      const appStore = useApplicationsStore()
      const app = appStore.selectedApplication
      if (!app) return

      if (!this.form) return

      const { handleSubmit } = this.form

      return handleSubmit(async (values: FormValues) => {
        const { httpPost } = useHttpClient()
        const response = await httpPost<LLMModel>(`applications/${app.uuid}/configure-integration/`, {
          integration: integrationUUID,
          type: integrationType,
          branch_name: values.branch_name,
        })
        return response
      })()
    },
  }
})
