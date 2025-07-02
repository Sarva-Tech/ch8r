<script setup lang="ts">
import {
  AppWindow,
  LayoutDashboard,
  Command,
  ChevronsUpDown,
  Sparkles,
} from 'lucide-vue-next'

import { h, ref } from 'vue'
import NavUser from '@/components/NavUser.vue'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  type SidebarProps,
  useSidebar,
} from '@/components/ui/sidebar'
import type { Application } from '@/stores/applications'
const { isMobile } = useSidebar()

const applicationsStore = useApplicationsStore()
const chatroomStore = useChatroomStore()
const chatroomMessagesStore = useChatroomMessagesStore()

const applications = computed(() => applicationsStore.applications)
const selectedApplication = computed(() => applicationsStore.selectedApplication)
const chatrooms = computed(() => chatroomStore.chatrooms)

const props = withDefaults(defineProps<SidebarProps>(), {
  collapsible: 'icon',
})

const data = {
  user: {
    name: 'shadcn',
    email: 'm@example.com',
    avatar: '/avatars/shadcn.jpg',
  },
  navMain: [
    {
      title: 'Dashboard',
      url: '/',
      icon: LayoutDashboard,
      isActive: true,
    },
    {
      title: 'Applications',
      url: '/applications',
      icon: AppWindow,
      isActive: false,
    },
  ],
  mails: [
    {
      name: 'William Smith',
      email: 'williamsmith@example.com',
      subject: 'Meeting Tomorrow',
      date: '09:34 AM',
      teaser:
        'Hi team, just a reminder about our meeting tomorrow at 10 AM.\nPlease come prepared with your project updates.',
    },
  ],
}

const activeItem = ref(data.navMain[0])
const mails = ref(data.mails)
const { setOpen } = useSidebar()

function selectApplication(app: Application) {
  applicationsStore.selectApplication(app)
}
</script>

<template>
  <Sidebar
    class="overflow-hidden *:data-[sidebar=sidebar]:flex-row"
    v-bind="props"
  >
    <Sidebar
      collapsible="none"
      class="w-[calc(var(--sidebar-width-icon)+1px)]! border-r"
    >
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" as-child class="md:h-8 md:p-0">
              <a href="#">
                <div
                  class="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg"
                >
                  <Command class="size-4" />
                </div>
                <div class="grid flex-1 text-left text-sm leading-tight">
                  <span class="truncate font-medium">Acme Inc</span>
                  <span class="truncate text-xs">Enterprise</span>
                </div>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent class="px-1.5 md:px-0">
            <SidebarMenu>
              <SidebarMenuItem v-for="item in data.navMain" :key="item.title">
                <SidebarMenuButton
                  :tooltip="h('div', { hidden: false }, item.title)"
                  :is-active="activeItem.title === item.title"
                  class="px-2.5 md:px-2"
                  @click="
                    () => {
                      activeItem = item

                      const mail = data.mails.sort(() => Math.random() - 0.5)
                      mails = mail.slice(
                        0,
                        Math.max(5, Math.floor(Math.random() * 10) + 1),
                      )
                      setOpen(true)
                    }
                  "
                >
                  <component :is="item.icon" />
                  <span>{{ item.title }}</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <NavUser :user="data.user" />
      </SidebarFooter>
    </Sidebar>
    <Sidebar collapsible="none" class="hidden flex-1 md:flex">
      <SidebarHeader class="gap-3.5 border-b">
        <DropdownMenu>
          <DropdownMenuTrigger as-child>
            <SidebarMenuButton
              size="lg"
              class="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
            >
              <Avatar class="h-8 w-8 rounded-lg">
                <AvatarImage src="/avatars/shadcn.jpg" alt="Avt" />
                <AvatarFallback class="rounded-lg"> CN </AvatarFallback>
              </Avatar>
              <div class="grid flex-1 text-left text-sm leading-tight">
                <span class="truncate font-semibold">{{ selectedApplication?.name }}</span>
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
                @click="selectApplication(application)"
              >
                <Sparkles />
                {{ application.name }}
                <DropdownMenuSeparator />
              </DropdownMenuItem>
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenu>
        <SidebarGroup class="px-0">
          <SidebarGroupContent>
            <NuxtLink
              :to="`/applications/${selectedApplication?.uuid}/knowledge-base`"
              class="hover:bg-sidebar-accent hover:text-sidebar-accent-foreground flex flex-col items-start gap-2 border-b p-2 text-sm leading-tight whitespace-nowrap last:border-b-0"
            >
              <div class="flex w-full items-center">
                Knowledge Base
              </div>
            </NuxtLink>
            <a
              href="#"
              class="hover:bg-sidebar-accent hover:text-sidebar-accent-foreground flex flex-col items-start gap-2 border-b p-2 text-sm leading-tight whitespace-nowrap last:border-b-0"
            >
              <div class="flex w-full items-center">
                <span>API & Widgets</span>
              </div>
            </a>

          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup class="px-0">
          <SidebarGroupContent>
            <SidebarGroupLabel>Chat</SidebarGroupLabel>
            <a
              v-for="chatroom in chatrooms"
              :key="chatroom.uuid"
              href="#"
              class="hover:bg-sidebar-accent hover:text-sidebar-accent-foreground flex flex-col items-start gap-2 border-b p-4 text-sm leading-tight whitespace-nowrap last:border-b-0"
              @click="chatroomMessagesStore.selectChatroom(selectedApplication?.uuid!, chatroom.uuid)"
            >
              <div class="flex w-full items-center gap-2">
                <span>{{ chatroom.name }}</span>
                <span class="ml-auto text-xs">{{ chatroom.last_message?.created_at }}</span>
              </div>
              <span
                class="line-clamp-2 w-[260px] whitespace-break-spaces text-xs"
              >
                {{ chatroom.last_message?.message }}
              </span>
            </a>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  </Sidebar>
</template>
