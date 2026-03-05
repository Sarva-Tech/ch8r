<template>
  <SlideOver
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

    <form class="space-y-5" @submit.prevent="createNewAIProvider">
      <C8APIAlert :api-error="apiError" />

      <FormField v-slot="{ componentField }" name="provider">
        <FormItem>
          <FormLabel class="flex items-center">
            AI Provider
            <RequiredLabel />
          </FormLabel>
          <C8Select
            :options="providerOptions"
            v-bind="componentField"
          />
        </FormItem>
      </FormField>

      <FormField v-if="shouldShowBaseUrl" v-slot="{ componentField }" name="base_url">
        <FormItem>
          <FormLabel class="flex items-center">
            <div>
              Base URL
              <RequiredLabel v-if="isCustomProvider" />
            </div>
          </FormLabel>
          <FormControl>
            <Input
              v-bind="componentField"
              placeholder="https://api.openai.com/v1"
              :disabled="!isCustomProvider"
            />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

      <FormField v-slot="{ componentField }" name="provider_api_key">
        <FormItem>
          <FormLabel class="flex items-center">
            <div>
              API Key
              <RequiredLabel />
            </div>
          </FormLabel>
          <FormControl>
            <Input
              v-bind="componentField"
              type="password"
              placeholder="org-YvnH2WW0YjzHn0gAUzh7JY3q"
            />
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

      <FormField v-slot="{ componentField }" name="name">
        <FormItem>
          <FormLabel class="flex items-center">
            <div>
              Connection Name
              <RequiredLabel />
            </div>
          </FormLabel>
          <FormControl>
            <div class="flex gap-2">
              <Input v-bind="componentField" placeholder="Ch8r Dev" class="flex-1" />
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
import { toast } from 'vue-sonner'
import { toTypedSchema } from '@vee-validate/zod'
import { computed, ref, watch, onMounted } from 'vue'
import C8Select from '~/components/C8Select.vue'
import RequiredLabel from '~/components/RequiredLabel.vue'
import {
  FormControl,
  FormItem,
  FormLabel,
  FormMessage,
} from '~/components/ui/form'
import { z } from 'zod'
import { useForm } from 'vee-validate'
import { useUniqueName } from '~/composables/useUniqueName'
import { useApiErrorHandling } from '~/composables/useApiErrorHandling'
import { useAIProviderIcon } from '~/composables/useAIProviderIcon'
import { Sparkles, Plus } from 'lucide-vue-next'
import C8APIAlert from '~/components/C8APIAlert.vue'

const newAIProviderSlide = ref<InstanceType<typeof SlideOver> | null>(null)
const AIProviderStore = useAIProviderStore()
const { generateShortUniqueName } = useUniqueName()
const { apiError, handleError, clearError } = useApiErrorHandling()

const providerOptions = computed(() =>
  AIProviderStore.supportedAIProviders.map(p => ({ 
    label: p.label, 
    value: p.id, 
    baseUrl: p.base_url,
    icon: useAIProviderIcon(p.id).value
  }))
)
const isCustomProvider = computed(() => form.values.provider === 'custom')
const shouldShowBaseUrl = computed(() => isCustomProvider.value || form.values.provider === '')

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
        path: ['base_url']
      })
    } else if (!z.string().url().safeParse(data.base_url).success) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Please enter a valid URL',
        path: ['base_url']
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
  }
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
      if (newProvider === 'custom') {
        form.setFieldValue('base_url', '')
      } else {
        form.setFieldValue('base_url', selectedProvider.base_url)
      }
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
      }
    })
  }
}

const openSlideWithReset = () => {
  resetFormToDefaults()
  newAIProviderSlide.value?.openSlide()
}

const generateUniqueConnectionName = () => {
  const uniqueName = generateShortUniqueName('Connection')
  form.setFieldValue('name', uniqueName)
}

const createNewAIProvider = form.handleSubmit(async (values) => {
  clearError()

  const submitValues = { ...values }
  if (values.provider !== 'custom') {
    delete submitValues.base_url
  }

  try {
    await AIProviderStore.create(submitValues)
    newAIProviderSlide.value?.closeSlide()
    toast.success('AI provider created')
  } catch (error: unknown) {
    handleError(error, form)
  }
})

const disabled = computed(() => {
  const values = form.values
  const baseUrlValid = values.provider === 'custom' 
    ? values.base_url?.trim() 
    : true
  return !(
    values.name?.trim() &&
    baseUrlValid &&
    values.provider?.trim() &&
    values.provider_api_key?.trim()
  )
})
</script>
