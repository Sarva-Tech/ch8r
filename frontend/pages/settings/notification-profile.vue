<template>
  <div class="flex flex-col min-h-0 flex-1 p-4 pt-[72px] pb-[120px] overflow-y-auto">
    <div class="w-full space-y-2">
      <div class="flex gap-2 items-center py-4">
        <div class="ml-auto">
          <NewNotificationProfile />
        </div>
      </div>

      <C8Item
        v-for="(profile, index) in notificationProfiles"
        :key="index"
        :icon="getNotificationIcon(profile.type)"
        container-class="w-full"
        item-class="w-full"
      >
        <template #title>
          {{ profile.name }}
        </template>
        <template #details>
          <ItemDescription>
            <div class="inline-flex space-x-3">
              <div class="flex items-center space-x-1">
                <Bell class="w-4 h-4" />
                <div>{{ typeDisplayName(profile.type) }}</div>
              </div>
              <div
                v-if="profile.config?.email"
                class="flex items-center space-x-1"
              >
                <Mail class="w-4 h-4" />
                <div>{{ profile.config.email }}</div>
              </div>
            </div>
          </ItemDescription>
        </template>

        <template #dropdown>
          <DropdownMenuItem
            :disabled="!canManageProfile(profile)"
            @click="updateProfile(profile)"
          >
            <PencilLine class="h-4 w-4" />
            Update
          </DropdownMenuItem>
          <DropdownMenuItem
            class="text-destructive"
            :disabled="!canManageProfile(profile)"
            @click="openDeleteDialog(profile)"
          >
            <Trash class="h-4 w-4 text-destructive" />
            Delete
          </DropdownMenuItem>
        </template>
      </C8Item>

      <C8Empty
        v-if="!loading && notificationProfiles.length === 0"
        :icon="BellOff"
        title="No notification profiles configured"
        description="Add a new notification profile"
      >
        <template #action>
          <NewNotificationProfile />
        </template>
      </C8Empty>

      <UpdateNotificationProfile ref="updateNotificationProfileSlide" />
      <C8Dialog
        v-model:open="isDeleteDialogOpen"
        :title="`Delete Notification Profile ${profileToDelete?.name}`"
        :confirm-text="'Delete'"
        :destructive="true"
        @confirm="confirmDelete"
      >
        <template #description>
          <div>
            Are you sure you want to delete the notification profile <span class="font-bold">{{ profileToDelete?.name }}</span>?
          </div>
        </template>
      </C8Dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import NewNotificationProfile from '~/components/notification/NewNotificationProfile.vue'
import UpdateNotificationProfile from '~/components/notification/UpdateNotificationProfile.vue'
import C8Dialog from '~/components/C8Dialog.vue'
import C8Item from '~/components/C8Item.vue'
import { ItemDescription } from '~/components/ui/item'
import { DropdownMenuItem } from '@/components/ui/dropdown-menu'
import { useNotificationProviderIcon } from '~/composables/useNotificationProviderIcon'
import { toast } from 'vue-sonner'
import { PencilLine, Trash, Bell, Mail, BellOff } from 'lucide-vue-next'
import C8Empty from '~/components/C8Empty.vue'

const updateNotificationProfileSlide = ref<InstanceType<typeof UpdateNotificationProfile> | null>(null)
const isDeleteDialogOpen = ref(false)
const profileToDelete = ref<NotificationProfile | null>(null)

const notificationProfileStore = useNotificationProfileStore()
const user = useUserStore()

const loading = ref(false)

function getNotificationIcon(type: string) {
  return useNotificationProviderIcon(type).value
}

function canManageProfile(profile: NotificationProfile) {
  return user.authUser?.id === profile.owner
}

function typeDisplayName(type: string) {
  switch (type?.toLowerCase()) {
    case 'slack':
      return 'Slack'
    case 'discord':
      return 'Discord'
    case 'email':
      return 'Email'
    default:
      return type?.charAt(0).toUpperCase() + type?.slice(1)
  }
}

onMounted(async () => {
  loading.value = true
  try {
    await notificationProfileStore.load()
  }
  catch (e: unknown) {
    console.error(e)
    toast.error('Failed to load notification profiles')
  }
  finally {
    loading.value = false
  }
})

const notificationProfiles = computed(() => notificationProfileStore.profiles)

function updateProfile(profile: NotificationProfile) {
  updateNotificationProfileSlide.value?.open(profile)
}

function openDeleteDialog(profile: NotificationProfile) {
  profileToDelete.value = profile
  isDeleteDialogOpen.value = true
}

function confirmDelete() {
  if (profileToDelete.value) {
    deleteProfile(profileToDelete.value)
  }
}

function deleteProfile(profile: NotificationProfile) {
  const id = profile.id || profile.uuid
  if (!id) return

  notificationProfileStore.delete(id).then(() => {
    toast.success('Notification profile deleted')
  }).catch((e) => {
    console.error(e)
    toast.error('Failed to delete notification profile')
  })
}
</script>
