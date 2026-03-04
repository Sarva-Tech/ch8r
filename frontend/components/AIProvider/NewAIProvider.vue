<template>
  <SlideOver
    ref="newAIProviderSlideOver"
    title="Create New AI Provider"
  >
    <template #trigger>
      <C8Button label="Create New AI Provider" />
    </template>

    <form class="space-y-5" @submit.prevent="createNewAIProvider">
      <Alert v-if="formError" variant="destructive">
        <AlertCircleIcon />
        <AlertTitle>{{ formError.error }}</AlertTitle>
        <AlertDescription v-if="formError.details">
          <p> {{ formError.details }} </p>
        </AlertDescription>
      </Alert>

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

      <FormField v-slot="{ componentField }" name="base_url">
        <FormItem>
          <FormLabel class="flex items-center">
            <div>
              Base URL
              <RequiredLabel />
            </div>
          </FormLabel>
          <FormControl>
            <Input
              v-bind="componentField"
              placeholder="https://api.openai.com/v1"
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
import { setBackendErrors } from '~/lib/utils'
import { useUniqueName } from '~/composables/useUniqueName'
import { Sparkles, AlertCircleIcon } from 'lucide-vue-next'

const newAIProviderSlideOver = ref<InstanceType<typeof SlideOver> | null>(null)
const AIProviderStore = useAIProviderStore()
const { generateShortUniqueName } = useUniqueName()

const formError = ref<{
  error?: string
  details?: string
} | null>(null)

const providerOptions = computed(() =>
  AIProviderStore.supportedAIProviders.map(p => ({ label: p.label, value: p.id, baseUrl: p.base_url }))
)
const schema = z.object({
  name: z.string().nonempty({ message: 'Required' }).min(1).max(255),
  base_url: z
    .string()
    .nonempty({ message: 'Required' }),
  provider: z.string().nonempty({ message: 'Required' }),
  provider_api_key: z.string().nonempty({ message: 'Required' }),
})

const form = useForm({
  validationSchema: toTypedSchema(schema),
  initialValues: {
    name: '',
    base_url: '',
    provider_api_key: '',
    provider: ''
  }
})
const { isSubmitting, setFieldValue } = form

onMounted(async () => {
  await AIProviderStore.load()
  if (AIProviderStore.supportedAIProviders.length > 0) {
    const firstProvider = AIProviderStore.supportedAIProviders[0]
    setFieldValue('provider', firstProvider.id)
    setFieldValue('base_url', firstProvider.base_url)
    const uniqueName = generateShortUniqueName('Connection')
    setFieldValue('name', uniqueName)
  }
})

watch(() => form.values.provider, (newProvider) => {
  if (newProvider) {
    const selectedProvider = AIProviderStore.supportedAIProviders.find(p => p.id === newProvider)
    if (selectedProvider) {
      form.setFieldValue('base_url', selectedProvider.base_url)
    }
  }
})

const generateUniqueConnectionName = () => {
  const uniqueName = generateShortUniqueName('Connection')
  form.setFieldValue('name', uniqueName)
}

const createNewAIProvider = form.handleSubmit(async (values) => {
  formError.value = null

  try {
    await AIProviderStore.create(values)
    newAIProviderSlideOver.value?.closeSlide()
    toast.success('AI provider created')
  } catch (error: unknown) {
    const err = error as {
      errors?: Record<string, string[] | string> | { error?: string; details?: string }
    }

    if (err.errors && typeof err.errors === 'object' && 'error' in err.errors) {
      const errorObj = err.errors as { error?: string; details?: string }
      formError.value = {
        error: errorObj.error,
        details: errorObj.details
      }
    } else if (err.errors && typeof err.errors === 'object') {
      setBackendErrors(form, err.errors as Record<string, string[] | string>)
    } else {
      formError.value = {
        error: 'Unexpected Error',
        details: 'An unexpected error occurred while creating the AI provider'
      }
    }
  }
})

const disabled = computed(() => {
  const values = form.values
  return !(
    values.name?.trim() &&
    values.base_url?.trim() &&
    values.provider?.trim() &&
    values.provider_api_key?.trim()
  )
})
</script>
