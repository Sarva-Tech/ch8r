<template>
  <template v-if="props.inline">
    <ConnectIntegrationForm
      :api-error="apiError"
      :provider="props.provider"
      @submit="connectIntegration"
      @generate-name="generateUniqueConnectionName"
    />
    <C8Button
      label="Connect"
      :disabled="disabled"
      :loading="isSubmitting"
      class="mt-4"
      @click="connectIntegration"
    />
  </template>

  <SlideOver
    v-else
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

    <ConnectIntegrationForm
      :api-error="apiError"
      :provider="props.provider"
      @submit="connectIntegration"
      @generate-name="generateUniqueConnectionName"
    />

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
import ConnectIntegrationForm from '~/components/Integration/ConnectIntegrationForm.vue'
import { toast } from 'vue-sonner'
import { toTypedSchema } from '@vee-validate/zod'
import { computed, ref } from 'vue'
import { useForm } from 'vee-validate'
import { z } from 'zod'
import { useIntegrationStore } from '~/stores/integration'
import type { SupportedIntegration } from '~/stores/integration'
import { useUniqueName } from '~/composables/useUniqueName'
import { useApiErrorHandling } from '~/composables/useApiErrorHandling'
import { Plus } from 'lucide-vue-next'

const props = defineProps<{
  provider?: SupportedIntegration
  inline?: boolean
}>()

const emit = defineEmits<{ connected: [] }>()

const connectIntegrationSlide = ref<InstanceType<typeof SlideOver> | null>(null)
const integrationStore = useIntegrationStore()
const { generateShortUniqueName } = useUniqueName()
const { apiError, handleError, clearError } = useApiErrorHandling()

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
