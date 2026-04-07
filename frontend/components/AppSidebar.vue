<script setup lang="ts">
import {
  AppWindow,
  ChevronsUpDown,
  Sparkles,
  BookOpen,
  KeyRound,
  MessageSquare,
  Plus,
  Settings2,
  Box,
  Puzzle,
  Bell,
  Lock,
  MoreVertical,
  Pencil,
  Trash2,
  ChevronLeft,
} from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import type SlideOver from '~/components/SlideOver.vue'
import { ref, computed, onBeforeUnmount, watch, nextTick } from 'vue'
import dayjs from 'dayjs'

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenuButton,
  useSidebar,
} from '@/components/ui/sidebar'

import { useNavigation } from '~/composables/useNavigation'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '~/components/ui/dropdown-menu'
import { Button } from '~/components/ui/button'
import C8Dialog from '~/components/C8Dialog.vue'
import NewApp from '~/components/App/NewApp.vue'

const newAppSlideOver = ref<InstanceType<typeof SlideOver> | null>(null)

const activeMenu = ref('')
const route = useRoute()

watch(
  () => route.path,
  (newPath) => {
    const uuidMatch = newPath.match(
      /\/applications\/[^/]+\/(?:messages|knowledge-base|api-keys-and-widget)\/([^/]+)/,
    )
    if (uuidMatch && uuidMatch[1]) {
      setActiveMenu(uuidMatch[1])
    }

    if (newPath.includes('/messages/new_chat')) {
      setActiveMenu('newChat')
    }

    if (
      newPath.includes('/knowledge-base')
      && !newPath.match(/\/knowledge-base\/[^/]+$/)
    ) {
      setActiveMenu('knowledge-base')
    } else if (
      newPath.includes('/api-keys-and-widget')
      && !newPath.match(/\/api-keys-and-widget\/[^/]+$/)
    ) {
      setActiveMenu('api-keys')
    }
  },
  { immediate: true },
)

const { isMobile } = useSidebar()
const applicationsStore = useApplicationsStore()
const chatroomStore = useChatroomStore()
const liveUpdateStore = useLiveUpdateStore()

const unsubscribeUnread = liveUpdateStore.subscribe((msg) => {
  if (msg.type === 'unread_update') {
    const { chatroom_uuid, has_unread } = msg as any
    if (has_unread) {
      chatroomStore.markUnread(chatroom_uuid)
    } else {
      chatroomStore.markRead(chatroom_uuid)
    }
  }
  if (msg.type === 'message') {
    const data = (msg as any).data
    if (data?.chatroom_identifier) {
      chatroomStore.updateLastMessage(data.chatroom_identifier, data)
    }
  }
  if (msg.type === 'new_chatroom') {
    const data = (msg as any).data
    if (data) {
      chatroomStore.addChatroom(data)
    }
  }
})
onBeforeUnmount(() => unsubscribeUnread())

watch(() => liveUpdateStore.isConnected, (connected, wasConnected) => {
  if (connected && wasConnected === false && selectedApplication.value?.uuid) {
    chatroomStore.fetchChatrooms(selectedApplication.value.uuid)
  }
})

const { selectAppAndNavigate } = useNavigation()
const { ellipsis } = useTextUtils()

function setActiveMenu(uuid: string) {
  activeMenu.value = uuid
  localStorage.setItem('activeMenu', uuid)
}

const applications = computed(() => applicationsStore.applications)
const selectedApplication = computed(
  () => applicationsStore.selectedApplication,
)
const chatrooms = computed(() => chatroomStore.chatrooms)

const isAppSettingsRoute = computed(() => route.path.match(/\/applications\/[^/]+\/settings/) !== null)

const isSettingsRoute = computed(() => route.path.startsWith('/settings') || isAppSettingsRoute.value)

const backToAppLink = computed(() => {
  if (isAppSettingsRoute.value && selectedApplication.value) {
    return `/applications/${selectedApplication.value.uuid}/knowledge-base`
  }
  return '/'
})

const appSettingsItems = [
  { name: 'AI Models', tab: 'models', icon: Box },
  { name: 'Integrations', tab: 'integrations', icon: Puzzle },
  { name: 'Agent Configuration', tab: 'prompt', icon: Sparkles },
  { name: 'Notifications', tab: 'notifications', icon: Bell },
]

const currentAppSettingsTab = computed(() => {
  const tab = route.query.tab as string
  return tab || 'models'
})

const settingsItems = [
  { name: 'AI Provider', path: '/settings/ai-providers', icon: Box, key: 'models' },
  { name: 'Integrations', path: '/settings/integrations', icon: Puzzle, key: 'integrations' },
  { name: 'Notification Profile', path: '/settings/notification-profile', icon: Bell, key: 'notification-profile' },
  { name: 'Change Password', path: '/settings/change-password', icon: Lock, key: 'change-password' },
]

async function initNewChat() {
  setActiveMenu('newChat')
  if (selectedApplication.value) {
    await navigateTo(`/applications/${selectedApplication.value.uuid}/messages/new_chat`)
  }
}
const editingChatroomId = ref<string | null>(null)
const openMenuChatroomId = ref<string | null>(null)
const editingName = ref('')
const originalName = ref('')
const renameInputRef = ref<HTMLInputElement | null>(null)
const chatroomToDelete = ref<ChatroomPreview | null>(null)
const showDeleteDialog = ref(false)

function setRenameInputRef(el: HTMLInputElement | null, chatroomUuid: string) {
  if (el && editingChatroomId.value === chatroomUuid) {
    renameInputRef.value = el
  }
}

function startRename(chatroom: ChatroomPreview) {
  openMenuChatroomId.value = null
  editingChatroomId.value = chatroom.uuid
  editingName.value = chatroom.name
  originalName.value = chatroom.name
  nextTick(() => {
    renameInputRef.value?.focus()
    renameInputRef.value?.select()
  })
}

function formatTimeShort(date: string | undefined): string {
  if (!date) return ''
  const now = dayjs()
  const then = dayjs(date)
  const diffSeconds = now.diff(then, 'second')
  const diffMinutes = now.diff(then, 'minute')
  const diffHours = now.diff(then, 'hour')
  const diffDays = now.diff(then, 'day')
  const diffWeeks = now.diff(then, 'week')
  const diffMonths = now.diff(then, 'month')
  const diffYears = now.diff(then, 'year')

  if (diffSeconds < 60) return 'now'
  if (diffMinutes < 60) return `${diffMinutes}m`
  if (diffHours < 24) return `${diffHours}h`
  if (diffDays < 7) return `${diffDays}d`
  if (diffWeeks < 4) return `${diffWeeks}w`
  if (diffMonths < 12) return `${diffMonths}mo`
  return `${diffYears}y`
}

async function saveRename() {
  const trimmedName = editingName.value.trim()
  const trimmedOriginal = originalName.value.trim()
  const hasChanged = trimmedName !== trimmedOriginal
  if (editingChatroomId.value && trimmedName && hasChanged) {
    await chatroomStore.renameChatroom(
      selectedApplication.value?.uuid || '',
      editingChatroomId.value,
      trimmedName
    )
    toast.success('Chatroom renamed')
  }
  editingChatroomId.value = null
  editingName.value = ''
  originalName.value = ''
}

function cancelRename() {
  editingChatroomId.value = null
  editingName.value = ''
  originalName.value = ''
}

function confirmDelete(chatroom: ChatroomPreview) {
  chatroomToDelete.value = chatroom
  showDeleteDialog.value = true
}

async function handleDelete() {
  if (chatroomToDelete.value) {
    await chatroomStore.deleteChatroom(
      selectedApplication.value?.uuid || '',
      chatroomToDelete.value.uuid
    )
    toast.success('Conversation deleted')
    if (activeMenu.value === chatroomToDelete.value.uuid) {
      navigateTo(`/applications/${selectedApplication.value?.uuid}/messages/new_chat`)
    }
  }
  showDeleteDialog.value = false
  chatroomToDelete.value = null
}
</script>

<template>
  <Sidebar class="hidden flex-1 md:flex">
    <SidebarHeader class="gap-3 border-b">
      <template v-if="isSettingsRoute">
        <div class="p-2">
          <NuxtLink
            :to="backToAppLink"
            class="flex items-center gap-2 text-sm font-bold text-muted-foreground hover:text-foreground transition-colors"
          >
            <ChevronLeft class="size-4" />
            Back to App
          </NuxtLink>
        </div>
        <SidebarGroup
          v-if="isAppSettingsRoute"
          class="p-0 m-0"
        >
          <SidebarGroupContent class="space-y-1">
            <SidebarMenuButton
              v-for="item in appSettingsItems"
              :key="item.tab"
              :class="[
                'hover:bg-sidebar-accent hover:text-sidebar-accent-foreground flex flex-col items-start gap-2 text-sm leading-tight whitespace-nowrap',
                currentAppSettingsTab === item.tab
                  ? 'bg-sidebar-accent text-sidebar-accent-foreground font-semibold'
                  : '',
              ]"
            >
              <NuxtLink
                :to="`/applications/${selectedApplication?.uuid}/settings?tab=${item.tab}`"
                class="flex w-full items-center space-x-2"
              >
                <component
                  :is="item.icon"
                  class="size-4"
                />
                <div>{{ item.name }}</div>
              </NuxtLink>
            </SidebarMenuButton>
          </SidebarGroupContent>
        </SidebarGroup>
        <SidebarGroup
          v-if="!isAppSettingsRoute"
          class="p-0 m-0"
        >
          <SidebarGroupContent class="space-y-1">
            <SidebarMenuButton
              v-for="item in settingsItems"
              :key="item.path"
              :class="[
                'hover:bg-sidebar-accent hover:text-sidebar-accent-foreground flex flex-col items-start gap-2 text-sm leading-tight whitespace-nowrap',
                route.path === item.path
                  ? 'bg-sidebar-accent text-sidebar-accent-foreground font-semibold'
                  : '',
              ]"
            >
              <NuxtLink
                :to="item.path"
                class="flex w-full items-center space-x-2"
              >
                <component
                  :is="item.icon"
                  class="size-4"
                />
                <div>{{ item.name }}</div>
              </NuxtLink>
            </SidebarMenuButton>
          </SidebarGroupContent>
        </SidebarGroup>
      </template>

      <template v-else>
        <div class="flex w-full items-center justify-between space-x-2">
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

                <DropdownMenuSeparator />
                <DropdownMenuItem
                  class="gap-2 p-2"
                  @click="newAppSlideOver?.openSlide()"
                >
                  <div class="flex size-6 items-center justify-center rounded-md border bg-transparent">
                    <Plus class="size-4" />
                  </div>
                  <div
                    class="font-medium text-muted-foreground"
                  >
                    Create New Application
                  </div>
                </DropdownMenuItem>
              </DropdownMenuGroup>
            </DropdownMenuContent>
          </DropdownMenu>
          <Button
            class="w-8 h-8"
            variant="ghost"
            size="icon"
            @click="navigateTo(`/applications/${selectedApplication?.uuid}/settings`)"
          >
            <Settings2 class="w-4 h-4" />
          </Button>
        </div>
        <SidebarGroup class="p-0 m-0">
          <SidebarGroupContent class="space-y-1">
            <SidebarMenuButton
              :class="[
                'hover:bg-sidebar-accent hover:text-sidebar-accent-foreground flex flex-col items-start gap-2 text-sm leading-tight whitespace-nowrap',
                activeMenu === 'knowledge-base'
                  ? 'bg-sidebar-accent text-sidebar-accent-foreground font-semibold'
                  : '',
              ]"
            >
              <NuxtLink
                :to="`/applications/${selectedApplication?.uuid}/knowledge-base`"
                class="flex w-full items-center space-x-2"
                @click="setActiveMenu('knowledge-base')"
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
            >
              <NuxtLink
                :to="`/applications/${selectedApplication?.uuid}/api-keys-and-widget`"
                class="flex w-full items-center space-x-2"
                @click="setActiveMenu('api-keys')"
              >
                <KeyRound class="size-4" />
                <div>API Keys & Widget</div>
              </NuxtLink>
            </SidebarMenuButton>
            <SidebarMenuButton
              :class="[
                'hover:bg-sidebar-accent hover:text-sidebar-accent-foreground flex flex-col items-start gap-2 text-sm leading-tight whitespace-nowrap cursor-pointer',
                activeMenu === 'newChat'
                  ? 'bg-sidebar-accent text-sidebar-accent-foreground font-semibold'
                  : '',
              ]"
              @click="initNewChat"
            >
              <div class="flex w-full items-center space-x-2">
                <MessageSquare class="size-4" />
                <div>Start New Conversation</div>
              </div>
            </SidebarMenuButton>
          </SidebarGroupContent>
        </SidebarGroup>
      </template>
    </SidebarHeader>

    <template v-if="!isSettingsRoute">
      <div class="flex w-full items-center px-3 py-1">
        <SidebarGroupLabel class="text-xs font-medium">
          Conversations
        </SidebarGroupLabel>
      </div>

      <ScrollArea class="h-full">
        <SidebarContent class="">
          <SidebarGroup class="p-0 m-0 overflow-visible">
            <SidebarGroupContent class="p-2 space-y-1 overflow-visible">
              <div
                v-for="chatroom in chatrooms"
                :key="chatroom.uuid"
                class="relative"
              >
                <NuxtLink
                  :to="`/applications/${selectedApplication?.uuid}/messages/${chatroom.uuid}`"
                  :class="[
                    'hover:bg-sidebar-accent hover:text-sidebar-accent-foreground flex items-center gap-2 px-4 py-2 text-sm leading-tight rounded-lg min-w-0',
                    activeMenu === chatroom.uuid ? 'bg-sidebar-accent text-sidebar-accent-foreground font-semibold' : '',
                    chatroom.has_unread && activeMenu !== chatroom.uuid ? 'bg-primary/10 border border-border' : '',
                  ]"
                  @click="() => { chatroomStore.markRead(chatroom.uuid); setActiveMenu(chatroom.uuid) }"
                >
                  <div class="flex flex-col items-start gap-1 flex-1 min-w-0">
                    <div class="flex w-full items-center gap-2 min-w-0">
                      <template v-if="editingChatroomId === chatroom.uuid">
                        <input
                          :ref="(el) => setRenameInputRef(el as HTMLInputElement, chatroom.uuid)"
                          v-model="editingName"
                          type="text"
                          class="flex-1 bg-transparent outline-none min-w-0 text-sm"
                          @blur="saveRename"
                          @keydown.enter="saveRename"
                          @keydown.esc="cancelRename"
                        >
                      </template>
                      <template v-else>
                        <span
                          class="truncate flex-1 cursor-pointer"
                          @dblclick="startRename(chatroom)"
                        >{{ ellipsis(chatroom.name, 30) }}</span>
                      </template>
                      <div class="flex items-center gap-1 flex-shrink-0">
                        <span class="text-xs text-muted-foreground">
                          {{ formatTimeShort(chatroom.last_message?.created_at) }}
                        </span>
                        <DropdownMenu
                          v-if="editingChatroomId !== chatroom.uuid"
                          :open="openMenuChatroomId === chatroom.uuid"
                          @update:open="(open) => openMenuChatroomId = open ? chatroom.uuid : null"
                        >
                          <DropdownMenuTrigger as-child>
                            <Button
                              variant="ghost"
                              size="icon"
                              class="h-6 w-6 p-0 -mr-2"
                              @click.prevent
                            >
                              <MoreVertical class="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent
                            align="end"
                            class="w-32"
                          >
                            <DropdownMenuItem @click="startRename(chatroom)">
                              <Pencil class="h-4 w-4" />
                              Rename
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              class="text-destructive focus:text-destructive"
                              @click="confirmDelete(chatroom)"
                            >
                              <Trash2 class="h-4 w-4 text-destructive" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>
                    <span class="line-clamp-2 whitespace-break-spaces text-xs w-full min-w-0">
                      {{ chatroom.last_message?.message }}
                    </span>
                  </div>
                  <UnreadBadge
                    v-if="chatroom.has_unread"
                    class="flex-shrink-0"
                  />
                </NuxtLink>
              </div>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>
      </ScrollArea>
    </template>
  </Sidebar>
  <NewApp
    ref="newAppSlideOver"
    @success="setActiveMenu"
  />
  <C8Dialog
    v-model:open="showDeleteDialog"
    title="Delete Conversation"
    confirm-text="Delete"
    cancel-text="Cancel"
    :destructive="true"
    @confirm="handleDelete"
    @cancel="showDeleteDialog = false; chatroomToDelete = null"
  >
    <template #description>
      <div>
        Are you sure you want to delete <span class="font-bold"> {{ chatroomToDelete?.name }} </span>?
      </div>
    </template>
  </C8Dialog>
</template>
