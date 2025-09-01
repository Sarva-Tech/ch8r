<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import UpdateNotificationProfiles from '~/components/notification/UpdateNotificationProfile.vue'
import Ch8rTable from '~/components/C8Table.vue'
import NewNotificationProfile from '~/components/notification/NewNotificationProfile.vue'
import { useNotificationProfileStore } from '~/stores/notificationProfile'
import type { NotificationProfile } from '~/lib/types'
import type { ColumnDef } from '@tanstack/vue-table'

const updateNotification = ref<InstanceType<
  typeof UpdateNotificationProfiles
> | null>(null)
const notificationProfileStore = useNotificationProfileStore()
const isLoading = ref(false)

const profiles = computed(() => notificationProfileStore.profiles)

onMounted(async () => {
  isLoading.value = true
  try {
    await notificationProfileStore.load()
  } catch (err) {
    console.error('Failed to fetch notification profiles:', err)
  } finally {
    isLoading.value = false
  }
})

function handleEdit(profile: NotificationProfile) {
  updateNotification.value?.openSheet(profile)
}

function handleDelete(identifier: number | string) {
  notificationProfileStore.delete(identifier)
}

const columns: ColumnDef<never>[] = [
  {
    accessorKey: 'name',
    header: 'Name',
    cell: (info) => info.getValue(),
  },
  {
    id: 'actions',
    header: 'Actions',
    cell: () => '',
  },
]
</script>

<template>
  <div class="flex flex-col h-screen p-4 pt-[72px] pb-[120px] overflow-y-auto">
    <div class="w-full space-y-4">
      <div class="flex gap-2 items-center py-4">
        <div class="ml-auto">
          <NewNotificationProfile />
        </div>
      </div>
      <Ch8rTable
        :data="profiles"
        :columns="columns"
        :update-fn="handleEdit"
        :delete-fn="handleDelete"
        :expandable="false"
      />
    </div>
    <UpdateNotificationProfiles ref="updateNotification" />
  </div>
</template>