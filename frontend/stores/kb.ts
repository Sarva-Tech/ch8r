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

        if (item.type === 'url' && item.crawling_config) {
          formData.append(`items[${index}].crawling_config.enable_crawling`, item.crawling_config.enable_crawling.toString())
          formData.append(`items[${index}].crawling_config.max_depth`, '1')
          formData.append(`items[${index}].crawling_config.max_pages`, '50')
        }
      })

      const { httpPostForm } = useHttpClient()
      const response = await httpPostForm<{ kbs: KnowledgeBaseItem[] }>(`/applications/${app.uuid}/knowledge-bases/`, formData)
      if (response?.kbs) {
        this.kbs.push(...response.kbs)
      }
      return response
    },

    updateStatus(uuid: string, status: StatusType) {
      const kb = this.kbs.find(item => item.uuid === uuid)
      if (!kb) return

      kb.status = status
    },

    async update(id: string, content: string) {
      const appStore = useApplicationsStore()
      const app = appStore.selectedApplication
      if (!app) return

      this.loading = true

      try {
        const { httpPatch } = useHttpClient()
        const response = await httpPatch(
          `/applications/${app.uuid}/knowledge-bases/${id}/`, { content }
        )
        const updatedKB = this.kbs.find(kb => kb.uuid === id)
        if (updatedKB) {
          Object.assign(updatedKB, response)
        }
      }
      catch (err: unknown) {
        console.error('Delete error:', err)
      } finally {
        this.loading = false
      }
    },

    async delete(id: string) {
      const appStore = useApplicationsStore()
      const app = appStore.selectedApplication
      if (!app) return

      this.loading = true

      try {
        const { httpDelete } = useHttpClient()
        await httpDelete(
          `/applications/${app.uuid}/knowledge-bases/${id}/`,
        )
        this.kbs = this.kbs.filter((kb) => kb.uuid !== id)
      }
      catch (err: unknown) {
        console.error('Delete error:', err)
      } finally {
        this.loading = false
      }
    },
  },
})
