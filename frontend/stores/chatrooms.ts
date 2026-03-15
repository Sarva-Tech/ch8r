import { defineStore } from 'pinia'
import { useHttpClient } from '~/composables/useHttpClient'
import type { Message } from '~/stores/chatroomMessages'

export interface ChatroomPreview {
  uuid: string
  name: string
  last_message?: Message | null
  has_unread: boolean
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

    markUnread(chatroomId: string) {
      const chatroom = this.chatrooms.find(c => c.uuid === chatroomId)
      if (chatroom) chatroom.has_unread = true
    },

    markRead(chatroomId: string) {
      const chatroom = this.chatrooms.find(c => c.uuid === chatroomId)
      if (chatroom) chatroom.has_unread = false
    },

    updateLastMessage(chatroomId: string, message: Message) {
      const chatroom = this.chatrooms.find(c => c.uuid === chatroomId)
      if (chatroom) chatroom.last_message = message
    },
  },
})
