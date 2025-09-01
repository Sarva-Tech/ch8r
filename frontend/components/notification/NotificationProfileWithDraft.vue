<template>
  <div class="space-y-5">
    <form class="space-y-5">
      <FormField v-slot="{ componentField }" name="name">
        <FormItem>
          <FormLabel class="flex items-center">
            <div>
              Profile Name
              <RequiredLabel />
            </div>
          </FormLabel>
          <FormControl>
            <Input v-bind="componentField" placeholder="Production Alerts" />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>
      <C8Select
        :options="notificationTypes"
        :model-value="selectedNotificationType"
        label="Notification Type"
        @update:model-value="(val) => (selectedNotificationType = val)"
      />

      <template v-if="selectedNotificationType">
<!--        <FormField-->
<!--          v-if="selectedNotificationType.value === 'email'"-->
<!--          v-slot="{ componentField }"-->
<!--          name="config.email"-->
<!--        >-->
<!--          <FormItem>-->
<!--            <FormLabel class="flex items-center">-->
<!--              <div>-->
<!--                Email Address-->
<!--                <RequiredLabel />-->
<!--              </div>-->
<!--            </FormLabel>-->
<!--            <FormControl>-->
<!--              <Input-->
<!--                v-bind="componentField"-->
<!--                type="email"-->
<!--                placeholder="user@example.com"-->
<!--                @keyup.enter="addToDraft"-->
<!--              />-->
<!--            </FormControl>-->
<!--            <FormMessage />-->
<!--          </FormItem>-->
<!--        </FormField>-->

        <FormField
          v-if="selectedNotificationType.value !== 'email'"
          v-slot="{ componentField }"
          name="config.webhookUrl"
        >
          <FormItem>
            <FormLabel class="flex items-center">
              <div>
                Webhook URL
                <RequiredLabel />
              </div>
            </FormLabel>
            <FormControl>
              <Input
                v-bind="componentField"
                type="url"
                :placeholder="webhookPlaceholder"
                @keyup.enter="addToDraft"
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        </FormField>
      </template>
    </form>

    <div class="flex justify-end">
      <Button class="w-fit" variant="secondary" @click="addToDraft">
        Add to Draft
      </Button>
    </div>
    <NotificationItemsList
      v-if="draftStore.hasDrafts"
      :items="{
        discord: draftStore.discordItems,
        slack: draftStore.slackItems,
        email: draftStore.emailItems,
      }"
      @remove="removeFromDraft"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Field as FormField } from 'vee-validate'
import C8Select from '~/components/C8Select.vue'
import {
  FormControl,
  FormItem,
  FormLabel,
  FormMessage,
} from '~/components/ui/form'
import RequiredLabel from '~/components/RequiredLabel.vue'
import NotificationItemsList from '~/components/notification/NotificationItemsList.vue'
import { useNotificationProfileStore } from '~/stores/notificationProfile'
import { useNotificationDraftStore } from '~/stores/notificationProfileDraft'
import type { NotificationType } from '~/stores/notificationProfile'

const notificationProfileStore = useNotificationProfileStore()
const draftStore = useNotificationDraftStore()

const notificationTypes = [
  // { label: 'Email', value: 'email' },
  { label: 'Slack', value: 'slack' },
  { label: 'Discord', value: 'discord' },
]

const selectedNotificationType = ref(notificationTypes[0])

const webhookPlaceholder = computed(() => {
  switch (selectedNotificationType.value?.value) {
    case 'slack':
      return 'https://hooks.slack.com/services/...'
    case 'discord':
      return 'https://discord.com/api/webhooks/...'
    default:
      return 'Enter webhook URL'
  }
})

const { defineField, handleSubmit, resetForm } =
  notificationProfileStore.initForm()

const [name] = defineField('name')
const [type] = defineField('type')
const [config_email] = defineField('config.email')
const [config_webhookUrl] = defineField('config.webhookUrl')

const addToDraft = handleSubmit(async (values) => {
  const notificationType = type.value as NotificationType
  const profileName = values.name
  const value =
    notificationType === 'email'
      ? values.config.email
      : values.config.webhookUrl

  if (!profileName || !value) return

  try {
    draftStore.addItem(notificationType, profileName, value)

    resetForm({
      values: {
        name: '',
        type: notificationType,
        config: {
          email: '',
          webhookUrl: '',
        },
      },
    })
  } catch (error) {
    console.error('Failed to add to draft:', error)
  }
})

const removeFromDraft = (id: string) => {
  draftStore.removeItem(id)
}

watch(
  selectedNotificationType,
  (val) => {
    type.value = val.value

    if (val.value === 'email') {
      config_webhookUrl.value = ''
    } else {
      config_email.value = ''
    }
  },
  { immediate: true },
)
</script>
