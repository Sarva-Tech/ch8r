<script setup lang="ts">
import {
  ChevronsUpDown,
  LogOut,
  Settings
} from 'lucide-vue-next'

import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar'
import { getGravatarUrl } from '~/lib/avatar'
import { useLogout } from '~/composables/useLogout'

defineProps<{
  user: {
    name: string
    email: string
  }
}>()

const { logout } = useLogout()

function getInitials(name: string): string {
  console.log(name)
  if (!name) return '??'
  return name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}
</script>

<template>
  <SidebarMenu>
    <SidebarMenuItem>
      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <SidebarMenuButton
            size="sm"
            class="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground p-4"
          >
            <Avatar class="h-5 w-5 rounded-md">
              <AvatarImage :src="getGravatarUrl(user.email)" :alt="user.name" />
              <AvatarFallback class="rounded-md">
                {{ getInitials(user.name) }}
              </AvatarFallback>
            </Avatar>
            <div class="grid flex-1 text-left text-sm leading-tight">
              <span class="truncate font-medium">{{ user.name }}</span>
              <span class="truncate text-xs">{{ user.email }}</span>
            </div>
            <ChevronsUpDown class="ml-auto size-4" />
          </SidebarMenuButton>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          class="w-[--reka-dropdown-menu-trigger-width] min-w-56 rounded-lg"
          side="bottom"
          align="end"
          :side-offset="4"
        >
          <DropdownMenuItem @click="$router.push('/settings')">
            <Settings />
            Settings
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem class="text-destructive group" @click="logout">
            <LogOut class="text-destructive group-hover:text-destructive-foreground"/>
            Log out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </SidebarMenuItem>
  </SidebarMenu>
</template>
