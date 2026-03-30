<template>
  <SlideOver
    ref="updateNotificationProfileSlide"
    title="Update Notification Profile"
  >
    <form
      class="space-y-5"
      @submit.prevent="updateNotificationProfile"
    >
      <C8APIAlert :api-error="apiError" />

      <FormField name="type">
        <FormItem>
          <FormLabel class="flex items-center">
            Notification Type
          </FormLabel>
          <FormControl>
            <div class="flex items-center gap-2 bg-muted border rounded-md px-3 py-2">
              <component
                :is="getNotificationIcon(form.values.type || '')"
                v-if="getNotificationIcon(form.values.type || '')"
                class="h-4 w-4 flex-shrink-0"
              />
              <span class="text-sm text-muted-foreground">
                {{ typeDisplayName(form.values.type || '') }}
              </span>
            </div>
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

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
            <Input
              v-bind="componentField"
              placeholder="Production Alerts"
            />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

      <FormField
        v-if="requiresWebhook"
        v-slot="{ componentField }"
        name="webhookUrl"
      >
        <FormItem>
          <FormLabel class="flex items-center">
            <div>
              Webhook URL
            </div>
          </FormLabel>
          <FormControl>
            <Input
              v-bind="componentField"
              type="password"
              placeholder="Leave blank to keep existing URL"
            />
          </FormControl>
          <FormDescription>
            Leave the webhook URL field blank to keep the existing URL.
          </FormDescription>
          <FormMessage />
        </FormItem>
      </FormField>

      <FormField
        v-if="form.values.type === 'email'"
        v-slot="{ componentField }"
        name="email"
      >
        <FormItem>
          <FormLabel class="flex items-center">
            <div>
              Email Address
            </div>
          </FormLabel>
          <FormControl>
            <Input
              v-bind="componentField"
              placeholder="Enter email address"
            />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>
    </form>

    <template #submitBtn>
      <C8Button
        label="Update"
        :disabled="disabled"
        :loading="isSubmitting"
        @click="updateNotificationProfile"
      />
    </template>
  </SlideOver>
</template>

<script setup lang="ts">
import SlideOver from '~/components/SlideOver.vue'
import { toast } from 'vue-sonner'
import { toTypedSchema } from '@vee-validate/zod'
import { computed, ref, nextTick } from 'vue'
import RequiredLabel from '~/components/RequiredLabel.vue'
import C8APIAlert from '~/components/C8APIAlert.vue'
import { Input } from '~/components/ui/input'
import {
  FormControl,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from '~/components/ui/form'
import { useForm } from 'vee-validate'
import { z } from 'zod'
import { useApiErrorHandling } from '~/composables/useApiErrorHandling'
import { useNotificationProviderIcon } from '~/composables/useNotificationProviderIcon'
import type { NotificationProfile } from '~/stores/notificationProfile'

const updateNotificationProfileSlide = ref<InstanceType<typeof SlideOver> | null>(null)
const notificationProfileStore = useNotificationProfileStore()
const { apiError, handleError, clearError } = useApiErrorHandling()

const requiresWebhook = computed(() => {
  const type = form.values.type
  return type === 'slack' || type === 'discord'
})

function getNotificationIcon(type: string) {
  return useNotificationProviderIcon(type).value
}

function typeDisplayName(type: string) {
  switch (type?.toLowerCase()) {
    case 'slack':
      return 'Slack'
    case 'discord':
      return 'Discord'
    case 'email':
      return 'Email'
    default:
      return type?.charAt(0).toUpperCase() + type?.slice(1)
  }
}

const schema = z.object({
  id: z.number().optional(),
  uuid: z.string().optional(),
  name: z.string().nonempty({ message: 'Required' }).min(1).max(255),
  type: z.string().nonempty({ message: 'Required' }),
  webhookUrl: z.string().optional(),
  email: z.string().email().optional().or(z.literal('')),
}).superRefine((data, ctx) => {
  if ((data.type === 'slack' || data.type === 'discord') && data.webhookUrl) {
    if (!z.string().url().safeParse(data.webhookUrl).success) {
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
    id: undefined,
    uuid: '',
    name: '',
    type: '',
    webhookUrl: '',
    email: '',
  },
})

const { isSubmitting, meta, setValues } = form

function open(profile: NotificationProfile) {
  clearError()

  const email = profile.type === 'email' ? profile.config?.email || '' : ''

  setValues({
    id: profile.id,
    uuid: profile.uuid,
    name: profile.name,
    type: profile.type,
    webhookUrl: '',
    email,
  })

  nextTick(() => {
    updateNotificationProfileSlide.value?.openSlide()
  })
}

defineExpose({
  open,
})

const updateNotificationProfile = form.handleSubmit(async (values) => {
  clearError()

  const id = values.id || values.uuid
  if (!id) return

  const payload: Partial<NotificationProfile> = {
    name: values.name,
  }

  if (values.type === 'email' && values.email) {
    payload.config = { email: values.email }
  }
  else if ((values.type === 'slack' || values.type === 'discord') && values.webhookUrl) {
    payload.config = { webhookUrl: values.webhookUrl }
  }

  try {
    await notificationProfileStore.update(id, payload)
    updateNotificationProfileSlide.value?.closeSlide()
    toast.success('Notification profile updated')
  }
  catch (error: unknown) {
    handleError(error, form)
  }
})

const disabled = computed(() => !meta.value.valid)
</script>
