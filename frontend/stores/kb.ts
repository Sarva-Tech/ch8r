import { defineStore } from 'pinia'
import { useHttpClient } from '@/composables/useHttpClient'
import type { StatusType } from '~/lib/consts'

export const useKnowledgeBaseStore = defineStore('kb', {
  state: () => ({
    appDetails: null as Application | null,
    loading: false,
    kbs: [] as KnowledgeBaseItem[]
  }),

  actions: {
    async load() {
      const appStore = useApplicationsStore()
      const app = appStore.selectedApplication
      if (!app) return

      this.loading = true

      try {
        const { httpGet } = useHttpClient()
        const response = await httpGet<{ application: Application }>(
          `applications/${app.uuid}/knowledge-bases/`
        )
        this.appDetails = response.application
        this.kbs = this.appDetails?.knowledge_base || []
      } catch (err: unknown) {
        console.error('Fetch error:', err)
      } finally {
        this.loading = false
      }
    },

    async process() {
      const appStore = useApplicationsStore()
      const app = appStore.selectedApplication
      if (!app) return

      const kbDraftStore = useKBDraftStore()
      const kbItems = kbDraftStore.items

      this.loading = true

      const formData = new FormData()
      kbItems.forEach((item, index) => {
        formData.append(`items[${index}].type`, item.type)

        if (item.type === 'file') {
          formData.append(`items[${index}].file`, item.value)
        } else {
          formData.append(`items[${index}].value`, item.value)
        }
      })

      try {
        const { httpPostForm } = useHttpClient()
        const response = await httpPostForm<{ kbs: KnowledgeBaseItem[] }>(`/applications/${app.uuid}/knowledge-bases/`, formData)
        if (response?.kbs) {
          this.kbs.push(...response.kbs)
        }
      } catch (err: unknown) {
        console.error('Error processing knowledge base:', err)
      }
    },

    updateStatus(uuid: string, status: StatusType, content: string) {
      const kb = this.kbs.find(item => item.uuid === uuid)
      if (!kb) return

      kb.status = status

      if (!kb.metadata) {
        kb.metadata = { content: '', filename: '' }
      }
      kb.metadata.content = content
    },

    async updateKb() {
    },

    async deleteKb() {
    },
  },
})
