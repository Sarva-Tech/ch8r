<template>
  <div class="flex flex-col h-screen">
    <div class="overflow-y-auto pt-[72px] pb-[120px] p-4">
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
</template>

<script setup lang="ts">
import { ref } from 'vue'
import BaseSheet from '~/components/BaseSheet.vue'
import { Button } from '~/components/ui/button'
import NotificationProfileForm from '~/components/notification/NotificationProfileForm.vue'
import { useNotificationProfileStore } from '~/stores/notificationProfile'
import { useNotificationDraftStore } from '~/stores/notificationProfileDraft'
import { toast } from 'vue-sonner'
import { encryptWithPublicKey, PUBLIC_KEY } from '~/utils/encryption'


const notificationProfileStore = useNotificationProfileStore()
const notificationDraftStore = useNotificationDraftStore()
const loading = ref(false)


const handleSubmit = async () => {
  if (loading.value) return
  if (!notificationDraftStore.hasDrafts) return

  loading.value = true

  try {
    const payload = [
      ...notificationDraftStore.discordItems.map(item => ({
        name: item.profileName,
        type: 'discord' as const,
        config: {
          webhookUrl: encryptWithPublicKey(item.value, PUBLIC_KEY),
        }
      })),
      ...notificationDraftStore.slackItems.map(item => ({
        name: item.profileName,
        type: 'slack' as const,
        config: {
          webhookUrl: encryptWithPublicKey(item.value, PUBLIC_KEY),
        }
      })),
      ...notificationDraftStore.emailItems.map(item => ({
        name: item.profileName,
        type: 'email' as const,
        config: {
          email: item.value
        }
      }))
    ]

    await notificationProfileStore.createBulkNotificationProfiles(payload)
    notificationDraftStore.clear()
    toast.success(`Successfully created ${payload.length} notification profiles`)
  } catch (error) {
    toast.error(error.message || 'Failed to create notification profiles')
  } finally {
    loading.value = false
  }
}

</script>