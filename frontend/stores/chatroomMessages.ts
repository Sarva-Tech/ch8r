import { defineStore } from 'pinia'
import { useUserStore} from '@/stores/user'
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
        return
      }

      const userStore = useUserStore()
      const token = userStore.getToken

      if (!token.value) {
        this.error = 'No auth token'
        this.loading = false
        return
      }

      try {
        const data = await $fetch<ChatRoomMessagesResponse>(
          `http://localhost:8000/api/applications/${applicationUuid}/chatrooms/${chatroomUuid}/messages/`,
          {
            method: 'GET',
            headers: {
              Authorization: `Token ${token.value}`,
            },
          }
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
      const user = userStore.getUser
      const sender = `reg_${user.id}`

      if (!this.selectedChatroom) {
        throw new Error('No chatroom selected')
      }

      const dummyMessage: Message = {
        id: this.messages.length + 1,
        uuid: `${Date.now()}`,
        sender_identifier: sender,
        message: messageText,
        metadata: {},
        created_at: `${Date.now()}`
      }

      this.addMessage(dummyMessage)

      const token = userStore.getToken
      if (!token.value) {
        this.error = 'No auth token'
        this.loading = false
        return
      }

      try {
        const body = {
          chatroom_identifier: this.selectedChatroom.uuid,
          message: messageText,
          sender_identifier: sender,
          metadata: {
            source: 'web'
          }
        }

        return $fetch<Message>(
          `http://localhost:8000/api/applications/${applicationUuid}/chatrooms/send-message/`,
          {
            method: 'POST',
            body,
            headers: {
              Authorization: `Token ${token.value}`,
            },
          }
        )
      } catch (err: any) {
        console.error('Failed to send message:', err)
        throw err
      }
    },

    addMessage(newMessage: Message) {
      this.messages.push(newMessage)
    },
  },
})
