<template>
  <SlideOver
    ref="newNotificationSlide"
    title="Add Notification Profile"
  >
    <template #trigger>
      <C8Button
        label="Add Notification Profile"
        :icon="Plus"
        @click="openSlideWithReset"
      />
    </template>

    <form
      class="space-y-5"
      @submit.prevent="createNotificationProfile"
    >
      <C8APIAlert :api-error="apiError" />

      <FormField
        v-slot="{ componentField }"
        name="name"
      >
        <FormItem>
          <FormLabel class="flex items-center">
            <div>
              Profile Name
              <RequiredLabel />
            </div>
          </FormLabel>
          <FormControl>
            <div class="flex gap-2">
              <Input
                v-bind="componentField"
                placeholder="Production Alerts"
                class="flex-1"
              />
              <C8Button
                variant="outline"
                size="icon"
                type="button"
                @click="generateUniqueProfileName"
              >
                <Sparkles class="h-4 w-4" />
              </C8Button>
            </div>
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

      <FormField
        v-slot="{ componentField }"
        name="type"
      >
        <FormItem>
          <FormLabel class="flex items-center">
            <div>
              Notification Type
              <RequiredLabel />
            </div>
          </FormLabel>
          <C8Select
            :options="notificationTypes"
            v-bind="componentField"
          />
          <FormMessage />
        </FormItem>
      </FormField>

      <FormField
        v-slot="{ componentField }"
        name="webhookUrl"
      >
        <FormItem>
          <FormLabel class="flex items-center">
            <div>
              Webhook URL
              <RequiredLabel v-if="requiresWebhook" />
            </div>
          </FormLabel>
          <FormControl>
            <Input
              v-bind="componentField"
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
        @click="createNotificationProfile"
      />
    </template>
  </SlideOver>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import SlideOver from '~/components/SlideOver.vue'
import { toast } from 'vue-sonner'
import { toTypedSchema } from '@vee-validate/zod'
import { FormControl, FormItem, FormLabel, FormMessage } from '~/components/ui/form'
import RequiredLabel from '~/components/RequiredLabel.vue'
import C8Select from '~/components/C8Select.vue'
import C8APIAlert from '~/components/C8APIAlert.vue'
import { z } from 'zod'
import { useForm } from 'vee-validate'
import { useApiErrorHandling } from '~/composables/useApiErrorHandling'
import { Plus, Sparkles } from 'lucide-vue-next'
import { useUniqueName } from '~/composables/useUniqueName'

const newNotificationSlide = ref<InstanceType<typeof SlideOver> | null>(null)
const notificationProfileStore = useNotificationProfileStore()
const { apiError, handleError, clearError } = useApiErrorHandling()
const { generateShortUniqueName } = useUniqueName()

const notificationTypes = [
  { label: 'Slack', value: 'slack' },
  { label: 'Discord', value: 'discord' },
  { label: 'Email', value: 'email' },
]

const requiresWebhook = computed(() => {
  const type = form.values.type
  return type === 'slack' || type === 'discord'
})

const webhookPlaceholder = computed(() => {
  switch (form.values.type) {
    case 'slack':
      return 'https://hooks.slack.com/services/...'
    case 'discord':
      return 'https://discord.com/api/webhooks/...'
    default:
      return 'Enter webhook URL'
  }
})

const schema = z.object({
  name: z.string().nonempty({ message: 'Required' }).min(1).max(255),
  type: z.string().nonempty({ message: 'Required' }),
  webhookUrl: z.string().optional(),
}).superRefine((data, ctx) => {
  if (data.type === 'slack' || data.type === 'discord') {
    if (!data.webhookUrl || !data.webhookUrl.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Webhook URL is required for this notification type',
        path: ['webhookUrl'],
      })
    }
    else if (!z.string().url().safeParse(data.webhookUrl).success) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Please enter a valid URL',
        path: ['webhookUrl'],
      })
    }
  }
})

const form = useForm({
  validationSchema: toTypedSchema(schema),
  initialValues: {
    name: '',
    type: 'slack',
    webhookUrl: '',
  },
})

const { isSubmitting, meta } = form

const resetFormToDefaults = () => {
  form.resetForm({
    values: {
      name: generateShortUniqueName('Profile'),
      type: 'slack',
      webhookUrl: '',
    },
  })
}

const generateUniqueProfileName = () => {
  const uniqueName = generateShortUniqueName('Profile')
  form.setFieldValue('name', uniqueName)
}

const openSlideWithReset = () => {
  clearError()
  resetFormToDefaults()
  newNotificationSlide.value?.openSlide()
}

const createNotificationProfile = form.handleSubmit(async (values) => {
  clearError()

  const payload: Record<string, unknown> = {
    name: values.name,
    type: values.type,
    config: {},
  }

  if (values.type === 'email') {
    payload.config = { email: values.webhookUrl }
  }
  else if (values.webhookUrl) {
    payload.config = { webhookUrl: values.webhookUrl }
  }

  try {
    await notificationProfileStore.create(payload)
    newNotificationSlide.value?.closeSlide()
    toast.success('Notification profile created')
  }
  catch (error: unknown) {
    handleError(error, form)
  }
})

const disabled = computed(() => !meta.value.valid)
</script>
