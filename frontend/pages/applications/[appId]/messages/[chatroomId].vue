<template>
  <div class="flex flex-col h-screen">
    <div
      class="overflow-y-auto pt-[72px] pb-[120px] px-6 space-y-6"
      :style="`height: calc(100vh - 64px - 112px);`"
    >
      <div
        v-for="message in messages"
        :key="message.id"
        :class="cn(
            'flex w-fit max-w-[75%] lg:max-w-[60%] xl:max-w-[50%] flex-col gap-2 rounded-lg p-2 text-sm',
            isMessageSentByCurrentUser(message.sender_identifier) ? 'ml-auto bg-primary text-primary-foreground' : 'bg-muted',
          )"
      >
        {{ message.message }}
      </div>
    </div>

    <div
      class="fixed bottom-0 transition-[left] duration-300 ease-in-out px-6 pb-4 bg-background"
      :style="{ left: isMobile ? '0' : sidebarWidth, right: '0' }"
    >
      <div class="w-full space-y-2">
        <Textarea
          v-model="currentMessage"
          placeholder="Message"
          class="max-h-40 overflow-y-auto resize-none"
          @keydown.enter="send"
        />
        <div class="flex justify-end">
          <Button
            class="flex items-center w-20 bg-primary"
            size="default"
            @click="send"
          >
            <span class="text-xs">Send</span>
            <Send class="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { cn } from '@/lib/utils'
import { Textarea } from '@/components/ui/textarea'
import { NEW_CHAT } from '~/lib/consts'
import {
  useSidebar,
} from '@/components/ui/sidebar'
import { SIDEBAR_WIDTH } from '~/components/ui/sidebar/utils'
import { Send } from 'lucide-vue-next'
import { Button } from '~/components/ui/button'
const websocket = ref<WebSocket | null>(null)
const connectedChatroomId = ref<string | null>(null)

const userStore = useUserStore()
const chatroomsStore = useChatroomStore()
const chatroomMessagesStore = useChatroomMessagesStore()
const appStore = useApplicationsStore()

const messages = computed(() => chatroomMessagesStore.messages)
const selectedApp = computed(() => appStore.selectedApplication)
const selectedChatroom = computed(() => chatroomMessagesStore.selectedChatroom)

const currentMessage = ref('')

const { state, isMobile } = useSidebar()

const sidebarWidth = computed(() =>
  state.value === 'expanded' ? SIDEBAR_WIDTH : '0rem'
)

const isMessageSentByCurrentUser = (sender: string) => {
  return sender === userStore.senderIdentifier
}

async function send() {
  if (!currentMessage.value.trim() || !selectedApp?.value?.uuid) return

  const response = await chatroomMessagesStore.sendMessage(
    selectedApp.value.uuid,
    currentMessage.value,
  )
  currentMessage.value = ''

  if (selectedChatroom?.value?.uuid === NEW_CHAT) {
    const newChatroomId = response?.chatroom_identifier
    if (newChatroomId) {
      await navigateTo(
        `/applications/${selectedApp.value.uuid}/messages/${newChatroomId}`,
      )
      await chatroomsStore.fetchChatrooms(selectedApp.value.uuid)
    }
  }
}

const connectWebSocket = () => {
  const chatroom = selectedChatroom.value
  if (!chatroom) return

  const wsProtocol = location.protocol === 'https:' ? 'wss://' : 'ws://'
  const wsUrl = `${wsProtocol}localhost:8000/ws/chat/${chatroom.uuid}/`

  const ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    console.log('WebSocket connected to', chatroom.uuid)
  }

  ws.onmessage = (event: MessageEvent) => {
    chatroomMessagesStore.addMessage(JSON.parse(event.data))
  }

  ws.onclose = (event: CloseEvent) => {
    console.log('WebSocket disconnected:', event.code, event.reason)
    connectedChatroomId.value = null
  }

  ws.onerror = (error: Event) => {
    console.error('WebSocket error:', error)
  }

  websocket.value = ws
}

const disconnectWebSocket = () => {
  if (websocket.value) {
    console.log('Disconnecting WebSocket')
    websocket.value.close()
    websocket.value = null
  }
}

watch(
  selectedChatroom,
  (newChatroom, _, onCleanup) => {
    const newId = newChatroom?.uuid ?? null

    if (newId === NEW_CHAT) {
      return
    }

    disconnectWebSocket()

    if (newChatroom && newChatroom.uuid !== NEW_CHAT) {
      setTimeout(() => {
        connectWebSocket()
      }, 100)
    }

    onCleanup(() => {
      disconnectWebSocket()
    })
  },
  { immediate: true, once: true }
)

onUnmounted(() => {
  disconnectWebSocket()
})
</script>
