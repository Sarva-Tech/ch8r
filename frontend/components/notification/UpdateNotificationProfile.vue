<template>
  <BaseSheet
    v-model:open="open"
    title="Update Notification Profiles"
    submit-text="Update"
    :on-submit="updateNotification"
  >
    <div class="space-y-4">
      <div>
        <label class="text-sm font-medium">Select Notification Type</label>
        <Select v-model="type" class="w-full" disabled>
          <SelectTrigger class="w-full">
            <SelectValue placeholder="Choose type..." />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="discord">Discord</SelectItem>
            <SelectItem value="slack">Slack</SelectItem>
            <SelectItem value="email">Email</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <CustomInput
        v-model="profileName"
        label="Notification Profile Name"
        placeholder="Enter profile name (optional)"
      />

      <template v-if="type === 'email'">
        <CustomInput
          v-model="emailValue"
          label="Notification Email"
          placeholder="Enter email"
        />
      </template>

      <template v-else>
        <CustomInput
          v-model="webhookValue"
          label="Webhook URL"
          placeholder="Enter webhook URL (leave empty to keep current)"
        />
        <p class="text-xs text-muted-foreground">
          We are intentionally not showing the existing webhook URL for security reasons.
          If you want to update it, please enter the new webhook URL here.
        </p>
      </template>
    </div>
  </BaseSheet>
</template>

<script setup lang="ts">
import { ref, defineExpose } from 'vue'
import BaseSheet from '~/components/BaseSheet.vue'
import { useNotificationProfileStore } from '~/stores/notificationProfile'
import type { NotificationProfile } from '~/stores/notificationProfile';
import { toast } from 'vue-sonner'

const open = ref(false)
const currentProfile = ref<null | { [key: string]: any }>(null)
const notificationStore = useNotificationProfileStore()

const type = ref('')
const profileName = ref('')
const emailValue = ref('')
const webhookValue = ref('')

function openSheet(profile: NotificationProfile) {
  currentProfile.value = profile
  type.value = profile.type ?? ''
  profileName.value = profile.name ?? ''
  emailValue.value = profile.config?.email ?? ''
  webhookValue.value = ''
  open.value = true
}

async function updateNotification() {
  if (!currentProfile.value) return

  const payload: Partial<NotificationProfile> = {
    id: currentProfile.value.id,
    name: profileName.value,
  }

  if (type.value === 'email' && emailValue.value) {
    payload.config = { email: emailValue.value }
  } else if (type.value !== 'email' && webhookValue.value) {
    payload.config = { webhookUrl: encryptWithPublicKey(webhookValue.value) }
  }

  try {
    await notificationStore.updateNotificationProfile(payload)
    open.value = false
    await notificationStore.fetchNotificationProfiles();
    toast.success('Profile updated successfully!')
  } catch (err) {
    toast.error(err.message || 'Failed to update profile')
  }
}
defineExpose({ openSheet })
</script>