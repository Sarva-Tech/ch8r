<template>
  <div class="space-y-4">
    <NotificationTypeSelect v-model="selectedType" />

    <div v-if="selectedType" class="space-y-4">
      <C8Input
        v-model="profileName"
        label="Notification Profile Name"
        placeholder="Enter profile name"
        required
        :error="profileNameError"
      />

      <C8Input
        v-model="inputValue"
        :label="inputLabel"
        :placeholder="inputPlaceholder"
        :type="inputType"
        required
        :error="inputValueError"
        @keyup.enter="addItem"
      />

      <div class="flex justify-end">
        <Button class="w-fit" variant="secondary" @click="addItem">
          Add
        </Button>
      </div>
    </div>

    <NotificationItemsList
      :items="{
        discord: store.discordItems,
        slack: store.slackItems,
        email: store.emailItems
      }"
      @remove="removeItem"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useNotificationDraftStore } from '~/stores/notificationProfileDraft'
import C8Input from '~/components/C8Input.vue'
import NotificationTypeSelect from '~/components/notification/NotificationTypeSelect.vue'
import NotificationItemsList from '~/components/notification/NotificationItemsList.vue'

const store = useNotificationDraftStore()

const selectedType = ref<NotificationType | ''>('')
const profileName = ref('')
const inputValue = ref('')
const profileNameError = ref('')
const inputValueError = ref('')

const inputLabel = computed(() => {
  switch (selectedType.value) {
    case 'discord': return 'Discord Webhook URL'
    case 'slack': return 'Slack Webhook URL'
    case 'email': return 'Email Address'
    default: return ''
  }
})

const inputPlaceholder = computed(() => {
  switch (selectedType.value) {
    case 'discord':
    case 'slack': return 'Enter webhook URL'
    case 'email': return 'Enter email address'
    default: return ''
  }
})

const inputType = computed(() => {
  return selectedType.value === 'email' ? 'email' : 'url'
})

const validateInputs = () => {
  let isValid = true

  if (!profileName.value.trim()) {
    profileNameError.value = 'Profile name is required'
    isValid = false
  } else {
    profileNameError.value = ''
  }

  if (!inputValue.value.trim()) {
    inputValueError.value = `${inputLabel.value} is required`
    isValid = false
  } else if (selectedType.value === 'email' && !isValidEmail(inputValue.value)) {
    inputValueError.value = 'Please enter a valid email address'
    isValid = false
  } else if ((selectedType.value === 'discord' || selectedType.value === 'slack') &&
    !isValidUrl(inputValue.value)) {
    inputValueError.value = 'Please enter a valid URL'
    isValid = false
  } else {
    inputValueError.value = ''
  }

  return isValid
}

const isValidEmail = (email: string) => {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

const isValidUrl = (url: string) => {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

const addItem = () => {
  if (!selectedType.value || !validateInputs()) return
  store.addItem(selectedType.value as NotificationType, profileName.value.trim(), inputValue.value.trim())
  inputValue.value = ''
  profileName.value = ''
}

const removeItem = (id: string) => {
  store.removeItem(id)
}

watch(selectedType, () => {
  inputValue.value = ''
  profileName.value = ''
  profileNameError.value = ''
  inputValueError.value = ''
})
</script>
