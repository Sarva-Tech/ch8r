<template>
  <div class="space-y-4">
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div class="flex flex-col lg:flex-row gap-4">
        <div class="flex-1">
          <UInput
            v-model="filters.search"
            placeholder="Search pull requests..."
            icon="i-heroicons-magnifying-glass-16-solid"
            size="sm"
          />
        </div>

        <div class="w-full lg:w-48">
          <USelect
            v-model="filters.state"
            :options="stateOptions"
            size="sm"
          />
        </div>

        <div class="w-full lg:w-48">
          <UInput
            v-model="filters.author"
            placeholder="Filter by author..."
            size="sm"
          />
        </div>

        <UButton
          variant="ghost"
          color="gray"
          size="sm"
          icon="i-heroicons-x-mark-16-solid"
          @click="clearFilters"
        >
          Clear
        </UButton>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <UCard class="text-center">
        <div class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ stats.totalPRs }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Total PRs</div>
      </UCard>
      <UCard class="text-center">
        <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">
          {{ stats.openPRs }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Open PRs</div>
      </UCard>
      <UCard class="text-center">
        <div class="text-2xl font-bold text-green-600 dark:text-green-400">
          {{ stats.mergedPRs }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Merged PRs</div>
      </UCard>
      <UCard class="text-center">
        <div class="text-2xl font-bold text-gray-600 dark:text-gray-400">
          {{ stats.closedPRs }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Closed PRs</div>
      </UCard>
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
      <template #title>Error Loading Pull Requests</template>
      <template #description>{{ error }}</template>
      <template #actions>
        <UButton @click="refreshPullRequests" variant="solid" color="red" size="xs">
          Retry
        </UButton>
      </template>
    </UAlert>

    <UCard
      v-else-if="filteredPullRequests.length === 0"
      class="text-center py-8"
    >
      <UIcon name="i-heroicons-code-bracket-square-16-solid" class="mx-auto text-4xl text-gray-400 mb-4" />
      <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
        No pull requests found
      </h3>
      <p class="text-gray-500 dark:text-gray-400">
        {{ filters.search || filters.author ? 'Try adjusting your filters' : 'This repository has no pull requests' }}
      </p>
    </UCard>

    <div v-else class="space-y-3">
      <div
        v-for="pr in paginatedPullRequests"
        :key="pr.id"
        class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition-shadow"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-2">
              <h4 class="text-lg font-medium text-gray-900 dark:text-white truncate">
                {{ pr.title }}
              </h4>
              <UBadge
                :color="prStateColor(pr.state)"
                :variant="pr.state === 'open' ? 'solid' : 'outline'"
                size="xs"
              >
                {{ pr.state }}
              </UBadge>
              <UBadge
                v-if="pr.merged"
                color="purple"
                variant="solid"
                size="xs"
              >
                Merged
              </UBadge>
            </div>

            <p v-if="pr.body" class="text-sm text-gray-600 dark:text-gray-300 line-clamp-2 mb-3">
              {{ pr.body }}
            </p>

            <div class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 mb-2">
              <span class="flex items-center gap-1">
                <UIcon name="i-heroicons-arrow-right-16-solid" />
                {{ pr.head_branch }}
              </span>
              <span>→</span>
              <span class="flex items-center gap-1">
                <UIcon name="i-heroicons-arrow-left-16-solid" />
                {{ pr.base_branch }}
              </span>
            </div>

            <div class="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
              <span class="flex items-center gap-1">
                <UIcon name="i-heroicons-user-16-solid" />
                {{ pr.author }}
              </span>
              <span class="flex items-center gap-1">
                <UIcon name="i-heroicons-chat-bubble-left-right-16-solid" />
                {{ pr.comment_count }} comments
              </span>
              <span class="flex items-center gap-1">
                <UIcon name="i-heroicons-document-text-16-solid" />
                {{ pr.file_count }} files
              </span>
              <span class="flex items-center gap-1">
                <UIcon name="i-heroicons-calendar-16-solid" />
                {{ formatDate(pr.created_at) }}
              </span>
              <span v-if="pr.labels.length > 0" class="flex items-center gap-1">
                <UIcon name="i-heroicons-tag-16-solid" />
                {{ pr.labels.length }} label{{ pr.labels.length !== 1 ? 's' : '' }}
              </span>
            </div>

            <div class="flex items-center gap-4 text-xs mt-2">
              <span class="flex items-center gap-1 text-green-600 dark:text-green-400">
                <UIcon name="i-heroicons-plus-16-solid" />
                +{{ pr.additions }}
              </span>
              <span class="flex items-center gap-1 text-red-600 dark:text-red-400">
                <UIcon name="i-heroicons-minus-16-solid" />
                -{{ pr.deletions }}
              </span>
              <span class="text-gray-500 dark:text-gray-400">
                {{ pr.changed_files }} files changed
              </span>
            </div>

            <div v-if="pr.labels.length > 0" class="flex flex-wrap gap-1 mt-2">
              <UBadge
                v-for="label in pr.labels.slice(0, 5)"
                :key="label"
                variant="soft"
                size="xs"
              >
                {{ label }}
              </UBadge>
              <UBadge
                v-if="pr.labels.length > 5"
                variant="outline"
                size="xs"
              >
                +{{ pr.labels.length - 5 }} more
              </UBadge>
            </div>
          </div>

          <div class="flex items-center gap-2 ml-4">
            <UButton
              :to="pr.url"
              target="_blank"
              variant="ghost"
              color="gray"
              size="xs"
              icon="i-heroicons-arrow-top-right-on-square-16-solid"
            >
              View on GitHub
            </UButton>
          </div>
        </div>
      </div>
    </div>

    <div v-if="totalPages > 1" class="flex justify-center">
      <UPagination
        v-model="currentPage"
        :page-count="pageSize"
        :total="filteredPullRequests.length"
        :max="7"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { GitHubPullRequest, GitHubFilters } from '~/types/github'

interface Props {
  repositoryId: number
  pullRequests?: GitHubPullRequest[]
  loading?: boolean
  error?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  pullRequests: () => [],
  loading: false,
  error: null
})

const emit = defineEmits<{
  refresh: []
  filterChange: [filters: GitHubFilters]
}>()

const githubStore = useGitHubStore()

const currentPage = ref(1)
const pageSize = 20

const filters = ref<GitHubFilters>({
  state: 'all',
  author: '',
  labels: [],
  since: '',
  until: '',
  search: ''
})

const stateOptions = [
  { value: 'all', label: 'All PRs' },
  { value: 'open', label: 'Open Only' },
  { value: 'closed', label: 'Closed Only' },
  { value: 'merged', label: 'Merged Only' }
]

const stats = computed(() => {
  const totalPRs = props.pullRequests.length
  const openPRs = props.pullRequests.filter(pr => pr.state === 'open').length
  const mergedPRs = props.pullRequests.filter(pr => pr.merged).length
  const closedPRs = props.pullRequests.filter(pr => pr.state === 'closed' && !pr.merged).length

  return {
    totalPRs,
    openPRs,
    mergedPRs,
    closedPRs
  }
})

const filteredPullRequests = computed(() => {
  let filtered = props.pullRequests

  if (filters.value.state !== 'all') {
    if (filters.value.state === 'merged') {
      filtered = filtered.filter(pr => pr.merged)
    } else {
      filtered = filtered.filter(pr => pr.state === filters.value.state)
    }
  }

  if (filters.value.author) {
    filtered = filtered.filter(pr =>
      pr.author.toLowerCase().includes(filters.value.author.toLowerCase())
    )
  }

  if (filters.value.search) {
    const search = filters.value.search.toLowerCase()
    filtered = filtered.filter(pr =>
      pr.title.toLowerCase().includes(search) ||
      pr.body.toLowerCase().includes(search)
    )
  }

  return filtered
})

const totalPages = computed(() => Math.ceil(filteredPullRequests.value.length / pageSize))

const paginatedPullRequests = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  const end = start + pageSize
  return filteredPullRequests.value.slice(start, end)
})

const prStateColor = (state: string) => {
  switch (state) {
    case 'open':
      return 'blue'
    case 'closed':
      return 'gray'
    case 'merged':
      return 'purple'
    default:
      return 'gray'
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString()
}

const clearFilters = () => {
  filters.value = {
    state: 'all',
    author: '',
    labels: [],
    since: '',
    until: '',
    search: ''
  }
  currentPage.value = 1
}

const refreshPullRequests = () => {
  emit('refresh')
}

watch(filters, (newFilters) => {
  currentPage.value = 1
  emit('filterChange', newFilters)
}, { deep: true })

watch(() => props.pullRequests, () => {
  currentPage.value = 1
}, { deep: true })
</script>
