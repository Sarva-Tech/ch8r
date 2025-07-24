import { defineStore } from 'pinia'
import { useUserStore } from '@/stores/user'
import { useHttpClient } from '~/composables/useHttpClient'
import { DUMMY_NEW_CHATROOM, NEW_CHAT } from '~/lib/consts'

interface Message {
  id: number
  uuid: string
  sender_identifier: string
  message: string
  metadata: Record<string, unknown>
  created_at: string
}

interface ChatRoomMessagesResponse {
  uuid: string
  name: string
  application: Application
  messages: Message[]
}

export const useChatroomMessagesStore = defineStore('chatroom', {
  state: () => ({
    selectedChatroom: null as ChatroomPreview | null,
    messages: [] as Message[],
    loading: false,
    error: null as string | null,
  }),

  actions: {
    async selectChatroom(applicationUuid: string, chatroomUuid: string) {
      this.loading = true
      this.error = null

      if (chatroomUuid === NEW_CHAT) {
        this.selectedChatroom = DUMMY_NEW_CHATROOM
        this.messages = []
        this.loading = false
        return
      }

      const { httpGet } = useHttpClient()
      try {
        const data = await httpGet<ChatRoomMessagesResponse>(
          `/applications/${applicationUuid}/chatrooms/${chatroomUuid}/messages/`
        )
        this.selectedChatroom = {
          uuid: data.uuid,
          name: data.name
        }
        this.messages = data.messages
      } catch (err: any) {
        this.error = err.message || 'Failed to load chatroom'
      } finally {
        this.loading = false
      }
    },

    async sendMessage(applicationUuid: string, messageText: string) {
      const userStore = useUserStore()
      const sender = userStore.userIdentifier

      if (!this.selectedChatroom) {
        throw new Error('No chatroom selected')
      }

      const dummyMessage: Message = {
        id: this.messages.length + 1,
        uuid: `${Date.now()}`,
        sender_identifier: sender,
        message: messageText,
        metadata: {},
        created_at: new Date().toISOString()
      }

      this.addMessage(dummyMessage)

      try {
        const { httpPost } = useHttpClient()

        const body = {
          chatroom_identifier: this.selectedChatroom.uuid,
          message: messageText,
          sender_identifier: sender,
          metadata: {
            source: 'web'
          }
        }

        return await httpPost<Message>(
          `/applications/${applicationUuid}/chatrooms/send-message/`,
          body
        )
      } catch (err: any) {
        console.error('Failed to send message:', err)
        this.error = err.message || 'Failed to send message'
        throw err
      }
    },

    addMessage(newMessage: Message) {
      this.messages.push(newMessage)
    },
  },
})
