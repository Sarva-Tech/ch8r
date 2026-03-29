<template>
  <SlideOver
    ref="updateIntegrationSlide"
    title="Update Integration"
  >
    <form
      class="space-y-5"
      @submit.prevent="updateIntegration"
    >
      <C8APIAlert :api-error="apiError" />

      <FormField name="provider">
        <FormItem>
          <FormLabel>Provider</FormLabel>
          <FormControl>
            <div class="flex items-center gap-2 bg-muted border rounded-md px-3 py-2">
              <component
                :is="providerIcon"
                v-if="providerIcon"
                class="h-4 w-4"
              />
              <span class="text-sm text-muted-foreground">
                {{ providerLabel }}
              </span>
            </div>
          </FormControl>
        </FormItem>
      </FormField>

      <FormField
        v-slot="{ componentField }"
        name="name"
      >
        <FormItem>
          <FormLabel class="flex items-center">
            <div>
              Connection Name
              <RequiredLabel />
            </div>
          </FormLabel>
          <FormControl>
            <Input
              v-bind="componentField"
              placeholder="My Integration"
            />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

      <FormField
        v-slot="{ componentField }"
        name="token"
      >
        <FormItem>
          <FormLabel>Token</FormLabel>
          <FormControl>
            <Input
              v-bind="componentField"
              type="password"
              placeholder="Leave blank to keep existing token"
            />
          </FormControl>
          <FormDescription>
            Leave blank to keep the existing token.
          </FormDescription>
          <FormMessage />
        </FormItem>
      </FormField>
    </form>

    <template #submitBtn>
      <C8Button
        label="Update"
        :disabled="disabled"
        :loading="isSubmitting"
        @click="updateIntegration"
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
import { useIntegrationStore } from '~/stores/integration'
import type { Integration } from '~/stores/integration'
import { useApiErrorHandling } from '~/composables/useApiErrorHandling'
import { useIntegrationIcon } from '~/composables/useIntegrationIcon'

const updateIntegrationSlide = ref<InstanceType<typeof SlideOver> | null>(null)
const integrationStore = useIntegrationStore()
const { apiError, handleError, clearError } = useApiErrorHandling()

const currentProvider = ref('')

const providerIcon = computed(() => {
  return useIntegrationIcon(currentProvider.value).value
})

const providerLabel = computed(() => {
  const found = integrationStore.supportedIntegrations.find(
    s => s.id === currentProvider.value,
  )
  return found?.label ?? currentProvider.value
})

const schema = z.object({
  uuid: z.string().nonempty({ message: 'Required' }),
  name: z.string().nonempty({ message: 'Required' }).min(1).max(255),
  token: z.string().optional(),
})

const form = useForm({
  validationSchema: toTypedSchema(schema),
  initialValues: {
    uuid: '',
    name: '',
    token: '',
  },
})
const { isSubmitting, meta, setValues } = form

function open(integration: Integration) {
  clearError()
  currentProvider.value = integration.provider
  setValues({
    uuid: integration.uuid,
    name: integration.name ?? '',
    token: '',
  })
  nextTick(() => {
    updateIntegrationSlide.value?.openSlide()
  })
}

defineExpose({ open })

const updateIntegration = form.handleSubmit(async (values) => {
  clearError()
  const payload: Record<string, unknown> = {
    uuid: values.uuid,
    name: values.name,
  }
  if (values.token?.trim()) {
    payload.token = values.token
  }
  try {
    await integrationStore.update(payload)
    updateIntegrationSlide.value?.closeSlide()
    toast.success('Integration updated')
  }
  catch (error: unknown) {
    handleError(error, form)
  }
})

const disabled = computed(() => !meta.value.valid)
</script>
