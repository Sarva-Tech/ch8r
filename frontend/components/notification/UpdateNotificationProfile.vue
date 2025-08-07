<template>
  <BaseSheet
    v-model:open="open"
    title="Update Notification Profiles"
    submit-text="Update"
    :on-submit="updateNotification"
    :disabled="!isFormValid"
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
        :error="errors.profileName"
        @blur="validateProfileName"
      />

      <template v-if="type === 'email'">
        <CustomInput
          v-model="emailValue"
          label="Notification Email"
          placeholder="Enter email"
          :error="errors.emailValue"
          @blur="validateEmail"
        />
      </template>

      <template v-else>
        <CustomInput
          v-model="webhookValue"
          label="Webhook URL"
          placeholder="Enter webhook URL"
          :error="errors.webhookValue"
          @blur="validateWebhook"
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
import { ref, defineExpose, computed } from 'vue'
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

const errors = ref({
  profileName: '',
  emailValue: '',
  webhookValue: ''
})

const isFormValid = computed(() => {
  if (type.value === 'email') {
    return !errors.value.emailValue && emailValue.value
  } else {
    return !errors.value.webhookValue && webhookValue.value
  }
})


const validateProfileName = () => {
  if (profileName.value.length > 50) {
    errors.value.profileName = 'Profile name must be less than 50 characters'
  } else {
    errors.value.profileName = ''
  }
}

const validateEmail = () => {
  if (emailValue.value) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(emailValue.value)) {
      errors.value.emailValue = 'Please enter a valid email address'
    } else {
      errors.value.emailValue = ''
    }
  } else {
    errors.value.emailValue = ''
  }
}

const validateWebhook = () => {
  if (webhookValue.value) {
    const urlRegex = /^(https?:\/\/)[^\s/$.?#].[^\s]*$/
    if (!urlRegex.test(webhookValue.value)) {
      errors.value.webhookValue = 'Please enter a valid URL starting with http:// or https://'
    } else {
      errors.value.webhookValue = ''
    }
  } else {
    errors.value.webhookValue = ''
  }
}

function openSheet(profile: NotificationProfile) {
  currentProfile.value = profile
  type.value = profile.type ?? ''
  profileName.value = profile.name ?? ''
  emailValue.value = profile.config?.email ?? ''
  webhookValue.value = profile.config?.webhookUrl ?? ''
  open.value = true

  errors.value = {
    profileName: '',
    emailValue: '',
    webhookValue: ''
  }
}

async function updateNotification() {
  validateProfileName()
  if (type.value === 'email') {
    validateEmail()
  } else {
    validateWebhook()
  }

  if (!isFormValid.value) {
    toast.error('Please fix the errors in the form')
    return
  }

  if (!currentProfile.value) return

  const payload: Partial<NotificationProfile> = {
    id: currentProfile.value.id,
  }

  if (profileName.value !== currentProfile.value.name) {
    payload.name = profileName.value
  }

  if (type.value !== currentProfile.value.type) {
    payload.type = type.value as NotificationType
  }

  if (type.value === 'email') {
    payload.config = { email: emailValue.value }
  } else {
    payload.config = {
      webhookUrl: encryptWithPublicKey(webhookValue.value)
    }
  }

  try {
    await notificationStore.updateNotificationProfile(payload)
    open.value = false
    toast.success('Profile updated successfully!')
  } catch (err) {
    toast.error(err.message || 'Failed to update profile')
  }
}

defineExpose({ openSheet })
</script>