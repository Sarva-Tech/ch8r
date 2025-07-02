<template>
  <div class="flex flex-col h-screen">
    <header
      class="bg-background fixed w-full top-0 z-10 flex shrink-0 items-center gap-2 border-b p-4"
    >
      <SidebarTrigger class="-ml-1" />
      <Separator
        orientation="vertical"
        class="mr-2 data-[orientation=vertical]:h-4"
      />
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem class="hidden md:block">
            <BreadcrumbLink href="#">All Inboxes</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator class="hidden md:block" />
          <BreadcrumbItem>
            <BreadcrumbPage>Inbox</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
    </header>

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

const chatroomMessagesStore = useChatroomMessagesStore()
const appStore = useApplicationsStore()

const messages = computed(() => chatroomMessagesStore.messages)
const selectedApp = computed(() => appStore.selectedApplication)

const currentMessage = ref('')

function send() {
  if (!currentMessage.value.trim() || !selectedApp?.value?.uuid) return

  chatroomMessagesStore.sendMessage(selectedApp.value.uuid, currentMessage.value)
  currentMessage.value = ''
}
</script>
