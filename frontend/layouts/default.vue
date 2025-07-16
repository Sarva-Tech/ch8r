<script setup lang="ts">
import AppSidebar from '@/components/AppSidebar.vue'
import { Separator } from '@/components/ui/separator'
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from '@/components/ui/sidebar'
import Toaster from '@/components/ui/sonner/Sonner.vue'
import 'vue-sonner/style.css'
import ThemePopover from '~/components/ThemePopover.vue'

const themeStore = useThemeStore()
const userStore = useUserStore()
const appStore = useApplicationsStore()
const chatroomStore = useChatroomStore()

const authUser = useCookie<User>('auth_user')

const selectedApp = computed(() => appStore.selectedApplication)

if (authUser.value?.id) {
  userStore.setUser(authUser.value)
}

watch(
  selectedApp,
  async (newApp) => {
    if (newApp?.uuid) {
      await chatroomStore.fetchChatrooms(newApp.uuid)
    }
  },
  { immediate: true },
)

onMounted(() => {
  themeStore.fetchAndApplyTheme()
})
</script>

<template class="theme-red">
  <SidebarProvider
    :style="{
      '--sidebar-width': '350px',
    }"
  >
    <AppSidebar />
    <SidebarInset>
      <header
        class="bg-background fixed w-full top-0 flex shrink-0 items-center gap-2 border-b p-4"
      >
        <SidebarTrigger class="-ml-1" />
        <Separator
          orientation="vertical"
          class="mr-2 data-[orientation=vertical]:h-4"
        />
        <ThemePopover />
      </header>
      <div class="flex flex-col h-screen">
        <NuxtPage />
      </div>
    </SidebarInset>
    <ClientOnly>
      <Toaster />
    </ClientOnly>
  </SidebarProvider>
</template>
