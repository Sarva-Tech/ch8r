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
  Settings2,
  Bell,
  Box,
  ChevronDown,
  ChevronUp,
  Puzzle,
} from 'lucide-vue-next'
import SlideOver from '~/components/SlideOver.vue'
import { ref, computed, onMounted, watch } from 'vue'

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
  DropdownMenuItem,
  DropdownMenuSeparator,
} from '~/components/ui/dropdown-menu'
import { Button } from '~/components/ui/button'
import ConfigureApp from '~/components/App/ConfigureApp.vue'
import { useRoute } from 'vue-router'
import NewApp from '~/components/App/NewApp.vue'

const newAppSlideOver = ref<InstanceType<typeof SlideOver> | null>(null)
const configureAppSlideOver = ref<InstanceType<typeof SlideOver> | null>(null)

const activeMenu = ref('')
const route = useRoute()

const settingsExpanded = ref(
  localStorage.getItem('settingsExpanded') === 'true',
)

function setActiveMenu(uuid: string) {
  activeMenu.value = uuid
  localStorage.setItem('activeMenu', uuid)
}

const toggleSettings = () => {
  settingsExpanded.value = !settingsExpanded.value
  localStorage.setItem('settingsExpanded', settingsExpanded.value.toString())
}

onMounted(() => {
  const savedActiveMenu = localStorage.getItem('activeMenu')
  if (savedActiveMenu) {
    activeMenu.value = savedActiveMenu
  }

  const savedSettingsExpanded = localStorage.getItem('settingsExpanded')
  if (savedSettingsExpanded !== null) {
    settingsExpanded.value = savedSettingsExpanded === 'true'
  }
})

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

    if (newPath.startsWith('/settings/')) {
      const settingType = newPath.split('/')[2]
      setActiveMenu(settingType)

      if (!settingsExpanded.value) {
        settingsExpanded.value = true
        localStorage.setItem('settingsExpanded', 'true')
      }
    }

    if (
      newPath.includes('/knowledge-base') &&
      !newPath.match(/\/knowledge-base\/[^/]+$/)
    ) {
      setActiveMenu('knowledge-base')
    } else if (
      newPath.includes('/api-keys-and-widget') &&
      !newPath.match(/\/api-keys-and-widget\/[^/]+$/)
    ) {
      setActiveMenu('api-keys')
    }
  },
  { immediate: true },
)

const { isMobile } = useSidebar()
const applicationsStore = useApplicationsStore()
const chatroomStore = useChatroomStore()

const { selectAppAndNavigate } = useNavigation()
const { ellipsis } = useTextUtils()

const applications = computed(() => applicationsStore.applications)
const selectedApplication = computed(
  () => applicationsStore.selectedApplication,
)
const chatrooms = computed(() => chatroomStore.chatrooms)
async function initNewChat() {
  setActiveMenu('newChat')
  if (selectedApplication.value) {
    await navigateTo(`/applications/${selectedApplication.value.uuid}/messages/new_chat`)
  }
}
</script>

<template>
  <Sidebar class="hidden flex-1 md:flex">
    <SidebarHeader class="gap-3 border-b">
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
              <DropdownMenuItem class="gap-2 p-2" @click="newAppSlideOver?.openSlide()">
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
          @click="configureAppSlideOver?.openSlide()"
        >
          <Settings2 class="w-4 h-4" />
        </Button>
      </div>
      <SidebarGroup class="p-0 m-0">
        <SidebarGroupContent class="space-y-1">
          <SidebarMenuButton
            data-settings-button
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
          <div v-if="settingsExpanded" data-settings-menu class="flex flex-col space-y-1">
            <SidebarMenuButton
              :class="[
                'px-4 py-2 rounded-lg text-sm hover:bg-sidebar-accent hover:text-sidebar-accent-foreground',
                activeMenu === 'models'
                  ? 'bg-sidebar-accent text-sidebar-accent-foreground font-semibold'
                  : '',
              ]"
            >
              <NuxtLink
                to="/settings/models"
                class="flex items-center gap-2 w-full"
                @click="setActiveMenu('models')"
              >
                <Box class="size-4" />
                <span>Models</span>
              </NuxtLink>
            </SidebarMenuButton>

            <SidebarMenuButton
              :class="[
                'px-4 py-2 rounded-lg text-sm hover:bg-sidebar-accent hover:text-sidebar-accent-foreground',
                activeMenu === 'integrations'
                  ? 'bg-sidebar-accent text-sidebar-accent-foreground font-semibold'
                  : '',
              ]"
            >
              <NuxtLink
                to="/settings/integrations"
                class="flex items-center gap-2 w-full"
                @click="setActiveMenu('integrations')"
              >
                <Puzzle class="size-4" />
                <span>Integrations</span>
              </NuxtLink>
            </SidebarMenuButton>

            <SidebarMenuButton
              :class="[
                'px-4 py-2 rounded-lg text-sm hover:bg-sidebar-accent hover:text-sidebar-accent-foreground',
                activeMenu === 'notification-profile'
                  ? 'bg-sidebar-accent text-sidebar-accent-foreground font-semibold'
                  : '',
              ]"
            >
              <NuxtLink
                to="/settings/notification-profile"
                class="flex items-center gap-2 w-full"
                @click="setActiveMenu('notification-profile')"
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
            @click="setActiveMenu('knowledge-base')"
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
            @click="setActiveMenu('api-keys')"
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
    </SidebarHeader>

    <div class="flex w-full items-center px-2 py-2">
      <SidebarGroupLabel>Conversations</SidebarGroupLabel>
    </div>

    <ScrollArea class="h-full">
      <SidebarContent class="">
        <SidebarGroup class="p-0 m-0">
          <SidebarGroupContent class="p-2 space-y-1">
            <NuxtLink
              v-for="chatroom in chatrooms"
              :key="chatroom.uuid"
              :to="`/applications/${selectedApplication.uuid}/messages/${chatroom.uuid}`"
              :class="[
                'hover:bg-sidebar-accent hover:text-sidebar-accent-foreground flex flex-col items-start gap-2 px-4 py-2 text-sm leading-tight whitespace-nowrap rounded-lg',
                activeMenu === chatroom.uuid ? 'bg-sidebar-accent text-sidebar-accent-foreground font-semibold' : ''
              ]"
              @click="() => setActiveMenu(chatroom.uuid)"
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
    </ScrollArea>
  </Sidebar>
  <NewApp ref="newAppSlideOver" @success="setActiveMenu" />
  <SlideOver
    ref="configureAppSlideOver"
    title="Configure Application"
    submit-text="Configure"
    cancel-text="Cancel"
    width="!w-lg !max-w-xl"
    :show-submit="false"
  >
    <ConfigureApp />
  </SlideOver>
</template>
