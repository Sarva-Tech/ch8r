<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 p-6 transition-all duration-200 hover:shadow-lg">
    <div class="flex items-start justify-between mb-4">
      <div class="flex-1">
        <div class="flex items-center gap-2 mb-2">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            {{ repository.name }}
          </h3>
          <span class="text-sm text-gray-500 dark:text-gray-400">
            {{ repository.owner }}
          </span>
        </div>
        <p class="text-sm text-gray-600 dark:text-gray-300 mb-2">
          {{ repository.full_name }}
        </p>
        <p v-if="repository.description" class="text-sm text-gray-700 dark:text-gray-300 line-clamp-2">
          {{ repository.description }}
        </p>
      </div>

      <div class="flex items-center gap-2">
        <UBadge
          :color="statusColor"
          :variant="statusVariant"
          class="text-xs"
        >
          {{ statusText }}
        </UBadge>

        <UDropdown
          v-if="showActions"
          :items="actionItems"
          :popper="{ placement: 'bottom-end' }"
        >
          <UButton
            icon="i-heroicons-ellipsis-horizontal-20-solid"
            variant="ghost"
            color="gray"
            size="xs"
            square
          />
        </UDropdown>
      </div>
    </div>

    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
      <div class="text-center">
        <div class="text-lg font-semibold text-gray-900 dark:text-white">
          {{ repository.issue_count || 0 }}
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400">Issues</div>
      </div>
      <div class="text-center">
        <div class="text-lg font-semibold text-gray-900 dark:text-white">
          {{ repository.pr_count || 0 }}
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400">PRs</div>
      </div>
      <div class="text-center">
        <div class="text-lg font-semibold text-gray-900 dark:text-white">
          {{ repository.discussion_count || 0 }}
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400">Discussions</div>
      </div>
      <div class="text-center">
        <div class="text-lg font-semibold text-gray-900 dark:text-white">
          {{ repository.wiki_page_count || 0 }}
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400">Wiki Pages</div>
      </div>
    </div>

    <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
      <div class="flex items-center gap-4">
        <span v-if="repository.is_private" class="flex items-center gap-1">
          <UIcon name="i-heroicons-lock-closed-16-solid" />
          Private
        </span>
        <span v-else class="flex items-center gap-1">
          <UIcon name="i-heroicons-globe-alt-16-solid" />
          Public
        </span>
        <span class="flex items-center gap-1">
          <UIcon name="i-heroicons-code-bracket-16-solid" />
          {{ repository.default_branch }}
        </span>
      </div>

      <div class="flex items-center gap-2">
        <span v-if="repository.last_ingested_at">
          Last synced: {{ formatDate(repository.last_ingested_at) }}
        </span>
        <UButton
          :to="`/applications/${appId}/github/${repository.id}`"
          variant="ghost"
          color="primary"
          size="xs"
        >
          View Details
        </UButton>
      </div>
    </div>

    <div v-if="repository.ingestion_status === 'running'" class="mt-4">
      <div class="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400">
        <UIcon name="i-heroicons-arrow-path-16-solid" class="animate-spin" />
        Ingesting repository data...
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { GitHubRepository } from '~/types/github'

interface Props {
  repository: GitHubRepository
  appId: string
  showActions?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showActions: true
})

const emit = defineEmits<{
  delete: [repository: GitHubRepository]
  reIngest: [repository: GitHubRepository]
  refresh: [repository: GitHubRepository]
}>()

const githubStore = useGitHubStore()

const statusColor = computed(() => {
  switch (props.repository.ingestion_status) {
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
  switch (props.repository.ingestion_status) {
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
  switch (props.repository.ingestion_status) {
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

const actionItems = computed(() => [
  [
    {
      label: 'View Details',
      icon: 'i-heroicons-eye-16-solid',
      click: () => navigateTo(`/applications/${props.appId}/github/${props.repository.id}`)
    },
    {
      label: 'Refresh Data',
      icon: 'i-heroicons-arrow-path-16-solid',
      click: () => emit('refresh', props.repository)
    },
    {
      label: 'Re-ingest',
      icon: 'i-heroicons-arrow-down-tray-16-solid',
      click: () => emit('reIngest', props.repository)
    }
  ],
  [
    {
      label: 'Delete',
      icon: 'i-heroicons-trash-16-solid',
      click: () => emit('delete', props.repository)
    }
  ]
])

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString()
}
</script>
