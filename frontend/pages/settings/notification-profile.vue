<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import UpdateNotificationProfiles from '~/components/notification/UpdateNotificationProfile.vue'
import C8Item from '~/components/C8Item.vue'
import NewNotificationProfile from '~/components/notification/NewNotificationProfile.vue'
import { useNotificationProfileStore } from '~/stores/notificationProfile'
import { ItemDescription } from '~/components/ui/item'
import { DropdownMenuItem } from '@/components/ui/dropdown-menu'
import { Bell, PencilLine, Trash, MessageSquare, Slack, BellOff } from 'lucide-vue-next'
import C8EmptyState from '~/components/C8EmptyState.vue'
import C8Dialog from '~/components/C8Dialog.vue'
import { toast } from 'vue-sonner'

const updateNotification = ref<InstanceType<
  typeof UpdateNotificationProfiles
> | null>(null)
const isDeleteDialogOpen = ref(false)
const profileToDelete = ref<any>(null)
const notificationProfileStore = useNotificationProfileStore()
const user = useUserStore()

const isLoading = ref(false)

const profiles = computed(() =>
  notificationProfileStore.profiles.map((profile) => ({
    ...profile,
    canDelete: profile.owner === user.authUser.id,
    canUpdate: profile.owner === user.authUser.id,
  }))
)

onMounted(async () => {
  isLoading.value = true
  try {
    await notificationProfileStore.load()
  } catch {
    toast.error('Failed to load notification profiles')
  } finally {
    isLoading.value = false
  }
})

function getNotificationIcon(type: string) {
  switch (type.toLowerCase()) {
    case 'slack':
      return Slack
    case 'discord':
      return MessageSquare
    case 'email':
      return Bell
    default:
      return Bell
  }
}

function canManageProfile(profile: any) {
  return user.authUser?.id === profile.owner
}

function profileTypeDisplayName(type: string) {
  switch (type.toLowerCase()) {
    case 'slack':
      return 'Slack'
    case 'discord':
      return 'Discord'
    default:
      return type.charAt(0).toUpperCase() + type.slice(1)
  }
}

function handleEdit(profile: any) {
  updateNotification.value?.openSheet(profile)
}

function openDeleteDialog(profile: any) {
  profileToDelete.value = profile
  isDeleteDialogOpen.value = true
}

async function confirmDelete() {
  if (profileToDelete.value) {
    try {
      await notificationProfileStore.delete(profileToDelete.value.uuid)
      toast.success('Notification profile deleted')
    } catch {
      toast.error('Failed to delete notification profile')
    }
    isDeleteDialogOpen.value = false
    profileToDelete.value = null
  }
}
</script>

<template>
  <div class="flex flex-col h-screen p-4 pt-[72px] pb-[120px] overflow-y-auto">
    <div class="w-full space-y-2">
      <div class="flex gap-2 items-center py-4">
        <div class="ml-auto">
          <NewNotificationProfile />
        </div>
      </div>

      <C8EmptyState
        v-if="!isLoading && profiles.length === 0"
        :icon="BellOff"
        title="No notification profiles yet"
        description="Create a profile to start receiving alerts via email, Slack, or Discord."
      />

      <C8Item
        v-for="(profile, index) in profiles"
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
                <div>{{ profileTypeDisplayName(profile.type) }}</div>
              </div>
            </div>
          </ItemDescription>
        </template>

        <template #dropdown>
          <DropdownMenuItem
            :disabled="!canManageProfile(profile)"
            @click="handleEdit(profile)"
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
      <UpdateNotificationProfiles ref="updateNotification" />
    </div>

    <C8Dialog
      v-model:open="isDeleteDialogOpen"
      title="Delete Notification Profile"
      :item-name="profileToDelete?.name || 'this notification profile'"
      confirm-text="Delete"
      destructive
      @confirm="confirmDelete"
    >
      <template #description>
        <div>
          Are you sure you want to delete <span class="font-bold">{{ profileToDelete?.name || 'this notification profile' }}</span>?
        </div>
      </template>
    </C8Dialog>
  </div>
</template>
