<template>
  <div class="space-y-4">

    <div class="space-y-2">
      <Label class="text-sm font-medium">GitHub Integration</Label>
      <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
        <div class="flex items-center gap-2">
          <svg class="w-4 h-4 text-gray-600 dark:text-gray-400" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
          </svg>
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

    <Alert v-if="error" variant="destructive">
      <AlertCircle class="h-4 w-4" />
      <AlertTitle>Ingestion Error</AlertTitle>
      <AlertDescription>{{ error }}</AlertDescription>
    </Alert>

    <Alert v-if="success">
      <CheckCircle class="h-4 w-4" />
      <AlertTitle>Ingestion Started</AlertTitle>
      <AlertDescription>
        Repository ingestion has started successfully. It will appear in your knowledge base once completed.
      </AlertDescription>
    </Alert>
  </div>
</template>

<script setup lang="ts">
import type { GitHubIngestionRequest } from '~/types/github'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { AlertCircle, CheckCircle } from 'lucide-vue-next'

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

const form = ref<GitHubIngestionRequest>({
  owner: '',
  repo: '',
  app_integration_id: 0,
  since: ''
})

const integrationName = computed(() => {
  const appIntegrations = integrationStore.appIntegrations || []
  const githubIntegration = appIntegrations.find(
    (appInt: any) => appInt.integration.provider === 'github'
  )
  return githubIntegration?.integration.name
})

const isValid = computed(() => {
  return form.value.owner.trim() !== '' &&
         form.value.repo.trim() !== '' &&
         integrationName.value
})

const getGitHubIntegrationId = () => {
  const appIntegrations = integrationStore.appIntegrations || []
  const githubIntegration = appIntegrations.find(
    (appInt: any) => appInt.integration.provider === 'github'
  )
  const integrationId = githubIntegration?.id || 0
  return integrationId
}

watch([form], () => {
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
