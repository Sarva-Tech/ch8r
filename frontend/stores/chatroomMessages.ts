import { defineStore } from 'pinia'
import { useFetch } from '#app'
import { useUserStore} from '@/stores/user'

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

// const userStore = useUserStore()

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

      const userStore = useUserStore()
      const token = userStore.getToken

      if (!token.value) {
        this.error = 'No auth token'
        this.loading = false
        return
      }

      try {
        const { data, error } = await useFetch<ChatRoomMessagesResponse>(
          `http://localhost:8000/api/applications/${applicationUuid}/chatrooms/${chatroomUuid}/messages/`,
          {
            method: 'GET',
            headers: {
              Authorization: `Token ${token.value}`,
            },
          }
        )

        if (error.value) throw new Error(error.value.message)

        this.selectedChatroom = data.value!
        this.messages = data.value!.messages
      } catch (err: any) {
        this.error = err.message || 'Failed to load chatroom'
      } finally {
        this.loading = false
      }
    },

    // TODO: we need to update sender_identifier here
    async sendMessage(applicationUuid: string, messageText: string, sender = 'reg_1') {
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

      this.messages.push(dummyMessage)

      const userStore = useUserStore()
      const token = userStore.getToken
      console.log(token)
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

        const { data, error } = await useFetch<Message>(
          `http://localhost:8000/api/applications/${applicationUuid}/chatrooms/send-message/`,
          {
            method: 'POST',
            body,
            headers: {
              Authorization: `Token ${token.value}`,
            },
          }
        )

        if (error.value) throw new Error(error.value.message)

        // Optionally append it to the list immediately
        this.messages.push(data.value!)
      } catch (err: any) {
        console.error('Failed to send message:', err)
        throw err
      }
    },

    addMessage(newMessage: Message) {
      this.messages.push(newMessage)
    },

    clearChatroom() {
      this.selectedChatroom = null
      this.messages = []
    },
  },
})
