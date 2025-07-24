import { defineStore } from 'pinia'
import { useHttpClient } from '~/composables/useHttpClient'

export interface ChatroomPreview {
  uuid: string
  name: string
  last_message?: {
    id: number
    uuid: string
    sender_identifier: string
    message: string
    metadata: Record<string, unknown> | null
    created_at: string
  } | null
}

interface ChatroomsResponse {
  chatrooms: ChatroomPreview[]
}

export const useChatroomStore = defineStore('chatrooms', {
  state: () => ({
    chatrooms: [] as ChatroomPreview[],
    loading: false,
    error: null as string | null,
  }),

  actions: {
    async fetchChatrooms(appUuid: string) {
      this.loading = true
      this.error = null
      const { httpGet } = useHttpClient()

      try {
        const data = await httpGet<ChatroomsResponse>(
          `/applications/${appUuid}/chatrooms/`
        )
        this.chatrooms = data.chatrooms || []
      } catch (err: any) {
        console.error('Failed to fetch chatrooms:', err)
        this.error = err.message || 'Failed to load chatrooms'
      } finally {
        this.loading = false
      }
    },
  },
})
