<script setup lang="ts">
import {
  AppWindow,
  ChevronsUpDown,
  Sparkles,
  BookOpen,
  KeyRound,
  MessageSquare,
  Plus,
  Settings,
  Bell,
  ChevronDown,
  ChevronUp,
} from 'lucide-vue-next'
import AppSheet from '~/components/BaseSheet.vue'
import { toast } from 'vue-sonner'
import { ref, computed } from 'vue'
import { Input } from '@/components/ui/input'
import { useKBDraftStore } from '~/stores/kbDraft'
import SourceSelector from '~/components/KnowledgeBase/SourceSelector.vue'
import FileUpload from '~/components/FileUpload.vue'
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

const settingsExpanded = ref(false)
const toggleSettings = () => {
  settingsExpanded.value = !settingsExpanded.value
}

const activeMenu = ref('')

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

const appName = ref('')
const kbDraft = useKBDraftStore()
const selectedSourceValue = ref('file')

const sources = KB_SOURCES
const selectedSource = computed(() =>
  sources.find((s) => s.value === selectedSourceValue.value),
)
const isFile = computed(() => selectedSourceValue.value === 'file')
const isUrl = computed(() => selectedSourceValue.value === 'url')
const isText = computed(() => selectedSourceValue.value === 'text')

const handleSubmit = async () => {
  if (!appName.value.trim()) {
    toast.error('Application name is required')
    return
  }

  try {
    const newApp = await applicationsStore.createApplicationWithKB(
      appName.value,
    )
    if (newApp) {
      await selectAppAndNavigate(newApp)
      toast.success(`Application "${newApp?.name}" created successfully`)
      appName.value = ''
      kbDraft.clear()
    } else {
      toast.error(applicationsStore.error || 'Failed to create application')
    }
  } catch (err: any) {
    toast.error(err.message || 'Something went wrong')
    console.error('Failed to create application:', err)
  }
}

function setActiveMenu(uuid: string) {
  activeMenu.value = uuid
}


async function initNewChat() {
  activeMenu.value = 'newChat'
  if (selectedApplication.value) {
    await selectChatroomAndNavigate(
      selectedApplication.value,
      DUMMY_NEW_CHATROOM,
    )
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
              <div
                class="grid flex-1 text-left text-sm leading-tight theme-neutral"
              >
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
          title="Create Application"
          submit-text="Create"
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

          <div class="space-y-4">
            <div class="space-y-2">
              <Label
                for="name"
                class="text-sm font-medium flex items-center gap-1"
              >
                Application Name
                <span class="text-xs text-muted-foreground italic ml-1"
                  >Required</span
                >
              </Label>
              <Input
                id="name"
                v-model="appName"
                placeholder="Application name"
                class="rounded-lg border border-gray-300 focus:border-primary focus:ring-2 focus:ring-primary/20 shadow-sm text-sm px-3 py-2"
              />
            </div>
          </div>
          <div class="space-y-4 mt-4">
            <SourceSelector v-model="selectedSourceValue" :sources="sources" />

            <div class="space-y-2">
              <div v-if="isFile" class="space-y-2">
                <Label for="upload_files" class="text-sm font-medium">
                  Upload Files
                </Label>
                <FileUpload @update:files="kbDraft.setFiles" />
              </div>
              <UrlInput v-if="isUrl" />
              <TextInput v-if="isText" />
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
          <SidebarMenuButton
            class="flex items-center justify-between text-sm"
            @click="toggleSettings"
          >
            <div class="flex items-center gap-2">
              <Settings class="size-4" />
              <span class="">Settings</span>
            </div>
            <ChevronUp v-if="settingsExpanded" class="size-4" />
            <ChevronDown v-else class="size-4" />
          </SidebarMenuButton>
          <div v-if="settingsExpanded" class="flex flex-col">
            <SidebarMenuButton
              :class="[
                'px-4 py-2 rounded-lg text-sm hover:bg-sidebar-accent hover:text-sidebar-accent-foreground',
                activeMenu === 'notification'
                  ? 'bg-sidebar-accent text-sidebar-accent-foreground font-semibold'
                  : '',
              ]"
            >
              <NuxtLink
                to="/notification-profile"
                class="flex items-center gap-2 w-full"
                @click.native="activeMenu = 'notification'"
              >
                <Bell class="size-4" />
                <span>Notification Profile</span>
              </NuxtLink>
            </SidebarMenuButton>
          </div>
          <SidebarMenuButton
            :class="[
              'hover:bg-sidebar-accent hover:text-sidebar-accent-foreground flex flex-col items-start gap-2 text-sm leading-tight whitespace-nowrap',
              activeMenu === 'knowledge-base'
                ? 'bg-sidebar-accent text-sidebar-accent-foreground font-semibold'
                : '',
            ]"
            @click="activeMenu = 'knowledge-base'"
          >
            <NuxtLink
              :to="`/applications/${selectedApplication?.uuid}/knowledge-base`"
              class="flex w-full items-center space-x-2"
            >
              <BookOpen class="size-4" />
              <div>Knowledge Base</div>
            </NuxtLink>
          </SidebarMenuButton>
          <SidebarMenuButton
            :class="[
              'hover:bg-sidebar-accent hover:text-sidebar-accent-foreground flex flex-col items-start gap-2 text-sm leading-tight whitespace-nowrap',
              activeMenu === 'api-keys'
                ? 'bg-sidebar-accent text-sidebar-accent-foreground font-semibold'
                : '',
            ]"
            @click="activeMenu = 'api-keys'"
          >
            <NuxtLink
              :to="`/applications/${selectedApplication?.uuid}/api-keys-and-widget`"
              class="flex w-full items-center space-x-2 w-full"
            >
              <KeyRound class="size-4" />
              <div>API Keys & Widget</div>
            </NuxtLink>
          </SidebarMenuButton>
          <SidebarMenuButton
            @click="initNewChat"
            :class="[
              'hover:bg-sidebar-accent hover:text-sidebar-accent-foreground flex flex-col items-start gap-2 text-sm leading-tight whitespace-nowrap cursor-pointer',
              activeMenu === 'newChat'
                ? 'bg-sidebar-accent text-sidebar-accent-foreground font-semibold'
                : '',
            ]"
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
            @click="() => setActiveMenu(chatroom.uuid)"
            :class="[
          'hover:bg-sidebar-accent hover:text-sidebar-accent-foreground flex flex-col items-start gap-2 px-4 py-2 text-sm leading-tight whitespace-nowrap rounded-lg',
          activeMenu === chatroom.uuid ? 'bg-sidebar-accent text-sidebar-accent-foreground font-semibold' : ''
        ]"
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
