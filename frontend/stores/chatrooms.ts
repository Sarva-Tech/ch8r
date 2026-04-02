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

    addChatroom(chatroom: ChatroomPreview) {
      const exists = this.chatrooms.some(c => c.uuid === chatroom.uuid)
      if (!exists) {
        this.chatrooms.unshift(chatroom)
      }
    },

    async renameChatroom(appUuid: string, chatroomId: string, newName: string) {
      const chatroom = this.chatrooms.find(c => c.uuid === chatroomId)
      if (!chatroom || chatroom.name === newName) {
        return
      }
      const { httpPatch } = useHttpClient()
      try {
        await httpPatch(`/applications/${appUuid}/chatrooms/${chatroomId}/`, {
          name: newName,
        })
        chatroom.name = newName
      } catch (err: any) {
        console.error('Failed to rename chatroom:', err)
        throw err
      }
    },

    async deleteChatroom(appUuid: string, chatroomId: string) {
      const { httpDelete } = useHttpClient()
      try {
        await httpDelete(`/applications/${appUuid}/chatrooms/${chatroomId}/delete/`)
        this.chatrooms = this.chatrooms.filter(c => c.uuid !== chatroomId)
      } catch (err: any) {
        console.error('Failed to delete chatroom:', err)
        throw err
      }
    },
  },
})
