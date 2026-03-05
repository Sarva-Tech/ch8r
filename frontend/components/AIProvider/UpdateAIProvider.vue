<template>
  <SlideOver ref="updateAIProviderSlide" title="Update AI Provider">
    <form class="space-y-5" @submit.prevent="updateAIProvider">
      <C8APIAlert :api-error="apiError" />

      <FormField name="provider">
        <FormItem>
          <FormLabel class="flex items-center">
            AI Provider
          </FormLabel>
          <FormControl>
            <div class="flex items-center gap-2 bg-muted border rounded-md px-3 py-2">
              <component
                :is="getProviderIcon(form.values.provider || '')"
                v-if="getProviderIcon(form.values.provider || '')" 
                class="h-4 w-4 flex-shrink-0"
              />
              <span class="text-sm text-muted-foreground">
                {{ getProviderLabel(form.values.provider || '') }}
              </span>
            </div>
          </FormControl>
          <FormMessage />
        </FormItem>
      </FormField>

      <FormField v-slot="{ componentField }" name="base_url" v-if="shouldShowBaseUrl">
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
            </div>
          </FormLabel>
          <FormControl>
            <Input
              v-bind="componentField"
              type="password"
              placeholder="Leave blank to keep existing key"
            />
          </FormControl>
          <FormDescription>
            Leave the API key field blank to keep the existing key.
          </FormDescription>
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
            <Input v-bind="componentField" placeholder="Ch8r Dev" />
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
        @click="updateAIProvider"
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
import { useAIProviderIcon } from '~/composables/useAIProviderIcon'
import type { AIProvider } from '~/stores/aiProvider'

const updateAIProviderSlide = ref<InstanceType<typeof SlideOver> | null>(null)
const AIProviderStore = useAIProviderStore()
const { apiError, handleError, clearError } = useApiErrorHandling()

const providerOptions = computed(() =>
  AIProviderStore.supportedAIProviders.map(p => ({ label: p.label, value: p.id, baseUrl: p.base_url }))
)

const getProviderLabel = (providerValue: string) => {
  const provider = providerOptions.value.find(p => p.value === providerValue)
  if (provider) {
    return provider.label
  }
  return providerValue.charAt(0).toUpperCase() + providerValue.slice(1)
}

const getProviderIcon = (providerValue: string) => {
  return useAIProviderIcon(providerValue).value
}

const isCustomProvider = computed(() => form.values.provider === 'custom')
const shouldShowBaseUrl = computed(() => isCustomProvider.value || form.values.provider === '')

const schema = z.object({
  uuid: z.string().nonempty({ message: 'Required' }),
  name: z.string().nonempty({ message: 'Required' }).min(1).max(255),
  provider: z.string().nonempty({ message: 'Required' }),
  base_url: z.string().optional(),
  provider_api_key: z.string().optional(),
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
    uuid: '',
    name: '',
    provider: '',
    base_url: '',
    provider_api_key: '',
  },
})
const { isSubmitting, meta, setValues } = form

function open(AIProvider: AIProvider) {
  clearError()
  
  let baseUrl = ''
  if (AIProvider.provider === 'custom') {
    baseUrl = (AIProvider.metadata?.base_url as string) || AIProvider.base_url || ''
  }
  
  setValues({
    uuid: AIProvider.uuid,
    name: AIProvider.name,
    provider: AIProvider.provider,
    base_url: baseUrl,
    provider_api_key: '',
  })

  nextTick(() => {
    updateAIProviderSlide.value?.openSlide()
  })
}

defineExpose({
  open
})

const updateAIProvider = form.handleSubmit(async (values) => {
  clearError()

  try {
    await AIProviderStore.update(values)
    updateAIProviderSlide.value?.closeSlide()
    toast.success('AI provider updated')
  } catch (error: unknown) {
    handleError(error, form)
  }
})

const disabled = computed(() => !meta.value.valid)
</script>
