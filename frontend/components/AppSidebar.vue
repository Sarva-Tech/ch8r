<script setup lang="ts">
import {
  AppWindow,
  ChevronsUpDown,
  Sparkles,
  BookOpen,
  KeyRound,
  MessageSquare
} from 'lucide-vue-next'

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenuButton,
  useSidebar,
} from '@/components/ui/sidebar'
const { isMobile } = useSidebar()

const applicationsStore = useApplicationsStore()
const chatroomStore = useChatroomStore()

const { selectAndNavigate } = useAppNavigation()
const { ellipsis } = useTextUtils()


const applications = computed(() => applicationsStore.applications)
const selectedApplication = computed(
  () => applicationsStore.selectedApplication,
)
const chatrooms = computed(() => chatroomStore.chatrooms)
</script>

<template>
  <Sidebar class="hidden flex-1 md:flex">
    <SidebarHeader class="gap-3 border-b">
      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <SidebarMenuButton
            size="lg"
            class="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
          >
            <AppWindow class="ml-auto size-4" />
            <div class="grid flex-1 text-left text-sm leading-tight">
              <span class="truncate font-semibold">{{
                selectedApplication?.name
              }}</span>
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
            <DropdownMenuItem
              v-for="application in applications"
              :key="application.uuid"
              @click="selectAndNavigate(application)"
            >
              <Sparkles />
              {{ application.name }}
              <DropdownMenuSeparator />
            </DropdownMenuItem>
          </DropdownMenuGroup>
        </DropdownMenuContent>
      </DropdownMenu>
      <SidebarGroup class="p-0 m-0">
        <SidebarGroupContent>
          <NuxtLink
            :to="`/applications/${selectedApplication?.uuid}/knowledge-base`"
            class="hover:bg-sidebar-accent hover:text-sidebar-accent-foreground flex flex-col items-start gap-2 border-b p-2 text-sm leading-tight whitespace-nowrap last:border-b-0"
          >
            <div class="flex w-full items-center space-x-2">
              <BookOpen class="size-4" />
              <div class="">Knowledge Base</div>
            </div>
          </NuxtLink>
          <NuxtLink
            :to="`/applications/${selectedApplication?.uuid}/api-keys-and-widget`"
            class="hover:bg-sidebar-accent hover:text-sidebar-accent-foreground flex flex-col items-start gap-2 border-b p-2 text-sm leading-tight whitespace-nowrap last:border-b-0"
          >
            <div class="flex w-full items-center space-x-2">
              <KeyRound class="size-4" />
              <div>API Keys & Widget</div>
            </div>
          </NuxtLink>
        </SidebarGroupContent>
      </SidebarGroup>
    </SidebarHeader>
    <SidebarContent class="overflow-x-hidden">
      <SidebarGroup class="p-0 m-0">
        <SidebarGroupContent>
          <div class="flex w-full items-center px-4 py-2">
            <MessageSquare class="size-4" />
            <SidebarGroupLabel>Conversations</SidebarGroupLabel>
          </div>
          <NuxtLink
            v-for="chatroom in chatrooms"
            :key="chatroom.uuid"
            :to="`/applications/${selectedApplication.uuid}/messages/${chatroom.uuid}`"
            class="hover:bg-sidebar-accent hover:text-sidebar-accent-foreground flex flex-col items-start gap-2 border-b px-4 py-2 text-sm leading-tight whitespace-nowrap last:border-b-0"
          >
            <div class="flex w-full items-center gap-2">
              <span>{{ ellipsis(chatroom.name, 30) }}</span>
              <span class="ml-auto text-xs">{{
                $dayjs(chatroom.last_message?.created_at).fromNow()
              }}</span>
            </div>
            <span
              class="line-clamp-2 whitespace-break-spaces text-xs"
            >
              {{ chatroom.last_message?.message }}
            </span>
          </NuxtLink>
        </SidebarGroupContent>
      </SidebarGroup>
    </SidebarContent>
  </Sidebar>
</template>
