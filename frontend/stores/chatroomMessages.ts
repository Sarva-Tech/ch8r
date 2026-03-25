import { defineStore } from 'pinia'
import { useUserStore } from '@/stores/user'
import { useHttpClient } from '~/composables/useHttpClient'
import { DUMMY_NEW_CHATROOM, NEW_CHAT } from '~/lib/consts'
import type { AIProvider } from '@/stores/aiProvider'

export interface Message {
  id: number
  uuid: string
  sender_identifier: string
  message: string
  metadata: Record<string, unknown>
  created_at: string
  chatroom_identifier?: string
  ai_provider_id?: number | null
  model?: string | null
  is_internal?: boolean
  platform?: 'dashboard' | 'widget'
  ai_mode?: boolean
}

interface ChatRoomMessagesResponse {
  uuid: string
  name: string
  application: Application
  messages: Message[]
  ai_provider: AIProvider
  ai_model: string | null
}

export const useChatroomMessagesStore = defineStore('chatroom', {
  state: () => ({
    selectedChatroom: null as ChatroomPreview | null,
    messages: [] as Message[],
    loading: false,
    error: null as string | null,
    lastUsedAIProvider: undefined as AIProvider | undefined,
    lastUsedAIModel: null as string | null,
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
          name: data.name,
          has_unread: false,
        }
        this.messages = data.messages
        this.lastUsedAIProvider = data.ai_provider
        this.lastUsedAIModel = data.ai_model
      } catch (err: any) {
        this.error = err.message || 'Failed to load chatroom'
      } finally {
        this.loading = false
      }
    },

    async sendMessage(applicationUuid: string, messageText: string, isInternal = false, aiProvider?: number, model?: string, aiMode?: boolean) {
      const userStore = useUserStore()
      const sender = userStore.userIdentifier

      if (!this.selectedChatroom) {
        throw new Error('No chatroom selected')
      }

      const tempUuid = `${Date.now()}`
      const dummyMessage: Message = {
        id: this.messages.length + 1,
        uuid: tempUuid,
        sender_identifier: sender,
        message: messageText,
        metadata: {},
        created_at: new Date().toISOString(),
        is_internal: isInternal,
        ai_provider_id: aiProvider ?? null,
        model: model ?? null,
        ai_mode: aiMode ?? false,
      }

      this.addMessage(dummyMessage)

      try {
        const { httpPost } = useHttpClient()

        const body: Record<string, unknown> = {
          chatroom_identifier: this.selectedChatroom.uuid,
          message: messageText,
          sender_identifier: sender,
          metadata: { source: 'web' },
          is_internal: isInternal,
          ai_provider: aiProvider,
          model: model,
          ai_mode: aiMode ?? false,
        }

        const response = await httpPost<Message>(
          `/applications/${applicationUuid}/chatrooms/send-message/`,
          body
        )

        const idx = this.messages.findIndex(m => m.uuid === tempUuid)
        if (idx !== -1 && response?.uuid) {
          this.messages[idx] = { ...this.messages[idx], ...response }
        }

        return response
      } catch (err: any) {
        console.error('Failed to send message:', err)
        this.error = err.message || 'Failed to send message'
        throw err
      }
    },

    addMessage(newMessage: Message) {
      const exists = this.messages.some(m => m.uuid === newMessage.uuid)
      if (!exists) {
        this.messages.push(newMessage)
      }
    },
  },
})
