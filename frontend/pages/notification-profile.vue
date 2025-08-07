<template>
  <div class="flex flex-col h-screen">
    <div class="overflow-y-auto pt-[72px] pb-[120px] p-4">
      <div class="flex gap-2 items-center py-4">
        <div class="ml-auto">
          <BaseSheet
            title="Add Notification profiles"
            :disabled="!notificationDraftStore.hasDrafts"
            :loading="loading"
            @submit="handleSubmit"
          >
            <template #trigger>
              <Button>Add Notification Profile</Button>
            </template>

            <NotificationProfileForm ref="notificationForm" />
          </BaseSheet>
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

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import BaseSheet from '~/components/BaseSheet.vue'
import { Button } from '~/components/ui/button'
import NotificationProfileForm from '~/components/notification/NotificationProfileForm.vue'
import { useNotificationProfileStore } from '~/stores/notificationProfile'
import { useNotificationDraftStore } from '~/stores/notificationProfileDraft'
import { toast } from 'vue-sonner'
import UpdateNotificationProfiles from '~/components/notification/UpdateNotificationProfile.vue'
import { encryptWithPublicKey } from '~/utils/encryption'
import type { ColumnDef } from '@tanstack/vue-table'


const updateNotification = ref<InstanceType<typeof UpdateNotificationProfiles> | null>(null)


const notificationProfileStore = useNotificationProfileStore()
const notificationDraftStore = useNotificationDraftStore()
const loading = ref(false)

const profiles = computed(() => notificationProfileStore.profiles)

onMounted(async () => {
  loading.value = true
  try {
    await notificationProfileStore.fetchNotificationProfiles()
  } catch (err) {
    console.log('error')
  } finally {
    loading.value = false
  }
})

const handleEdit = (profile: any) => {
  updateNotification.value?.openSheet(profile)
}

const handleDelete = (identifier: number | string) => {
  console.log('Deleting profile with ID or UUID:', identifier)
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
const handleSubmit = async () => {
  if (loading.value) return
  if (!notificationDraftStore.hasDrafts) return

  loading.value = true

  try {
    const payload = [
      ...notificationDraftStore.discordItems.map((item) => ({
        name: item.profileName,
        type: 'discord' as const,
        config: {
          webhookUrl: encryptWithPublicKey(item.value),
        },
      })),
      ...notificationDraftStore.slackItems.map((item) => ({
        name: item.profileName,
        type: 'slack' as const,
        config: {
          webhookUrl: encryptWithPublicKey(item.value),
        },
      })),
      ...notificationDraftStore.emailItems.map((item) => ({
        name: item.profileName,
        type: 'email' as const,
        config: {
          email: item.value,
        },
      })),
    ]

    await notificationProfileStore.createBulkNotificationProfiles(payload)
    notificationDraftStore.clear()
    toast.success(
      `Successfully created ${payload.length} notification profiles`,
    )
  } catch (error) {
    toast.error(error.message || 'Failed to create notification profiles')
  } finally {
    loading.value = false
  }
}
</script>
