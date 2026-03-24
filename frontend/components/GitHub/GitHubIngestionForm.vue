<template>
  <UCard>
    <template #header>
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
          Ingest GitHub Repository
        </h3>
        <UButton
          icon="i-heroicons-x-mark-20-solid"
          variant="ghost"
          color="gray"
          size="sm"
          square
          @click="$emit('close')"
        />
      </div>
    </template>

    <form @submit.prevent="handleSubmit" class="space-y-6">
      <!-- Repository Input -->
      <div class="space-y-2">
        <C8Label for="repository" required>Repository</C8Label>
        <div class="flex gap-2">
          <div class="flex-1">
            <C8Input
              id="owner"
              v-model="form.owner"
              placeholder="owner"
              required
              :disabled="loading"
            />
          </div>
          <span class="flex items-center text-gray-500 dark:text-gray-400">/</span>
          <div class="flex-1">
            <C8Input
              id="repo"
              v-model="form.repo"
              placeholder="repository-name"
              required
              :disabled="loading"
            />
          </div>
        </div>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Enter the GitHub repository in the format: owner/repository-name
        </p>
      </div>

      <!-- Integration Display (Read-only) -->
      <div class="space-y-2">
        <C8Label>GitHub Integration</C8Label>
        <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
          <div class="flex items-center gap-2">
            <UIcon name="i-simple-icons-github" class="text-gray-600 dark:text-gray-400" />
            <span class="text-gray-900 dark:text-white">
              {{ integrationName || 'No GitHub integration configured' }}
            </span>
          </div>
          <p v-if="!integrationName" class="text-sm text-red-600 dark:text-red-400 mt-2">
            Please configure a GitHub integration in the Integrations page first.
          </p>
        </div>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Using the configured GitHub integration for ingestion.
        </p>
      </div>

      <div class="space-y-2">
        <C8Label for="since">Ingest Since (Optional)</C8Label>
        <C8Input
          id="since"
          v-model="form.since"
          type="datetime-local"
          placeholder="Only ingest data since this date"
          :disabled="loading"
        />
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Only ingest data created since this date. Leave empty to ingest all data.
        </p>
      </div>


      <C8APIAlert :api-error="apiError" />

      <div v-if="apiError && apiError.details && apiError.details.includes('already in progress')" class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
        <div class="flex items-center gap-2 mb-2">
          <UIcon name="i-heroicons-exclamation-triangle-16-solid" class="text-yellow-600 dark:text-yellow-400" />
          <h4 class="text-sm font-medium text-yellow-800 dark:text-yellow-200">Ingestion in Progress</h4>
        </div>
        <p class="text-sm text-yellow-700 dark:text-yellow-300 mb-3">
          Another ingestion is currently running. You can wait for it to complete or force restart it.
        </p>
        <div class="flex gap-2">
          <UButton
            size="xs"
            variant="outline"
            color="yellow"
            @click="checkStatus"
          >
            Check Status
          </UButton>
          <UButton
            size="xs"
            variant="outline"
            color="red"
            @click="forceRetry"
          >
            Force Restart
          </UButton>
        </div>
      </div>

      <UAlert
        v-if="success"
        color="green"
        variant="soft"
        icon="i-heroicons-check-circle-16-solid"
      >
        <template #title>Ingestion Started</template>
        <template #description>
          Repository ingestion has started successfully. You can track the progress below.
        </template>
      </UAlert>

      <div class="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
        <UButton
          variant="ghost"
          color="gray"
          :disabled="loading"
          @click="$emit('close')"
        >
          Cancel
        </UButton>
        <UButton
          type="submit"
          :loading="loading"
          :disabled="!isFormValid"
        >
          {{ loading ? 'Ingesting...' : 'Start Ingestion' }}
        </UButton>
      </div>
    </form>
  </UCard>
</template>

<script setup lang="ts">
import type { GitHubIngestionRequest } from '~/types/github'
import { useApiErrorHandling } from '~/composables/useApiErrorHandling'
import C8APIAlert from '~/components/C8APIAlert.vue'
import { toast } from 'vue-sonner'

interface Props {
  githubIntegration?: {
    id: number
    name: string
    provider: string
  }
}

const props = withDefaults(defineProps<Props>(), {})

const emit = defineEmits<{
  close: []
  success: [data: GitHubIngestionRequest]
  error: [error: string]
  retry: [data: GitHubIngestionRequest]
}>()

const githubStore = useGitHubStore()
const { apiError, handleError, clearError } = useApiErrorHandling()

const loading = ref(false)
const error = ref<string | null>(null)
const success = ref(false)

const form = ref<GitHubIngestionRequest>({
  owner: '',
  repo: '',
  app_integration_id: 0,
  since: ''
})


const integrationName = computed(() => {
  return props.githubIntegration?.name
})

const isFormValid = computed(() => {
  return form.value.owner.trim() !== '' &&
         form.value.repo.trim() !== '' &&
         props.githubIntegration &&
         props.githubIntegration.id > 0
})

const checkStatus = async () => {
  if (!props.githubIntegration) return

  try {
    const repositories = await githubStore.getRepositories(props.githubIntegration.id)
    const repo = repositories.find(r => r.full_name === `${form.value.owner}/${form.value.repo}`)

    if (repo) {
      if (repo.ingestion_status === 'completed') {
        toast.success('Ingestion completed successfully!')
        emit('close')
      } else if (repo.ingestion_status === 'failed') {
        toast.error('Ingestion failed. You can try again.')
        clearError()
      } else {
        toast.info(`Ingestion status: ${repo.ingestion_status}`)
      }
    }
  } catch (error) {
    console.error('Failed to check status:', error)
  }
}

const forceRetry = () => {
  clearError()
  emit('retry', {
    owner: form.value.owner.trim(),
    repo: form.value.repo.trim(),
    app_integration_id: props.githubIntegration!.id,
    since: form.value.since ? new Date(form.value.since).toISOString() : undefined
  })
}
const handleSubmit = async () => {
  if (!isFormValid.value) return

  clearError()

  try {
    loading.value = true
    success.value = false

    let since = undefined
    if (form.value.since) {
      since = new Date(form.value.since).toISOString()
    }

    const ingestionData = {
      owner: form.value.owner.trim(),
      repo: form.value.repo.trim(),
      app_integration_id: props.githubIntegration!.id,
      since
    }

    await githubStore.ingestRepository(ingestionData)

    success.value = true
    emit('success', ingestionData)

    setTimeout(() => {
      resetForm()
      emit('close')
    }, 2000)

  } catch (err: unknown) {
    handleError(err, form)
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.value = {
    owner: '',
    repo: '',
    app_integration_id: 0,
    since: ''
  }
  success.value = false
  clearError()
}

watch(() => props.githubIntegration, (newIntegration) => {
  if (newIntegration) {
    form.value.app_integration_id = newIntegration.id
  }
}, { immediate: true })
</script>
