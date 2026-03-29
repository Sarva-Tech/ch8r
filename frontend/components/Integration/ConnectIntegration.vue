<template>
  <SlideOver
    ref="connectIntegrationSlide"
    title="Add New Integration"
  >
    <template #trigger>
      <C8Button
        label="Add New Integration"
        :icon="Plus"
        @click="open"
      />
    </template>
    <form
      class="space-y-5"
      @submit.prevent="connectIntegration"
    >
      <C8APIAlert :api-error="apiError" />

      <FormField
        v-if="!props.provider"
        v-slot="{ componentField }"
        name="provider"
      >
        <FormItem>
          <FormLabel class="flex items-center">
            Integration
            <RequiredLabel />
          </FormLabel>
          <C8Select
            :options="providerOptions"
            v-bind="componentField"
            placeholder="Select integration"
          />
          <FormMessage />
        </FormItem>
      </FormField>

      <div
        v-else
        class="flex items-center gap-2 rounded-md border bg-muted/40 px-3 py-2 text-sm"
      >
        <component
          :is="getProviderIcon(props.provider.id)"
          v-if="getProviderIcon(props.provider.id)"
          class="h-4 w-4"
        />
        <span class="font-medium">{{ props.provider.label }}</span>
      </div>

      <FormField
        v-slot="{ componentField }"
        name="token"
      >
        <FormItem>
          <FormLabel class="flex items-center">
            Token
            <RequiredLabel />
          </FormLabel>
          <FormControl>
            <Input
              v-bind="componentField"
              type="password"
              placeholder="Enter your token"
            />
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
            Connection Name
            <RequiredLabel />
          </FormLabel>
          <FormControl>
            <div class="flex gap-2">
              <Input
                v-bind="componentField"
                placeholder="My Integration"
                class="flex-1"
              />
              <C8Button
                variant="outline"
                size="icon"
                type="button"
                @click="generateUniqueConnectionName"
              >
                <Sparkles class="h-4 w-4" />
              </C8Button>
            </div>
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>
    </form>

    <template #submitBtn>
      <C8Button
        label="Connect"
        :disabled="disabled"
        :loading="isSubmitting"
        @click="connectIntegration"
      />
    </template>
  </SlideOver>
</template>

<script setup lang="ts">
import SlideOver from '~/components/SlideOver.vue'
import { toast } from 'vue-sonner'
import { toTypedSchema } from '@vee-validate/zod'
import { computed, ref } from 'vue'
import RequiredLabel from '~/components/RequiredLabel.vue'
import C8APIAlert from '~/components/C8APIAlert.vue'
import C8Select from '~/components/C8Select.vue'
import { Input } from '~/components/ui/input'
import {
  FormControl,
  FormItem,
  FormLabel,
  FormMessage,
} from '~/components/ui/form'
import { useForm } from 'vee-validate'
import { z } from 'zod'
import { useIntegrationStore } from '~/stores/integration'
import type { SupportedIntegration } from '~/stores/integration'
import { useUniqueName } from '~/composables/useUniqueName'
import { useApiErrorHandling } from '~/composables/useApiErrorHandling'
import { useIntegrationIcon } from '~/composables/useIntegrationIcon'
import { Sparkles, Plus } from 'lucide-vue-next'

const props = defineProps<{
  provider?: SupportedIntegration
}>()

const emit = defineEmits<{ connected: [] }>()

const connectIntegrationSlide = ref<InstanceType<typeof SlideOver> | null>(null)
const integrationStore = useIntegrationStore()
const { generateShortUniqueName } = useUniqueName()
const { apiError, handleError, clearError } = useApiErrorHandling()

const providerOptions = computed(() =>
  integrationStore.supportedIntegrations.map(p => ({
    label: p.label,
    value: p.id,
    icon: useIntegrationIcon(p.id).value,
  })),
)

function getProviderIcon(providerId: string) {
  return useIntegrationIcon(providerId).value
}

const schema = computed(() =>
  props.provider
    ? z.object({
        name: z.string().nonempty({ message: 'Required' }).min(1).max(255),
        token: z.string().nonempty({ message: 'Required' }),
        provider: z.string().optional(),
      })
    : z.object({
        name: z.string().nonempty({ message: 'Required' }).min(1).max(255),
        token: z.string().nonempty({ message: 'Required' }),
        provider: z.string().nonempty({ message: 'Please select an integration type' }),
      }),
)

const form = useForm({
  validationSchema: toTypedSchema(schema.value),
  initialValues: { name: '', token: '', provider: '' },
})
const { isSubmitting } = form

const generateUniqueConnectionName = () => {
  form.setFieldValue('name', generateShortUniqueName('Connection'))
}

function open() {
  clearError()
  form.resetForm({
    values: {
      name: generateShortUniqueName('Connection'),
      token: '',
      provider: props.provider?.id ?? '',
    },
  })
  connectIntegrationSlide.value?.openSlide()
}

defineExpose({ open })

const connectIntegration = form.handleSubmit(async (values) => {
  clearError()
  const providerId = props.provider?.id ?? values.provider
  try {
    await integrationStore.create({
      name: values.name,
      provider: providerId,
      token: values.token,
    })
    connectIntegrationSlide.value?.closeSlide()
    toast.success('Integration connected')
    emit('connected')
  }
  catch (error: unknown) {
    handleError(error, form)
  }
})

const disabled = computed(() => {
  const v = form.values
  const hasProvider = props.provider?.id || v.provider?.trim()
  return !(v.name?.trim() && v.token?.trim() && hasProvider)
})
</script>
