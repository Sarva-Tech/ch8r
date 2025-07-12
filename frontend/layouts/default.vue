<script setup lang="ts">
import AppSidebar from '@/components/AppSidebar.vue'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb'
import { Separator } from '@/components/ui/separator'
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from '@/components/ui/sidebar'

const appStore = useApplicationsStore()
const chatroomStore = useChatroomStore()
const userStore = useUserStore()

const authUser = useCookie<User>('auth_user')

if (authUser.value?.id) {
  userStore.setUser(authUser.value)
}

const selectedApp = computed(() => appStore.selectedApplication)

onMounted(async () => {
  if (!appStore.applications.length) {
    await appStore.fetchApplications()
  }
})

watch(
  selectedApp,
  async (newApp) => {
    if (newApp?.uuid) {
      await chatroomStore.fetchChatrooms(newApp.uuid)
    }
  },
  { immediate: true }
)
</script>

<template>
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
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem class="hidden md:block">
              <BreadcrumbLink href="#"> All Inboxes </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator class="hidden md:block" />
            <BreadcrumbItem>
              <BreadcrumbPage>Inbox</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
      </header>
      <div class="flex flex-col h-screen">
        <NuxtPage />
      </div>
    </SidebarInset>
  </SidebarProvider>
</template>
