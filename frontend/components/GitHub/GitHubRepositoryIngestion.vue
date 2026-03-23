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
          @click="$emit('cancel')"
        />
      </div>
    </template>

    <form @submit.prevent="handleSubmit" class="space-y-6">
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

      <div class="space-y-2">
        <C8Label for="integration" required>GitHub Integration</C8Label>
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

      <UAlert
        v-if="error"
        color="red"
        variant="soft"
        icon="i-heroicons-exclamation-triangle-16-solid"
      >
        <template #title>Ingestion Error</template>
        <template #description>{{ error }}</template>
      </UAlert>

      <UAlert
        v-if="success"
        color="green"
        variant="soft"
        icon="i-heroicons-check-circle-16-solid"
      >
        <template #title>Ingestion Started</template>
        <template #description>
          Repository ingestion has started successfully. The repository will appear in your knowledge base once completed.
        </template>
      </UAlert>

      <div class="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
        <UButton
          variant="ghost"
          color="gray"
          :disabled="loading"
          @click="$emit('cancel')"
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

interface Props {
  appId: string
  githubIntegration?: {
    id: number
    name: string
    provider: string
  }
}

const props = withDefaults(defineProps<Props>(), {})

const emit = defineEmits<{
  cancel: []
  success: [data: GitHubIngestionRequest]
  error: [error: string]
}>()

const githubStore = useGitHubStore()

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

const handleSubmit = async () => {
  if (!isFormValid.value) return

  try {
    loading.value = true
    error.value = null
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
      emit('cancel')
    }, 2000)

  } catch (err: any) {
    error.value = err.message || 'Failed to start repository ingestion'
    emit('error', error.value)
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
  error.value = null
  success.value = false
}

watch(() => props.githubIntegration, (newIntegration) => {
  if (newIntegration) {
    form.value.app_integration_id = newIntegration.id
  }
}, { immediate: true })
</script>
