<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          GitHub Repositories
        </h1>
        <p class="text-gray-600 dark:text-gray-300">
          Manage and ingest GitHub repository data
        </p>
      </div>

      <UButton
        icon="i-heroicons-plus-16-solid"
        @click="showIngestionForm = true"
      >
        Ingest Repository
      </UButton>
    </div>

    <UCard v-if="!hasGitHubIntegration">
      <div class="text-center py-8">
        <UIcon name="i-heroicons-link-16-solid" class="mx-auto text-4xl text-gray-400 mb-4" />
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
          No GitHub Integration Found
        </h3>
        <p class="text-gray-500 dark:text-gray-400 mb-4">
          You need to set up a GitHub integration before ingesting repositories.
        </p>
        <UButton
          :to="`/applications/${appId}/integrations`"
          icon="i-heroicons-cog-6-tooth-16-solid"
        >
          Configure Integration
        </UButton>
      </div>
    </UCard>

    <div v-else>
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <UCard class="text-center">
          <div class="text-2xl font-bold text-gray-900 dark:text-white">
            {{ repositories.length }}
          </div>
          <div class="text-sm text-gray-500 dark:text-gray-400">Total Repositories</div>
        </UCard>
        <UCard class="text-center">
          <div class="text-2xl font-bold text-green-600 dark:text-green-400">
            {{ completedRepositories.length }}
          </div>
          <div class="text-sm text-gray-500 dark:text-gray-400">Successfully Ingested</div>
        </UCard>
        <UCard class="text-center">
          <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {{ runningRepositories.length }}
          </div>
          <div class="text-sm text-gray-500 dark:text-gray-400">Currently Ingesting</div>
        </UCard>
        <UCard class="text-center">
          <div class="text-2xl font-bold text-red-600 dark:text-red-400">
            {{ failedRepositories.length }}
          </div>
          <div class="text-sm text-gray-500 dark:text-gray-400">Failed Ingestions</div>
        </UCard>
      </div>

      <div v-if="loading && repositories.length === 0" class="flex justify-center py-8">
        <UIcon name="i-heroicons-arrow-path-16-solid" class="animate-spin text-2xl text-blue-600" />
      </div>

      <UAlert
        v-else-if="error"
        color="red"
        variant="soft"
        icon="i-heroicons-exclamation-triangle-16-solid"
      >
        <template #title>Error Loading Repositories</template>
        <template #description>{{ error }}</template>
        <template #actions>
          <UButton @click="refreshRepositories" variant="solid" color="red" size="xs">
            Retry
          </UButton>
        </template>
      </UAlert>

      <UCard
        v-else-if="repositories.length === 0 && !loading"
        class="text-center py-8"
      >
        <UIcon name="i-heroicons-inbox-16-solid" class="mx-auto text-4xl text-gray-400 mb-4" />
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
          No repositories ingested yet
        </h3>
        <p class="text-gray-500 dark:text-gray-400 mb-4">
          Start by ingesting your first GitHub repository.
        </p>
        <UButton
          icon="i-heroicons-plus-16-solid"
          @click="showIngestionForm = true"
        >
          Ingest Repository
        </UButton>
      </UCard>

      <div v-else class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        <GitHubRepositoryCard
          v-for="repository in repositories"
          :key="repository.id"
          :repository="repository"
          :app-id="appId"
          @delete="handleDeleteRepository"
          @re-ingest="handleReIngestRepository"
          @refresh="handleRefreshRepository"
        />
      </div>
    </div>

    <UModal v-model="showIngestionForm" :ui="{ width: 'sm:max-w-2xl' }">
      <GitHubIngestionForm
        :integrations="integrations"
        @close="showIngestionForm = false"
        @success="handleIngestionSuccess"
        @error="handleIngestionError"
      />
    </UModal>

    <UModal v-model="showDeleteModal">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            Delete Repository
          </h3>
        </template>

        <div class="space-y-4">
          <p class="text-gray-600 dark:text-gray-300">
            Are you sure you want to delete the repository
            <span class="font-semibold">{{ repositoryToDelete?.full_name }}</span>?
          </p>
          <p class="text-sm text-red-600 dark:text-red-400">
            This action cannot be undone. All ingested data will be permanently deleted.
          </p>
        </div>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton
              variant="ghost"
              color="gray"
              @click="showDeleteModal = false"
            >
              Cancel
            </UButton>
            <UButton
              color="red"
              :loading="deleteLoading"
              @click="confirmDelete"
            >
              Delete Repository
            </UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <UModal v-model="showReIngestModal">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            Re-ingest Repository
          </h3>
        </template>

        <div class="space-y-4">
          <p class="text-gray-600 dark:text-gray-300">
            Re-ingest repository
            <span class="font-semibold">{{ repositoryToReIngest?.full_name }}</span>?
          </p>

          <div class="space-y-2">
            <C8Label for="since-date">Ingest Since (Optional)</C8Label>
            <C8Input
              id="since-date"
              v-model="reIngestSince"
              type="datetime-local"
              placeholder="Only ingest data since this date"
            />
            <p class="text-sm text-gray-500 dark:text-gray-400">
              Leave empty to re-ingest all data. Use this to only ingest recent changes.
            </p>
          </div>
        </div>

        <template #footer>
          <div class="flex justify-end gap-3">
            <UButton
              variant="ghost"
              color="gray"
              @click="showReIngestModal = false"
            >
              Cancel
            </UButton>
            <UButton
              :loading="reIngestLoading"
              @click="confirmReIngest"
            >
              Re-ingest Repository
            </UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import type { GitHubRepository } from '~/types/github'

definePageMeta({
  layout: 'application'
})

const route = useRoute()
const appId = route.params.appId as string

const githubStore = useGitHubStore()
const applicationStore = useApplicationStore()

const loading = ref(false)
const error = ref<string | null>(null)
const showIngestionForm = ref(false)
const showDeleteModal = ref(false)
const showReIngestModal = ref(false)
const deleteLoading = ref(false)
const reIngestLoading = ref(false)
const repositoryToDelete = ref<GitHubRepository | null>(null)
const repositoryToReIngest = ref<GitHubRepository | null>(null)
const reIngestSince = ref('')

const repositories = computed(() => githubStore.repositories)
const integrations = computed(() => applicationStore.integrations || [])

const hasGitHubIntegration = computed(() => {
  return integrations.value.some(integration => integration.provider === 'github')
})

const completedRepositories = computed(() =>
  repositories.value.filter(repo => repo.ingestion_status === 'completed')
)

const runningRepositories = computed(() =>
  repositories.value.filter(repo => repo.ingestion_status === 'running')
)

const failedRepositories = computed(() =>
  repositories.value.filter(repo => repo.ingestion_status === 'failed')
)

const loadRepositories = async () => {
  if (!hasGitHubIntegration.value) return

  try {
    loading.value = true
    error.value = null

    const githubIntegration = integrations.value.find(i => i.provider === 'github')
    if (githubIntegration) {
      await githubStore.fetchRepositories(githubIntegration.id)
    }
  } catch (err: any) {
    error.value = err.message || 'Failed to load repositories'
  } finally {
    loading.value = false
  }
}

const refreshRepositories = () => {
  loadRepositories()
}

const handleDeleteRepository = (repository: GitHubRepository) => {
  repositoryToDelete.value = repository
  showDeleteModal.value = true
}

const handleReIngestRepository = (repository: GitHubRepository) => {
  repositoryToReIngest.value = repository
  showReIngestModal.value = true
}

const handleRefreshRepository = async (repository: GitHubRepository) => {
  try {
    await githubStore.reIngestRepository(repository.id)

    const toast = useToast()
    toast.add({
      title: 'Repository Refreshed',
      description: `${repository.full_name} has been refreshed successfully.`,
      color: 'green'
    })
  } catch (err: any) {
    const toast = useToast()
    toast.add({
      title: 'Refresh Failed',
      description: err.message || 'Failed to refresh repository.',
      color: 'red'
    })
  }
}

const confirmDelete = async () => {
  if (!repositoryToDelete.value) return

  try {
    deleteLoading.value = true
    await githubStore.deleteRepository(repositoryToDelete.value.id)

    showDeleteModal.value = false
    repositoryToDelete.value = null

    const toast = useToast()
    toast.add({
      title: 'Repository Deleted',
      description: 'Repository and all its data have been deleted.',
      color: 'green'
    })
  } catch (err: any) {
    const toast = useToast()
    toast.add({
      title: 'Delete Failed',
      description: err.message || 'Failed to delete repository.',
      color: 'red'
    })
  } finally {
    deleteLoading.value = false
  }
}

const confirmReIngest = async () => {
  if (!repositoryToReIngest.value) return

  try {
    reIngestLoading.value = true

    const since = reIngestSince.value ? new Date(reIngestSince.value).toISOString() : undefined
    await githubStore.reIngestRepository(repositoryToReIngest.value.id, since)

    showReIngestModal.value = false
    repositoryToReIngest.value = null
    reIngestSince.value = ''

    const toast = useToast()
    toast.add({
      title: 'Re-ingestion Started',
      description: 'Repository re-ingestion has been started.',
      color: 'green'
    })
  } catch (err: any) {
    const toast = useToast()
    toast.add({
      title: 'Re-ingestion Failed',
      description: err.message || 'Failed to start re-ingestion.',
      color: 'red'
    })
  } finally {
    reIngestLoading.value = false
  }
}

const handleIngestionSuccess = (data: any) => {
  const toast = useToast()
  toast.add({
    title: 'Ingestion Started',
    description: `Repository ${data.owner}/${data.repo} ingestion has started.`,
    color: 'green'
  })

  loadRepositories()
}

const handleIngestionError = (errorMessage: string) => {
  const toast = useToast()
  toast.add({
    title: 'Ingestion Failed',
    description: errorMessage,
    color: 'red'
  })
}

onMounted(() => {
  loadRepositories()
})

watch(integrations, () => {
  if (hasGitHubIntegration.value) {
    loadRepositories()
  }
}, { immediate: true })
</script>
