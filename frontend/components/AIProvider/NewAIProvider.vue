<template>
  <template v-if="props.inline">
    <AIProviderForm
      :api-error="apiError"
      @submit="createNewAIProvider"
      @generate-name="generateUniqueConnectionName"
    />
    <C8Button
      label="Create"
      :disabled="disabled"
      :loading="isSubmitting"
      class="mt-4"
      @click="createNewAIProvider"
    />
  </template>

  <SlideOver
    v-else
    ref="newAIProviderSlide"
    title="Add New AI Provider"
  >
    <template #trigger>
      <C8Button
        label="Add AI Provider"
        :icon="Plus"
        @click="openSlideWithReset"
      />
    </template>

    <AIProviderForm
      :api-error="apiError"
      @submit="createNewAIProvider"
      @generate-name="generateUniqueConnectionName"
    />

    <template #submitBtn>
      <C8Button
        label="Create"
        :disabled="disabled"
        :loading="isSubmitting"
        @click="createNewAIProvider"
      />
    </template>
  </SlideOver>
</template>

<script setup lang="ts">
import SlideOver from '~/components/SlideOver.vue'
import AIProviderForm from '~/components/AIProvider/AIProviderForm.vue'
import { toast } from 'vue-sonner'
import { toTypedSchema } from '@vee-validate/zod'
import { computed, ref, watch, onMounted } from 'vue'
import { z } from 'zod'
import { useForm } from 'vee-validate'
import { useUniqueName } from '~/composables/useUniqueName'
import { useApiErrorHandling } from '~/composables/useApiErrorHandling'
import { Plus } from 'lucide-vue-next'

const props = withDefaults(defineProps<{ inline?: boolean }>(), { inline: false })

const newAIProviderSlide = ref<InstanceType<typeof SlideOver> | null>(null)
const AIProviderStore = useAIProviderStore()
const { generateShortUniqueName } = useUniqueName()
const { apiError, handleError, clearError } = useApiErrorHandling()

const schema = z.object({
  name: z.string().nonempty({ message: 'Required' }).min(1).max(255),
  base_url: z.string().optional(),
  provider: z.string().nonempty({ message: 'Required' }),
  provider_api_key: z.string().nonempty({ message: 'Required' }),
}).superRefine((data, ctx) => {
  if (data.provider === 'custom') {
    if (!data.base_url || !data.base_url.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Custom provider requires base URL',
        path: ['base_url'],
      })
    }
    else if (!z.string().url().safeParse(data.base_url).success) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Please enter a valid URL',
        path: ['base_url'],
      })
    }
  }
})

const form = useForm({
  validationSchema: toTypedSchema(schema),
  initialValues: {
    name: '',
    base_url: '',
    provider_api_key: '',
    provider: '',
  },
})
const { isSubmitting } = form

onMounted(async () => {
  await AIProviderStore.load()
  resetFormToDefaults()
})

watch(() => form.values.provider, (newProvider) => {
  if (newProvider) {
    const selectedProvider = AIProviderStore.supportedAIProviders.find(p => p.id === newProvider)
    if (selectedProvider) {
      form.setFieldValue('base_url', newProvider === 'custom' ? '' : selectedProvider.base_url)
    }
  }
})

const resetFormToDefaults = () => {
  if (AIProviderStore.supportedAIProviders.length > 0) {
    const firstProvider = AIProviderStore.supportedAIProviders[0]
    form.resetForm({
      values: {
        name: generateShortUniqueName('Connection'),
        base_url: firstProvider.base_url,
        provider_api_key: '',
        provider: firstProvider.id,
      },
    })
  }
}

const openSlideWithReset = () => {
  resetFormToDefaults()
  newAIProviderSlide.value?.openSlide()
}

const generateUniqueConnectionName = () => {
  form.setFieldValue('name', generateShortUniqueName('Connection'))
}

const createNewAIProvider = form.handleSubmit(async (values) => {
  clearError()
  const submitValues = { ...values }
  if (values.provider !== 'custom') {
    delete submitValues.base_url
  }
  try {
    await AIProviderStore.create(submitValues)
    await AIProviderStore.load()
    newAIProviderSlide.value?.closeSlide()
    toast.success('AI provider created')
  }
  catch (error: unknown) {
    handleError(error, form)
  }
})

const disabled = computed(() => {
  const values = form.values
  const baseUrlValid = values.provider === 'custom' ? values.base_url?.trim() : true
  return !(values.name?.trim() && baseUrlValid && values.provider?.trim() && values.provider_api_key?.trim())
})
</script>
