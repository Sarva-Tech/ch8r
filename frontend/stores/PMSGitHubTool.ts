import { defineStore } from 'pinia'
import { useForm } from 'vee-validate'
import { z } from 'zod'
import { toTypedSchema } from '@vee-validate/zod'
import { applyBackendErrors } from '~/lib/utils'
import { useHttpClient } from '~/composables/useHttpClient'


export const usePMSGitHubToolStore = defineStore('PMSGitHubTool', {
  state: () => ({
  }),

  actions: {
    async create(values: { branch_name: string }, integrationType: string, integrationUUID: string) {
      const appStore = useApplicationsStore()
      const app = appStore.selectedApplication
      if (!app) return

      const { httpPost } = useHttpClient()
      return httpPost<Integration>(`applications/${app.uuid}/configure-integration/`, {
        integration: integrationUUID,
        type: integrationType,
        branch_name: values.branch_name,
      })
    },
  }
})
