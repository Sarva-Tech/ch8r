import { defineStore } from 'pinia'
import { useUserStore} from '@/stores/user'

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

      const userStore = useUserStore()
      const token = userStore.getToken
      if (!token.value) {
        this.error = 'No auth token'
        this.loading = false
        return
      }

      try {
        const data = await $fetch<ChatroomsResponse>(
          `http://localhost:8000/api/applications/${appUuid}/chatrooms/`,
          {
            method: 'GET',
            headers: {
              Authorization: `Token ${token.value}`,
            },
          }
        )
        this.chatrooms = data.chatrooms || []
      } catch (err) {
        console.error('Failed to fetch chatrooms:', err)
        this.error = 'Failed to load chatrooms'
      } finally {
        this.loading = false
      }
    },
  },
})
