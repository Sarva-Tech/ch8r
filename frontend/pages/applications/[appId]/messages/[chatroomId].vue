<template>
  <div class="flex flex-col h-screen">
    <div
      class="overflow-y-auto pt-[72px] pb-[120px] px-4 space-y-2"
      :style="`height: calc(100vh - 64px - 112px);`"
    >
      <div v-for="message in messages" :key="message.id" class="bg-gray-200 rounded p-2 max-w-xs whitespace-pre-wrap">{{ message.message }}</div>
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

const route = useRoute()
const { appId, chatroomId } = route.params

const websocket = ref<WebSocket | null>(null)

const chatroomsStore = useChatroomStore()
const chatroomMessagesStore = useChatroomMessagesStore()
const appStore = useApplicationsStore()

const messages = computed(() => chatroomMessagesStore.messages)
const apps: Ref<Application[]> = computed(() => appStore.applications)
const selectedApp = computed(() => appStore.selectedApplication)
const chatrooms: Ref<ChatroomPreview[]> = computed(() => chatroomsStore.chatrooms)
const selectedChatroom = computed(() => chatroomMessagesStore.selectedChatroom)

const currentMessage = ref('')

watch(apps, (newVal) => {
  if (newVal && !selectedApp.value) {
    const app: Application = apps.value.find((app) => app?.uuid === appId)

    if (app) {
      appStore.selectApplication(app)

      if (!chatrooms.value && chatrooms?.value?.length === 0) {
        chatroomsStore.fetchChatrooms(app.uuid)
      }
    }
  }
}, { immediate: true });

watch(chatrooms, (newVal) => {
  if (newVal) {
    const chatroom = chatrooms.value.find((chatroom) => chatroom.uuid === chatroomId)
    if (selectedApp.value && chatroom) {
      chatroomMessagesStore.selectChatroom(selectedApp.value.uuid, chatroom.uuid)
    }
  }
}, { immediate: true });

watch(selectedChatroom, (newVal) => {
  if (newVal) {
    connectWebSocket()
  }
})


onMounted(() => {
  if (!apps.value || apps.value.length === 0) {
    appStore.fetchApplications()
  }
})

onUnmounted(() => {
  disconnectWebSocket();
});

function send() {
  if (!currentMessage.value.trim() || !selectedApp?.value?.uuid) return

  chatroomMessagesStore.sendMessage(selectedApp.value.uuid, currentMessage.value)
  currentMessage.value = ''
}

const connectWebSocket = () => {
  const wsProtocol = location.protocol === "https:" ? "wss://" : "ws://";
  const wsUrl = `${wsProtocol}localhost:8000/ws/chat/${selectedChatroom.value?.uuid}/`;
  websocket.value = new WebSocket(wsUrl);

  websocket.value.onopen = () => {
    console.log('WebSocket connected');
  };

  websocket.value.onmessage = (event: MessageEvent) => {
    chatroomMessagesStore.addMessage(JSON.parse(event.data))
  };

  websocket.value.onclose = (event: CloseEvent) => {
    console.log('WebSocket disconnected:', event.code, event.reason);
  };

  websocket.value.onerror = (error: Event) => {
    console.error('WebSocket error:', error);
  };
};

const disconnectWebSocket = () => {
  if (websocket.value) {
    websocket.value.close();
    websocket.value = null;
  }
};
</script>
