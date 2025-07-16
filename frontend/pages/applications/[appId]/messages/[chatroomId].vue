<template>
  <div class="flex flex-col h-screen">
    <div
      class="overflow-y-auto pt-[72px] pb-[120px] px-4 space-y-2"
      :style="`height: calc(100vh - 64px - 112px);`"
    >
      <div
        v-for="message in messages"
        :key="message.id"
        class="bg-gray-200 rounded p-2 max-w-xs whitespace-pre-wrap"
      >
        {{ message.message }}
      </div>
    </div>

    <div class="p-4 border-t fixed bottom-0 w-full h-[112px]">
      <div class="grid w-full gap-2">
        <Textarea v-model="currentMessage" placeholder="Message" />
        <Button class="w-15" @click="send">Send</Button>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { Textarea } from '@/components/ui/textarea'
import { NEW_CHAT } from '~/lib/consts'

const websocket = ref<WebSocket | null>(null)
const connectedChatroomId = ref<string | null>(null)

const chatroomsStore = useChatroomStore()
const chatroomMessagesStore = useChatroomMessagesStore()
const appStore = useApplicationsStore()

const messages = computed(() => chatroomMessagesStore.messages)
const selectedApp = computed(() => appStore.selectedApplication)
const selectedChatroom = computed(() => chatroomMessagesStore.selectedChatroom)

const currentMessage = ref('')

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
