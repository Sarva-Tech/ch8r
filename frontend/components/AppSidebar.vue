<script setup lang="ts">
import {
  AppWindow,
  ChevronsUpDown,
  Sparkles,
  BookOpen,
  KeyRound,
  MessageSquare,
  Plus,
} from 'lucide-vue-next'
import AppSheet from '~/components/BaseSheet.vue'
import { toast } from 'vue-sonner'
import { getErrorMessage } from '~/lib/utils'
import { ref, computed } from 'vue'
import { Input } from '@/components/ui/input'
import { useKBDraftStore } from '~/stores/kbDraft'
import SourceSelector from '~/components/KnowledgeBase/SourceSelector.vue'
import FileUpload from '~/components/KnowledgeBase/FileUpload.vue'
import UrlInput from '~/components/KnowledgeBase/UrlInput.vue'
import TextInput from '~/components/KnowledgeBase/TextInput.vue'
import Draft from '~/components/KnowledgeBase/Draft.vue'

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenuButton,
  useSidebar,
} from '@/components/ui/sidebar'
import { DUMMY_NEW_CHATROOM, KB_SOURCES } from '~/lib/consts'
import { useNavigation } from '~/composables/useNavigation'
const { isMobile } = useSidebar()

const applicationsStore = useApplicationsStore()
const chatroomStore = useChatroomStore()

const { selectAppAndNavigate, selectChatroomAndNavigate } = useNavigation()
const { ellipsis } = useTextUtils()

const applications = computed(() => applicationsStore.applications)
const selectedApplication = computed(
  () => applicationsStore.selectedApplication,
)
const chatrooms = computed(() => chatroomStore.chatrooms)
const loading = computed(() => applicationsStore.loading)

// Application creation
const appName = ref('')

// Knowledge base
const kbDraft = useKBDraftStore()
const selectedSourceValue = ref('file')
const textInput = ref('')
const urlInput = ref('')

const sources = KB_SOURCES
const selectedSource = computed(() => sources.find((s) => s.value === selectedSourceValue.value))
const isFile = computed(() => selectedSourceValue.value === 'file')
const isUrl = computed(() => selectedSourceValue.value === 'url')
const isText = computed(() => selectedSourceValue.value === 'text')

const addText = () => {
  if (textInput.value.trim()) {
    kbDraft.addText(textInput.value.trim())
    textInput.value = ''
  }
}

const addURL = () => {
  if (urlInput.value.trim()) {
    kbDraft.addUrl(urlInput.value.trim())
    urlInput.value = ''
  }
}

const handleFileUpload = (files: File[]) => {
  kbDraft.setFiles(files)
}

const handleSubmit = () => {
  // Handle both application creation and knowledge items here
  if (appName.value.trim()) {
    // In a real app, you would call your API here
    setTimeout(() => {
      toast.success(`Created application: ${appName.value}`)
      appName.value = ''
    }, 1000)
  }

  // Knowledge items are already in the draft store
  if (kbDraft.items.length > 0) {
    toast.success(`Added ${kbDraft.items.length} items to knowledge base`)
  }
}
async function initNewChat() {
  if (selectedApplication.value) {
    await selectChatroomAndNavigate(selectedApplication.value, DUMMY_NEW_CHATROOM)
  }
}
</script>

<template>
  <Sidebar class="hidden flex-1 md:flex">
    <SidebarHeader class="gap-3 border-b">
      <div class="flex w-full items-center justify-between">
        <DropdownMenu>
          <DropdownMenuTrigger as-child>
            <SidebarMenuButton
              size="lg"
              class="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
            >
              <AppWindow class="ml-auto size-4" />
              <div class="grid flex-1 text-left text-sm leading-tight theme-neutral">
                <span class="truncate font-semibold">
                  {{ selectedApplication?.name }}
                </span>
              </div>
              <ChevronsUpDown class="ml-auto size-4" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            class="w-[--reka-dropdown-menu-trigger-width] min-w-56 rounded-lg"
            :side="isMobile ? 'bottom' : 'right'"
            align="start"
            :side-offset="4"
          >
            <DropdownMenuGroup>
              <SidebarGroupLabel>Applications</SidebarGroupLabel>
              <DropdownMenuItem
                v-for="application in applications"
                :key="application?.uuid"
                @click="selectAppAndNavigate(application)"
              >
                <Sparkles />
                {{ application?.name }}
              </DropdownMenuItem>
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenu>

        <AppSheet
          title="Create Application & Add Knowledge"
          submit-text="Save All"
          cancel-text="Cancel"
          :on-submit="handleSubmit"
          :loading="loading"
        >
          <template #trigger>
            <button
              class="h-8 px-3 ml-2 flex items-center gap-1 rounded-md bg-sidebar-accent text-sidebar-accent-foreground hover:bg-sidebar-accent/80 text-sm cursor-pointer"
            >
              <Plus class="w-4 h-4" />
            </button>
          </template>

          <!-- Application Creation Section -->
          <div class="space-y-4 mb-6 pb-6 border-b">
            <h3 class="font-medium">Create New Application</h3>
            <div class="space-y-2">
              <Label for="name" class="text-sm font-medium text-gray-900">
                Application Name
              </Label>
              <Input
                id="name"
                v-model="appName"
                placeholder="Application name"
                class="rounded-lg border border-gray-300 focus:border-primary focus:ring-2 focus:ring-primary/20 shadow-sm text-sm px-3 py-2"
              />
            </div>
          </div>

          <!-- Knowledge Base Section -->
          <div class="space-y-4">
            <h3 class="font-medium">Add to Knowledge Base</h3>
            <SourceSelector v-model="selectedSourceValue" :sources="sources" />

            <div class="space-y-2">
              <div v-if="isFile" class="space-y-2">
                <Label for="upload_files" class="text-sm font-medium">
                  Upload Files
                </Label>
                <FileUpload
                  :max-files="1"
                  @update:files="handleFileUpload"
                />
              </div>

              <UrlInput
                v-if="isUrl"
                v-model="urlInput"
                @add="addURL"
              />

              <TextInput
                v-if="isText"
                v-model="textInput"
                @add="addText"
              />
            </div>

            <div class="space-y-2">
              <Draft
                v-for="item in kbDraft.items"
                :key="item.id"
                :item="item"
                @remove="kbDraft.remove"
              />
            </div>
          </div>
        </AppSheet>
      </div>
      <SidebarGroup class="p-0 m-0">
        <SidebarGroupContent>
          <SidebarMenuButton>
            <NuxtLink
              :to="`/applications/${selectedApplication?.uuid}/knowledge-base`"
              class="hover:bg-sidebar-accent hover:text-sidebar-accent-foreground flex flex-col items-start gap-2 text-sm leading-tight whitespace-nowrap"
            >
              <div class="flex w-full items-center space-x-2">
                <BookOpen class="size-4" />
                <div class="">Knowledge Base</div>
              </div>
            </NuxtLink>
          </SidebarMenuButton>
          <SidebarMenuButton>
            <NuxtLink
              :to="`/applications/${selectedApplication?.uuid}/api-keys-and-widget`"
              class="hover:bg-sidebar-accent hover:text-sidebar-accent-foreground flex flex-col items-start gap-2 text-sm leading-tight whitespace-nowrap"
            >
              <div class="flex w-full items-center space-x-2">
                <KeyRound class="size-4" />
                <div>API Keys & Widget</div>
              </div>
            </NuxtLink>
          </SidebarMenuButton>
          <SidebarMenuButton
            class="hover:bg-sidebar-accent hover:text-sidebar-accent-foreground flex flex-col items-start gap-2 text-sm leading-tight whitespace-nowrap"
            @click="initNewChat"
          >
            <div class="flex w-full items-center space-x-2">
              <MessageSquare class="size-4" />
              <div>Start New Conversation</div>
            </div>
          </SidebarMenuButton>
        </SidebarGroupContent>
      </SidebarGroup>
    </SidebarHeader>
    <div class="flex w-full items-center px-2 py-2">
      <SidebarGroupLabel>Conversations</SidebarGroupLabel>
    </div>

    <SidebarContent class="overflow-x-hidden">
      <SidebarGroup class="p-0 m-0">
        <SidebarGroupContent class="p-2">
          <NuxtLink
            v-for="chatroom in chatrooms"
            :key="chatroom.uuid"
            :to="`/applications/${selectedApplication.uuid}/messages/${chatroom.uuid}`"
            class="
              hover:bg-sidebar-accent
              hover:text-sidebar-accent-foreground
              flex
              flex-col
              items-start
              gap-2
              px-4
              py-2
              text-sm
              leading-tight
              whitespace-nowrap
              rounded-lg
            "
          >
            <div class="flex w-full items-center gap-2">
              <span>{{ ellipsis(chatroom.name, 30) }}</span>
              <span class="ml-auto text-xs">
                {{ $dayjs(chatroom.last_message?.created_at).fromNow() }}
              </span>
            </div>
            <span class="line-clamp-2 whitespace-break-spaces text-xs">
              {{ chatroom.last_message?.message }}
            </span>
          </NuxtLink>
        </SidebarGroupContent>
      </SidebarGroup>
    </SidebarContent>
  </Sidebar>
</template>
