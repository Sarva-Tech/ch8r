<template>
  <div class="space-y-4">
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div class="flex flex-col lg:flex-row gap-4">
        <div class="flex-1">
          <UInput
            v-model="filters.search"
            placeholder="Search issues..."
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

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <UCard class="text-center">
        <div class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ stats.totalIssues }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Total Issues</div>
      </UCard>
      <UCard class="text-center">
        <div class="text-2xl font-bold text-green-600 dark:text-green-400">
          {{ stats.openIssues }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Open Issues</div>
      </UCard>
      <UCard class="text-center">
        <div class="text-2xl font-bold text-gray-600 dark:text-gray-400">
          {{ stats.closedIssues }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Closed Issues</div>
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
      <template #title>Error Loading Issues</template>
      <template #description>{{ error }}</template>
      <template #actions>
        <UButton @click="refreshIssues" variant="solid" color="red" size="xs">
          Retry
        </UButton>
      </template>
    </UAlert>

    <UCard
      v-else-if="filteredIssues.length === 0"
      class="text-center py-8"
    >
      <UIcon name="i-heroicons-inbox-16-solid" class="mx-auto text-4xl text-gray-400 mb-4" />
      <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
        No issues found
      </h3>
      <p class="text-gray-500 dark:text-gray-400">
        {{ filters.search || filters.author ? 'Try adjusting your filters' : 'This repository has no issues' }}
      </p>
    </UCard>

    <div v-else class="space-y-3">
      <div
        v-for="issue in paginatedIssues"
        :key="issue.id"
        class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition-shadow"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-2">
              <h4 class="text-lg font-medium text-gray-900 dark:text-white truncate">
                {{ issue.title }}
              </h4>
              <UBadge
                :color="issue.state === 'open' ? 'green' : 'gray'"
                :variant="issue.state === 'open' ? 'solid' : 'outline'"
                size="xs"
              >
                {{ issue.state }}
              </UBadge>
            </div>

            <p v-if="issue.body" class="text-sm text-gray-600 dark:text-gray-300 line-clamp-2 mb-3">
              {{ issue.body }}
            </p>

            <div class="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
              <span class="flex items-center gap-1">
                <UIcon name="i-heroicons-user-16-solid" />
                {{ issue.author }}
              </span>
              <span class="flex items-center gap-1">
                <UIcon name="i-heroicons-chat-bubble-left-right-16-solid" />
                {{ issue.comment_count }} comments
              </span>
              <span class="flex items-center gap-1">
                <UIcon name="i-heroicons-calendar-16-solid" />
                {{ formatDate(issue.created_at) }}
              </span>
              <span v-if="issue.labels.length > 0" class="flex items-center gap-1">
                <UIcon name="i-heroicons-tag-16-solid" />
                {{ issue.labels.length }} label{{ issue.labels.length !== 1 ? 's' : '' }}
              </span>
            </div>

            <div v-if="issue.labels.length > 0" class="flex flex-wrap gap-1 mt-2">
              <UBadge
                v-for="label in issue.labels.slice(0, 5)"
                :key="label"
                variant="soft"
                size="xs"
              >
                {{ label }}
              </UBadge>
              <UBadge
                v-if="issue.labels.length > 5"
                variant="outline"
                size="xs"
              >
                +{{ issue.labels.length - 5 }} more
              </UBadge>
            </div>
          </div>

          <div class="flex items-center gap-2 ml-4">
            <UButton
              :to="issue.url"
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
        :total="filteredIssues.length"
        :max="7"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { GitHubIssue, GitHubFilters } from '~/types/github'

interface Props {
  repositoryId: number
  issues?: GitHubIssue[]
  loading?: boolean
  error?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  issues: () => [],
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
  { value: 'all', label: 'All Issues' },
  { value: 'open', label: 'Open Only' },
  { value: 'closed', label: 'Closed Only' }
]

const stats = computed(() => githubStore.stats)

const filteredIssues = computed(() => {
  let filtered = props.issues

  if (filters.value.state !== 'all') {
    filtered = filtered.filter(issue => issue.state === filters.value.state)
  }

  if (filters.value.author) {
    filtered = filtered.filter(issue =>
      issue.author.toLowerCase().includes(filters.value.author.toLowerCase())
    )
  }

  if (filters.value.search) {
    const search = filters.value.search.toLowerCase()
    filtered = filtered.filter(issue =>
      issue.title.toLowerCase().includes(search) ||
      issue.body.toLowerCase().includes(search)
    )
  }

  return filtered
})

const totalPages = computed(() => Math.ceil(filteredIssues.value.length / pageSize))

const paginatedIssues = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  const end = start + pageSize
  return filteredIssues.value.slice(start, end)
})

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

const refreshIssues = () => {
  emit('refresh')
}

watch(filters, (newFilters) => {
  currentPage.value = 1
  emit('filterChange', newFilters)
}, { deep: true })

watch(() => props.issues, () => {
  currentPage.value = 1
}, { deep: true })
</script>
