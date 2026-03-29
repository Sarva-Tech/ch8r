<template>
  <Card>
    <CardHeader>
      <CardTitle>{{ config.title }}</CardTitle>
      <CardDescription>{{ config.description }}</CardDescription>
    </CardHeader>
    <CardContent>
      <form
        class="space-y-4"
        @submit.prevent="save"
      >
        <C8APIAlert :api-error="apiError" />

        <template v-if="integrationStore.integrations.length === 0">
          <p class="text-sm text-muted-foreground">
            No integrations connected.
            <NuxtLink
              to="/settings/integrations"
              class="underline font-medium"
            >
              Connect one in Settings → Integrations
            </NuxtLink>.
          </p>
        </template>

        <template v-else>
          <FormField
            v-slot="{ componentField }"
            name="integration_uuid"
          >
            <FormItem>
              <FormLabel class="flex items-center">
                Integration
                <RequiredLabel />
              </FormLabel>
              <C8Select
                :options="integrationOptions"
                v-bind="componentField"
                placeholder="Select integration"
              />
              <FormMessage />
            </FormItem>
          </FormField>

          <FormField
            v-if="config.requiresRepo"
            name="repo"
          >
            <FormItem>
              <FormLabel class="flex items-center">
                Repository
                <RequiredLabel />
              </FormLabel>
              <C8Combobox
                v-model="selectedRepo"
                :options="repoOptions"
                :multiple="false"
                :allow-custom-values="true"
                placeholder="Select or type owner/repo"
                search-placeholder="Search repositories..."
                no-results-message="No matching repos"
                :no-options-message="loadingRepos ? 'Loading repositories...' : 'Type owner/repo manually'"
                add-custom-hint="Press Enter to use this repo"
                :disabled="!form.values.integration_uuid || loadingRepos"
              />
              <FormDescription>
                The repository to use for this integration.
              </FormDescription>
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
        </template>
      </form>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { toast } from 'vue-sonner'
import { toTypedSchema } from '@vee-validate/zod'
import { useForm } from 'vee-validate'
import { z } from 'zod'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  FormDescription,
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
import { useIntegrationStore } from '~/stores/integration'
import { useAppIntegrationStore } from '~/stores/appIntegration'

interface IntegrationConfig {
  id: string
  title: string
  description: string
  requiresRepo: boolean
  successMessage: string
}

const props = defineProps<{ config: IntegrationConfig }>()

const appStore = useApplicationsStore()
const integrationStore = useIntegrationStore()
const appIntegrationStore = useAppIntegrationStore()
const { apiError, handleError, clearError } = useApiErrorHandling()

const repoOptions = ref<{ value: string, label: string }[]>([])
const loadingRepos = ref(false)
const selectedRepo = ref<string[]>([])

const schema = computed(() =>
  props.config.requiresRepo
    ? z.object({
        integration_uuid: z.string().min(1, { message: 'Please select an integration' }),
        repo: z.string().optional(),
      })
    : z.object({
        integration_uuid: z.string().min(1, { message: 'Please select an integration' }),
        repo: z.string().optional(),
      }),
)

const form = useForm({
  validationSchema: toTypedSchema(schema.value),
  initialValues: { integration_uuid: '', repo: '' },
})
const { isSubmitting } = form

const integrationOptions = computed(() =>
  integrationStore.integrations.map(i => ({
    label: i.name || i.provider,
    value: i.uuid,
  })),
)

async function loadRepos(integrationUuid: string) {
  if (!integrationUuid) return
  loadingRepos.value = true
  try {
    const repos = await integrationStore.fetchRepos(integrationUuid)
    repoOptions.value = repos.map(r => ({ value: r.full_name, label: r.full_name }))
  }
  catch (e) {
    console.error('Failed to load repos', e)
  }
  finally {
    loadingRepos.value = false
  }
}

watch(() => form.values.integration_uuid, (uuid) => {
  if (uuid && props.config.requiresRepo) {
    // Only clear repos if the integration actually changed
    repoOptions.value = []
    loadRepos(uuid)
  }
}, { immediate: false })

// Keep form repo field in sync with combobox
watch(selectedRepo, (val) => {
  form.setFieldValue('repo', val[0] ?? '')
})

const disabled = computed(() => {
  const v = form.values
  if (!v.integration_uuid?.trim()) return true
  if (props.config.requiresRepo && !selectedRepo.value[0]?.trim()) return true
  return false
})

onMounted(async () => {
  try {
    await integrationStore.load()
    const appUuid = appStore.selectedApplication?.uuid
    if (appUuid) {
      await appIntegrationStore.load(appUuid)
      const existing = appIntegrationStore.appIntegrations.find(
        ai => ai.integration_type === props.config.id,
      )
      if (existing) {
        form.setFieldValue('integration_uuid', existing.integration.uuid)
        if (props.config.requiresRepo) {
          const existingRepo = (existing.metadata?.repo as string) ?? ''
          selectedRepo.value = existingRepo ? [existingRepo] : []
          form.setFieldValue('repo', existingRepo)
          await loadRepos(existing.integration.uuid)
        }
      }
    }
  }
  catch (e) {
    console.error(e)
  }
})

const save = form.handleSubmit(async (values) => {
  clearError()
  const appUuid = appStore.selectedApplication?.uuid
  if (!appUuid) return
  try {
    await appIntegrationStore.create(appUuid, {
      integration_uuid: values.integration_uuid,
      integration_type: props.config.id,
      metadata: props.config.requiresRepo ? { repo: values.repo } : {},
    })
    toast.success(props.config.successMessage)
  }
  catch (error: unknown) {
    handleError(error, form)
  }
})
</script>
