<template>
  <SlideOver
    ref="newNotificationSlideOver"
    title="Add Notification Profiles"
  >
    <template #trigger>
      <C8Button label="Add Notification Profile" />
    </template>
    <form class="space-y-5" @submit.prevent="createNewNotification">
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

      <FormField
        v-if="selectedNotificationType"
        v-slot="{ componentField }"
        name="webhookUrl"
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
            />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>
    </form>

    <template #submitBtn>
      <C8Button
        label="Create"
        :disabled="disabled"
        :loading="isSubmitting"
        @click="createNewNotification"
      />
    </template>
  </SlideOver>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import SlideOver from '~/components/SlideOver.vue'
import { toast } from 'vue-sonner'
import { useNotificationProfileStore } from '~/stores/notificationProfile'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import { z } from 'zod'
import { FormControl, FormItem, FormLabel, FormMessage } from '~/components/ui/form'
import RequiredLabel from '~/components/RequiredLabel.vue'
import C8Select from '~/components/C8Select.vue'
import { setBackendErrors } from '~/lib/utils'

const newNotificationSlideOver = ref<InstanceType<typeof SlideOver> | null>(
  null,
)

const schema = z.object({
  name: z.string().nonempty({ message: 'Required' }).min(1).max(255),
  type: z.string().nonempty({ message: 'Required' }).min(1).max(255),
  email: z.string().optional(),
  webhookUrl: z.string().url().optional(),
  }).superRefine((data, ctx) => {
  if (data.type === 'email' && !data.email) {
    ctx.addIssue({
      path: ['email'],
      code: z.ZodIssueCode.custom,
      message: 'Email is required',
    })
  }

  if ((data.type === 'slack' || data.type === 'discord') && !data.webhookUrl) {
    ctx.addIssue({
      path: ['webhookUrl'],
      code: z.ZodIssueCode.custom,
      message: 'Webhook URL is required',
    })
  }
})

const form = useForm({
  validationSchema: toTypedSchema(schema),
  initialValues: {
    name: '',
    type: '',
    email: '',
    webhookUrl: ''
  },
})

const notificationProfileStore = useNotificationProfileStore()

const { isSubmitting, meta, defineField } = form

const notificationTypes = [
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

const [type] = defineField('type')
const [config_webhookUrl] = defineField('webhookUrl')

const createNewNotification = form.handleSubmit(async (values) => {
  try {
    await notificationProfileStore.create(values)
    newNotificationSlideOver.value?.closeSlide()
    toast.success(`Notification profile created`)
  } catch (e: unknown) {
    setBackendErrors(form, e.errors)
  }
})

watch(
  selectedNotificationType,
  (val) => {
    type.value = val.value
    config_webhookUrl.value = ''
  },
  { immediate: true },
)


const disabled = computed(() => {
  return meta.value.valid
})
</script>
