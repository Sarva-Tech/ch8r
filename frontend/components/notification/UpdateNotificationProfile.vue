<template>
  <SlideOver
    v-model:open="open"
    title="Update Notification Profiles"
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

      <C8Input
        v-model="profileName"
        label="Notification Profile Name"
        placeholder="Enter profile name (optional)"
      />

      <template v-if="type === 'email'">
        <C8Input
          v-model="emailValue"
          label="Notification Email"
          placeholder="Enter email"
        />
      </template>

      <template v-else>
        <C8Input
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

    <template #submitBtn>
      <C8Button
        label="Update"
        :loading="isSubmitting"
        @click="updateNotification"
      />
    </template>
  </SlideOver>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import SlideOver from '~/components/SlideOver.vue'
import C8Button from '~/components/C8Button.vue'
import C8Input from '~/components/C8Input.vue'
import { useNotificationProfileStore } from '~/stores/notificationProfile'
import type { NotificationProfile } from '~/stores/notificationProfile';
import { toast } from 'vue-sonner'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select'
import { showError } from '~/lib/errorHandler'

const open = ref(false)
const isSubmitting = ref(false)
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
  emailValue.value = ''
  webhookValue.value = ''
  open.value = true
}

async function updateNotification() {
  if (!currentProfile.value) return

  isSubmitting.value = true

  const payload: Partial<NotificationProfile> = {}

  if (profileName.value !== currentProfile.value.name) {
    payload.name = profileName.value
  }

  if (type.value === 'email' && emailValue.value) {
    payload.config = { email: emailValue.value }
  } else if (type.value !== 'email' && webhookValue.value) {
    payload.config = { webhookUrl: webhookValue.value }
  }

  try {
    await notificationStore.update(currentProfile.value.uuid!, payload)
    open.value = false
    toast.success('Profile updated successfully!')
  } catch (err: any) {
    showError(err)
  } finally {
    isSubmitting.value = false
  }
}

defineExpose({ openSheet })
</script>
