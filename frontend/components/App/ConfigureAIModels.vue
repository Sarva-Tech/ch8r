<template>
  <Card>
    <CardHeader>
      <CardTitle>{{ config.title }}</CardTitle>
      <CardDescription class="space-y-2">
        <div>
          {{ config.description }}
        </div>
      </CardDescription>
    </CardHeader>
    <CardContent>
      <form
        class="space-y-4"
        @submit.prevent="configureModel"
      >
        <C8APIAlert :api-error="apiError" />

        <FormField
          v-slot="{ componentField }"
          name="ai_provider"
        >
          <FormItem>
            <FormLabel class="flex items-center">
              AI Provider
              <RequiredLabel />
            </FormLabel>
            <C8Select
              :options="configuredAIProviderOptions"
              v-bind="componentField"
              placeholder="Select AI provider"
            />
            <FormMessage />
          </FormItem>
        </FormField>

        <FormField
          v-slot="{ componentField }"
          name="models"
        >
          <FormItem>
            <FormLabel class="flex items-center">
              {{ config.modelLabel }}
              <RequiredLabel />
            </FormLabel>
            <C8Combobox
              v-bind="componentField"
              :options="getProviderModels(selectedProviderId)"
              :placeholder="config.modelPlaceholder"
              :multiple="false"
            />
            <FormMessage />
          </FormItem>
        </FormField>

        <div class="flex justify-end">
          <C8Button
            label="Configure"
            :disabled="disabled"
            :loading="isSubmitting"
            type="submit"
          />
        </div>
      </form>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { toast } from 'vue-sonner'
import { computed, watch, onMounted } from 'vue'
import { toTypedSchema } from '@vee-validate/zod'
import { useForm } from 'vee-validate'
import { z } from 'zod'
import {
  FormItem,
  FormLabel,
  FormMessage,
  FormField,
} from '~/components/ui/form'
import C8Select from '~/components/C8Select.vue'
import C8Combobox from '~/components/C8Combobox.vue'
import RequiredLabel from '~/components/RequiredLabel.vue'
import C8APIAlert from '~/components/C8APIAlert.vue'
import C8Button from '~/components/C8Button.vue'
import { useApiErrorHandling } from '~/composables/useApiErrorHandling'

interface ModelConfig {
  title: string
  description: string
  modelLabel: string
  modelPlaceholder: string
  capability: string
  context: string
  successMessage: string
}

interface Props {
  config: ModelConfig
}

const props = defineProps<Props>()

const appStore = useApplicationsStore()
const AIProviderStore = useAIProviderStore()
const AIProviderModelsStore = useAIProviderModelsStore()
const AppAIProvider = useAppAIProviderStore()

const { apiError, handleError, clearError } = useApiErrorHandling()

const schema = z.object({
  ai_provider: z.string().min(1, { message: 'Please select an AI provider' }),
  models: z.array(z.string()).min(1, { message: 'Please select a model' }),
})

const form = useForm({
  validationSchema: toTypedSchema(schema),
  initialValues: {
    ai_provider: undefined as string | undefined,
    models: [] as string[],
  } as {
    ai_provider: string | undefined
    models: string[]
  },
})

const { isSubmitting } = form
const selectedProviderId = computed(() => form.values.ai_provider ? parseInt(form.values.ai_provider) : 0)

watch(selectedProviderId, (newProviderId) => {
  if (newProviderId) {
    const existingConfigs = AppAIProvider.existingAppAIProviderConfigs
      .filter(config =>
        config.capability === props.config.capability
        && config.context === props.config.context
        && config.ai_provider.id === newProviderId
      )

    if (existingConfigs.length > 0) {
      const modelId = existingConfigs
        .map(config => config.external_model_id)
        .filter((id): id is string => id !== null)[0] || ''
      form.setFieldValue('models', modelId ? [modelId] : [])
    }
    else {
      form.setFieldValue('models', [])
    }
  }
  else {
    form.setFieldValue('models', [])
  }
})

const configuredAIProviderOptions = computed(() =>
  AIProviderStore.AIProviders.map(p => ({
    label: p.name,
    value: p.id.toString(),
    icon: useAIProviderIcon(p.provider).value,
  })),
)

const getProviderModels = (providerId: number) => {
  const providerWithModels = AIProviderModelsStore.providerModels.find(
    pm => pm.ai_provider.id === providerId,
  )

  if (!providerWithModels?.ai_provider_models?.models_data) {
    return []
  }

  return providerWithModels.ai_provider_models.models_data.map((model) => {
    const modelName = model.name || model.displayName || model.id || Object.values(model)[0] || ''
    return {
      label: modelName,
      value: modelName,
    }
  })
}

const configureModel = form.handleSubmit(async (values) => {
  clearError()
  try {
    const promise = AppAIProvider.addAppModel(
      appStore.selectedApplication!.uuid,
      parseInt(values.ai_provider),
      values.models[0],
      props.config.context,
      props.config.capability,
    )

    await promise
    if (appStore.selectedApplication) {
      await AppAIProvider.fetchAppAIProviderConfigs(appStore.selectedApplication.uuid)
    }
    toast.success(props.config.successMessage)
  }
  catch (error: unknown) {
    handleError(error, form)
  }
})

const disabled = computed(() => {
  const values = form.values
  return !(
    (values.ai_provider as string)
    && (values.models as string[]).length > 0
  )
})

onMounted(async () => {
  try {
    await AIProviderStore.load()
    await AIProviderModelsStore.load()
    if (appStore.selectedApplication) {
      await AppAIProvider.fetchAppAIProviderConfigs(appStore.selectedApplication.uuid)

      const existingConfigs = AppAIProvider.existingAppAIProviderConfigs
        .filter(config =>
          config.capability === props.config.capability
          && config.context === props.config.context
        )

      if (existingConfigs.length > 0) {
        const firstConfig = existingConfigs[0]
        const modelIds = existingConfigs
          .filter(config => config.ai_provider.id === firstConfig.ai_provider.id)
          .map(config => config.external_model_id)
          .filter((id): id is string => id !== null)

        form.setFieldValue('ai_provider', firstConfig.ai_provider.id.toString())
        form.setFieldValue('models', modelIds.length > 0 ? [modelIds[0]] : [])
      }
    }
  }
  catch (e: unknown) {
    console.error(e)
    toast.error('Failed to load initial data')
  }
})
</script>
