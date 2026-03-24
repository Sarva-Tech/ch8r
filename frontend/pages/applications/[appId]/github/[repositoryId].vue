<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <UButton
          icon="i-heroicons-arrow-left-16-solid"
          variant="ghost"
          color="gray"
          :to="`/applications/${appId}/github`"
        >
          Back to Repositories
        </UButton>

        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
            {{ repository?.full_name }}
          </h1>
          <p class="text-gray-600 dark:text-gray-300">
            Repository details and data management
          </p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <UButton
          icon="i-heroicons-arrow-path-16-solid"
          variant="outline"
          :loading="refreshing"
          @click="refreshRepository"
        >
          Refresh
        </UButton>

        <UDropdown
          :items="actionItems"
          :popper="{ placement: 'bottom-end' }"
        >
          <UButton
            icon="i-heroicons-ellipsis-horizontal-20-solid"
            variant="outline"
          />
        </UDropdown>
      </div>
    </div>

    <div v-if="loading" class="flex justify-center py-8">
      <UIcon name="i-heroicons-arrow-path-16-solid" class="animate-spin text-2xl text-blue-600" />
    </div>

    <UAlert
      v-else-if="error"
      color="red"
      variant="soft"
      icon="i-heroicons-exclamation-triangle-16-solid"
    >
      <template #title>Error Loading Repository</template>
      <template #description>{{ error }}</template>
      <template #actions>
        <UButton @click="loadRepository" variant="solid" color="red" size="xs">
          Retry
        </UButton>
      </template>
    </UAlert>

    <div v-else-if="repository" class="space-y-6">
      <UCard>
        <template #header>
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
            Repository Information
          </h2>
        </template>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div class="space-y-3">
            <div>
              <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">Repository</h3>
              <p class="text-gray-900 dark:text-white">{{ repository.full_name }}</p>
            </div>
            <div>
              <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">Status</h3>
              <UBadge
                :color="statusColor"
                :variant="statusVariant"
                class="mt-1"
              >
                {{ statusText }}
              </UBadge>
            </div>
            <div>
              <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">Visibility</h3>
              <p class="text-gray-900 dark:text-white">
                {{ repository.is_private ? 'Private' : 'Public' }}
              </p>
            </div>
          </div>

          <div class="space-y-3">
            <div>
              <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">Issues</h3>
              <p class="text-2xl font-bold text-gray-900 dark:text-white">
                {{ repository.issue_count || 0 }}
              </p>
            </div>
            <div>
              <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">Pull Requests</h3>
              <p class="text-2xl font-bold text-gray-900 dark:text-white">
                {{ repository.pr_count || 0 }}
              </p>
            </div>
            <div>
              <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">Discussions</h3>
              <p class="text-2xl font-bold text-gray-900 dark:text-white">
                {{ repository.discussion_count || 0 }}
              </p>
            </div>
          </div>

          <div class="space-y-3">
            <div>
              <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">Default Branch</h3>
              <p class="text-gray-900 dark:text-white">{{ repository.default_branch }}</p>
            </div>
            <div>
              <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">Wiki Pages</h3>
              <p class="text-2xl font-bold text-gray-900 dark:text-white">
                {{ repository.wiki_page_count || 0 }}
              </p>
            </div>
            <div>
              <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">Files</h3>
              <p class="text-2xl font-bold text-gray-900 dark:text-white">
                {{ repository.file_count || 0 }}
              </p>
            </div>
          </div>

          <div class="space-y-3">
            <div>
              <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">Created</h3>
              <p class="text-gray-900 dark:text-white">
                {{ formatDate(repository.created_at) }}
              </p>
            </div>
            <div>
              <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">Last Updated</h3>
              <p class="text-gray-900 dark:text-white">
                {{ formatDate(repository.updated_at) }}
              </p>
            </div>
            <div v-if="repository.last_ingested_at">
              <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">Last Ingested</h3>
              <p class="text-gray-900 dark:text-white">
                {{ formatDate(repository.last_ingested_at) }}
              </p>
            </div>
          </div>
        </div>
      </UCard>

      <UTabs v-model="activeTab" :items="tabItems">
        <template #issues>
          <GitHubIssuesList
            :repository-id="repository.id"
            :issues="issues"
            :loading="issuesLoading"
            :error="issuesError"
            @refresh="loadIssues"
          />
        </template>

        <template #pull-requests>
          <GitHubPullRequestsList
            :repository-id="repository.id"
            :pull-requests="pullRequests"
            :loading="pullRequestsLoading"
            :error="pullRequestsError"
            @refresh="loadPullRequests"
          />
        </template>

        <template #statistics>
          <div class="space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <UCard class="text-center">
                <div class="text-2xl font-bold text-gray-900 dark:text-white">
                  {{ stats.totalIssues }}
                </div>
                <div class="text-sm text-gray-500 dark:text-gray-400">Total Issues</div>
              </UCard>
              <UCard class="text-center">
                <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {{ stats.openIssues }}
                </div>
                <div class="text-sm text-gray-500 dark:text-gray-400">Open Issues</div>
              </UCard>
              <UCard class="text-center">
                <div class="text-2xl font-bold text-gray-900 dark:text-white">
                  {{ stats.totalPRs }}
                </div>
                <div class="text-sm text-gray-500 dark:text-gray-400">Total PRs</div>
              </UCard>
              <UCard class="text-center">
                <div class="text-2xl font-bold text-green-600 dark:text-green-400">
                  {{ stats.mergedPRs }}
                </div>
                <div class="text-sm text-gray-500 dark:text-gray-400">Merged PRs</div>
              </UCard>
            </div>

            <UCard>
              <template #header>
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                  Repository Activity
                </h3>
              </template>
              <div class="h-64 flex items-center justify-center bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div class="text-center">
                  <UIcon name="i-heroicons-chart-bar-16-solid" class="mx-auto text-4xl text-gray-400 mb-2" />
                  <p class="text-gray-500 dark:text-gray-400">
                    Activity charts coming soon
                  </p>
                </div>
              </div>
            </UCard>
          </div>
        </template>
      </UTabs>
    </div>
  </div>
</template>

<script setup lang="ts">

definePageMeta({
  layout: 'application'
})

const route = useRoute()
const appId = route.params.appId as string
const repositoryId = parseInt(route.params.repositoryId as string)

const githubStore = useGitHubStore()

const loading = ref(false)
const error = ref<string | null>(null)
const refreshing = ref(false)
const activeTab = ref('issues')

const issuesLoading = ref(false)
const issuesError = ref<string | null>(null)
const pullRequestsLoading = ref(false)
const pullRequestsError = ref<string | null>(null)

const repository = computed(() => githubStore.currentRepository)
const issues = computed(() => githubStore.issues)
const pullRequests = computed(() => githubStore.pullRequests)
const stats = computed(() => githubStore.stats)

const statusColor = computed(() => {
  switch (repository.value?.ingestion_status) {
    case 'completed':
      return 'green'
    case 'running':
      return 'blue'
    case 'failed':
      return 'red'
    default:
      return 'gray'
  }
})

const statusVariant = computed(() => {
  switch (repository.value?.ingestion_status) {
    case 'completed':
      return 'solid'
    case 'running':
      return 'soft'
    case 'failed':
      return 'solid'
    default:
      return 'outline'
  }
})

const statusText = computed(() => {
  switch (repository.value?.ingestion_status) {
    case 'completed':
      return 'Ready'
    case 'running':
      return 'Ingesting'
    case 'failed':
      return 'Failed'
    default:
      return 'Pending'
  }
})

const tabItems = [
  {
    key: 'issues',
    label: 'Issues',
    icon: 'i-heroicons-chat-bubble-left-right-16-solid'
  },
  {
    key: 'pull-requests',
    label: 'Pull Requests',
    icon: 'i-heroicons-code-bracket-square-16-solid'
  },
  {
    key: 'statistics',
    label: 'Statistics',
    icon: 'i-heroicons-chart-bar-16-solid'
  }
]

const actionItems = computed(() => [
  [
    {
      label: 'View on GitHub',
      icon: 'i-heroicons-arrow-top-right-on-square-16-solid',
      click: () => window.open(repository.value?.url, '_blank')
    },
    {
      label: 'Re-ingest Repository',
      icon: 'i-heroicons-arrow-down-tray-16-solid',
      click: handleReIngest
    }
  ],
  [
    {
      label: 'Delete Repository',
      icon: 'i-heroicons-trash-16-solid',
      click: handleDelete
    }
  ]
])

const loadRepository = async () => {
  try {
    loading.value = true
    error.value = null

    const repo = githubStore.getRepositoryById(repositoryId)
    if (repo) {
      githubStore.setCurrentRepository(repo)
    } else {
      error.value = 'Repository not found'
    }
  } catch (err: any) {
    error.value = err.message || 'Failed to load repository'
  } finally {
    loading.value = false
  }
}

const refreshRepository = async () => {
  try {
    refreshing.value = true
    await githubStore.reIngestRepository(repositoryId)

    const toast = useToast()
    toast.add({
      title: 'Repository Refreshed',
      description: 'Repository data has been refreshed.',
      color: 'green'
    })
  } catch (err: any) {
    const toast = useToast()
    toast.add({
      title: 'Refresh Failed',
      description: err.message || 'Failed to refresh repository.',
      color: 'red'
    })
  } finally {
    refreshing.value = false
  }
}

const loadIssues = async () => {
  try {
    issuesLoading.value = true
    issuesError.value = null
    await githubStore.fetchIssues(repositoryId)
  } catch (err: any) {
    issuesError.value = err.message || 'Failed to load issues'
  } finally {
    issuesLoading.value = false
  }
}

const loadPullRequests = async () => {
  try {
    pullRequestsLoading.value = true
    pullRequestsError.value = null
    await githubStore.fetchPullRequests(repositoryId)
  } catch (err: any) {
    pullRequestsError.value = err.message || 'Failed to load pull requests'
  } finally {
    pullRequestsLoading.value = false
  }
}

const handleReIngest = () => {
  navigateTo(`/applications/${appId}/github`)
}

const handleDelete = () => {
  navigateTo(`/applications/${appId}/github`)
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString()
}

onMounted(() => {
  loadRepository()
})

watch(activeTab, (newTab) => {
  if (newTab === 'issues' && issues.value.length === 0) {
    loadIssues()
  } else if (newTab === 'pull-requests' && pullRequests.value.length === 0) {
    loadPullRequests()
  }
})

watch([repository, activeTab], () => {
  if (repository.value && activeTab.value === 'issues' && issues.value.length === 0) {
    loadIssues()
  } else if (repository.value && activeTab.value === 'pull-requests' && pullRequests.value.length === 0) {
    loadPullRequests()
  }
}, { immediate: true })
</script>
