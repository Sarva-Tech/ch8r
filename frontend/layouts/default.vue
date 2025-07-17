<script setup lang="ts">
import AppSidebar from '@/components/AppSidebar.vue'
import {
  SidebarProvider,
} from '@/components/ui/sidebar'
import Toaster from '@/components/ui/sonner/Sonner.vue'
import 'vue-sonner/style.css'

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

<template>
  <SidebarProvider>
    <AppSidebar />
    <ClientOnly>
      <Toaster />
    </ClientOnly>
  </SidebarProvider>
</template>
