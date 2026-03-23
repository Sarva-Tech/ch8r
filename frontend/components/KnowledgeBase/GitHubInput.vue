<template>
  <div class="space-y-4">
    <div class="space-y-2">
      <Label for="github_repo" class="text-sm font-medium">
        GitHub Repository
        <RequiredLabel />
      </Label>
      <div class="flex gap-2">
        <div class="flex-1">
          <C8Input
            id="github_owner"
            v-model="form.owner"
            placeholder="owner"
            :disabled="loading"
          />
        </div>
        <span class="flex items-center text-gray-500 dark:text-gray-400">/</span>
        <div class="flex-1">
          <C8Input
            id="github_repo"
            v-model="form.repo"
            placeholder="repository-name"
            :disabled="loading"
          />
        </div>
      </div>
      <p class="text-sm text-gray-500 dark:text-gray-400">
        Enter the GitHub repository in the format: owner/repository-name
      </p>
    </div>

    <div class="space-y-2">
      <Label class="text-sm font-medium">GitHub Integration</Label>
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
      <Label for="github_since" class="text-sm font-medium">
        Ingest Since (Optional)
      </Label>
      <C8Input
        id="github_since"
        v-model="form.since"
        type="datetime-local"
        placeholder="Only ingest data since this date"
        :disabled="loading"
      />
      <p class="text-sm text-gray-500 dark:text-gray-400">
        Only ingest data created since this date. Leave empty to ingest all data.
      </p>
    </div>

    <UCollapse v-model="showAdvancedOptions">
      <div class="space-y-3 pt-3 border-t border-gray-200 dark:border-gray-700">
        <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300">Advanced Options</h4>

        <div class="space-y-2">
          <label class="flex items-center gap-2">
            <input
              v-model="advancedOptions.includeDiscussions"
              type="checkbox"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span class="text-sm text-gray-700 dark:text-gray-300">
              Include discussions
            </span>
          </label>
          <label class="flex items-center gap-2">
            <input
              v-model="advancedOptions.includeWiki"
              type="checkbox"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span class="text-sm text-gray-700 dark:text-gray-300">
              Include wiki pages
            </span>
          </label>
          <label class="flex items-center gap-2">
            <input
              v-model="advancedOptions.includeFiles"
              type="checkbox"
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span class="text-sm text-gray-700 dark:text-gray-300">
              Include repository files
            </span>
          </label>
        </div>
      </div>
    </UCollapse>

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
        Repository ingestion has started successfully. It will appear in your knowledge base once completed.
      </template>
    </UAlert>
  </div>
</template>

<script setup lang="ts">
import type { GitHubIngestionRequest } from '~/types/github'

interface Props {
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  update: [data: GitHubIngestionRequest | null]
  error: [message: string]
  success: [message: string]
}>()

const githubStore = useGitHubStore()
const integrationStore = useIntegrationStore()

const error = ref<string | null>(null)
const success = ref(false)
const showAdvancedOptions = ref(false)

const form = ref<GitHubIngestionRequest>({
  owner: '',
  repo: '',
  app_integration_id: 0,
  since: ''
})

const advancedOptions = ref({
  includeDiscussions: true,
  includeWiki: true,
  includeFiles: true
})

const integrationName = computed(() => {
  const appIntegrations = integrationStore.appIntegrations || []
  console.log('GitHubInput - appIntegrations:', appIntegrations)
  const githubIntegration = appIntegrations.find(
    (appInt: any) => appInt.integration.provider === 'github'
  )
  console.log('GitHubInput - githubIntegration:', githubIntegration)
  console.log('GitHubInput - integrationName:', githubIntegration?.integration.name)
  return githubIntegration?.integration.name
})

const isValid = computed(() => {
  return form.value.owner.trim() !== '' &&
         form.value.repo.trim() !== '' &&
         integrationName.value
})

const getGitHubIntegrationId = () => {
  const appIntegrations = integrationStore.appIntegrations || []
  console.log('getGitHubIntegrationId - appIntegrations:', appIntegrations)
  const githubIntegration = appIntegrations.find(
    (appInt: any) => appInt.integration.provider === 'github'
  )
  console.log('getGitHubIntegrationId - githubIntegration:', githubIntegration)
  const integrationId = githubIntegration?.id || 0
  console.log('getGitHubIntegrationId - integrationId:', integrationId)
  return integrationId
}

watch([form, advancedOptions], () => {
  if (isValid.value) {
    emit('update', {
      ...form.value,
      owner: form.value.owner.trim(),
      repo: form.value.repo.trim(),
      app_integration_id: getGitHubIntegrationId(),
      since: form.value.since ? new Date(form.value.since).toISOString() : undefined
    })
  } else {
    emit('update', null)
  }
}, { deep: true })

watch(() => integrationName.value, (newName) => {
  if (newName) {
    form.value.app_integration_id = getGitHubIntegrationId()
  }
}, { immediate: true })

watch(() => props.loading, (newLoading) => {
  if (!newLoading) {
    error.value = null
    success.value = false
  }
})
</script>
