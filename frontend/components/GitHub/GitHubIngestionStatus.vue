<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div
          class="w-3 h-3 rounded-full"
          :class="statusIndicatorClass"
        ></div>
        <h3 class="text-lg font-semibold text-foreground">
          Ingestion Status
        </h3>
      </div>

      <UButton
        v-if="showRefreshButton"
        icon="i-heroicons-arrow-path-16-solid"
        variant="ghost"
        color="gray"
        size="xs"
        :loading="refreshing"
        @click="refreshStatus"
      >
        Refresh
      </UButton>
    </div>

    <div class="bg-card rounded-lg border border-border p-4">
      <div v-if="status === 'running'" class="space-y-4">
        <div class="flex items-center gap-3">
          <UIcon name="i-heroicons-arrow-path-16-solid" class="animate-spin text-primary" />
          <span class="text-primary font-medium">
            Ingestion in Progress
          </span>
        </div>

        <div class="space-y-2">
          <div class="flex justify-between text-sm text-muted-foreground">
            <span>{{ currentStep }}</span>
            <span>{{ Math.round(progress) }}%</span>
          </div>
          <div class="w-full bg-muted rounded-full h-2">
            <div
              class="bg-primary h-2 rounded-full transition-all duration-300"
              :style="{ width: `${progress}%` }"
            ></div>
          </div>
        </div>

        <div class="bg-primary/10 rounded-lg p-3">
          <div class="flex items-center gap-2 text-sm">
            <UIcon name="i-heroicons-information-circle-16-solid" class="text-primary" />
            <span class="text-primary">
              {{ currentOperation }}
            </span>
          </div>
        </div>

        <div v-if="estimatedTime" class="text-sm text-muted-foreground">
          Estimated completion: {{ estimatedTime }}
        </div>
      </div>

      <div v-else-if="status === 'completed'" class="space-y-4">
        <div class="flex items-center gap-3">
          <UIcon name="i-heroicons-check-circle-16-solid" class="text-green-600" />
          <span class="text-green-600 font-medium">
            Ingestion Completed Successfully
          </span>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="text-center">
            <div class="text-lg font-semibold text-foreground">
              {{ summary.issues }}
            </div>
            <div class="text-xs text-muted-foreground">Issues</div>
          </div>
          <div class="text-center">
            <div class="text-lg font-semibold text-foreground">
              {{ summary.pullRequests }}
            </div>
            <div class="text-xs text-muted-foreground">Pull Requests</div>
          </div>
          <div class="text-center">
            <div class="text-lg font-semibold text-foreground">
              {{ summary.discussions }}
            </div>
            <div class="text-xs text-muted-foreground">Discussions</div>
          </div>
          <div class="text-center">
            <div class="text-lg font-semibold text-foreground">
              {{ summary.files }}
            </div>
            <div class="text-xs text-muted-foreground">Files</div>
          </div>
        </div>

        <div class="text-sm text-gray-500 dark:text-gray-400">
          Completed {{ completedAt }}
        </div>
      </div>

      <div v-else-if="status === 'failed'" class="space-y-4">
        <div class="flex items-center gap-3">
          <UIcon name="i-heroicons-x-circle-16-solid" class="text-red-600" />
          <span class="text-red-600 dark:text-red-400 font-medium">
            Ingestion Failed
          </span>
        </div>

        <div class="bg-red-50 dark:bg-red-900/20 rounded-lg p-3">
          <div class="flex items-start gap-2">
            <UIcon name="i-heroicons-exclamation-triangle-16-solid" class="text-red-600 mt-0.5" />
            <div class="flex-1">
              <p class="text-sm text-red-800 dark:text-red-200">
                {{ errorMessage }}
              </p>
              <p v-if="errorDetails" class="text-xs text-red-600 dark:text-red-400 mt-1">
                {{ errorDetails }}
              </p>
            </div>
          </div>
        </div>

        <div class="flex gap-3">
          <UButton
            icon="i-heroicons-arrow-path-16-solid"
            size="sm"
            @click="retryIngestion"
          >
            Retry
          </UButton>
          <UButton
            variant="outline"
            color="gray"
            size="sm"
            @click="viewLogs"
          >
            View Logs
          </UButton>
        </div>
      </div>

      <div v-else class="space-y-4">
        <div class="flex items-center gap-3">
          <UIcon name="i-heroicons-clock-16-solid" class="text-gray-600" />
          <span class="text-gray-600 dark:text-gray-400 font-medium">
            Waiting to Start
          </span>
        </div>

        <div class="text-sm text-gray-500 dark:text-gray-400">
          Ingestion is queued and will start shortly.
        </div>
      </div>
    </div>

    <div v-if="status === 'running' && detailedProgress" class="space-y-3">
      <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300">
        Detailed Progress
      </h4>

      <div class="space-y-2">
        <div
          v-for="step in progressSteps"
          :key="step.name"
          class="flex items-center gap-3"
        >
          <div class="w-4 h-4 rounded-full flex items-center justify-center"
               :class="stepStatusClass(step.status)"
          >
            <UIcon
              v-if="step.status === 'completed'"
              name="i-heroicons-check-16-solid"
              class="w-2 h-2 text-white"
            />
            <UIcon
              v-else-if="step.status === 'running'"
              name="i-heroicons-arrow-path-16-solid"
              class="w-2 h-2 text-white animate-spin"
            />
          </div>

          <div class="flex-1">
            <div class="text-sm font-medium text-gray-900 dark:text-white">
              {{ step.name }}
            </div>
            <div v-if="step.details" class="text-xs text-gray-500 dark:text-gray-400">
              {{ step.details }}
            </div>
          </div>

          <div v-if="step.progress !== undefined" class="text-xs text-gray-500 dark:text-gray-400">
            {{ step.progress }}%
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress?: number
  currentStep?: string
  currentOperation?: string
  estimatedTime?: string
  completedAt?: string
  errorMessage?: string
  errorDetails?: string
  summary?: {
    issues: number
    pullRequests: number
    discussions: number
    files: number
  }
  showRefreshButton?: boolean
  detailedProgress?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  progress: 0,
  showRefreshButton: true,
  detailedProgress: false
})

const emit = defineEmits<{
  refresh: []
  retry: []
  viewLogs: []
}>()

const refreshing = ref(false)

const progressSteps = ref([
  { name: 'Fetching repository info', status: 'completed', details: 'Repository metadata retrieved' },
  { name: 'Ingesting issues', status: 'running', progress: 75, details: 'Processing 127 issues...' },
  { name: 'Ingesting pull requests', status: 'pending', details: 'Waiting to start' },
  { name: 'Ingesting discussions', status: 'pending', details: 'Waiting to start' },
  { name: 'Ingesting wiki pages', status: 'pending', details: 'Waiting to start' },
  { name: 'Processing repository files', status: 'pending', details: 'Waiting to start' },
  { name: 'Creating knowledge base', status: 'pending', details: 'Waiting to start' }
])

const statusIndicatorClass = computed(() => {
  switch (props.status) {
    case 'running':
      return 'bg-blue-600 animate-pulse'
    case 'completed':
      return 'bg-green-600'
    case 'failed':
      return 'bg-red-600'
    default:
      return 'bg-gray-600'
  }
})

const stepStatusClass = (status: string) => {
  switch (status) {
    case 'completed':
      return 'bg-green-600'
    case 'running':
      return 'bg-blue-600 animate-pulse'
    case 'failed':
      return 'bg-red-600'
    default:
      return 'bg-gray-300 dark:bg-gray-600'
  }
}

const refreshStatus = async () => {
  refreshing.value = true
  try {
    emit('refresh')
  } finally {
    refreshing.value = false
  }
}

const retryIngestion = () => {
  emit('retry')
}

const viewLogs = () => {
  emit('viewLogs')
}

watch(() => props.progress, (newProgress) => {
  if (newProgress <= 20) {
    progressSteps.value[0].status = 'running'
    progressSteps.value[0].progress = newProgress * 5
  } else if (newProgress <= 50) {
    progressSteps.value[0].status = 'completed'
    progressSteps.value[1].status = 'running'
    progressSteps.value[1].progress = ((newProgress - 20) / 30) * 100
  } else if (newProgress <= 70) {
    progressSteps.value[0].status = 'completed'
    progressSteps.value[1].status = 'completed'
    progressSteps.value[2].status = 'running'
    progressSteps.value[2].progress = ((newProgress - 50) / 20) * 100
  } else if (newProgress <= 85) {
    progressSteps.value[0].status = 'completed'
    progressSteps.value[1].status = 'completed'
    progressSteps.value[2].status = 'completed'
    progressSteps.value[3].status = 'running'
    progressSteps.value[3].progress = ((newProgress - 70) / 15) * 100
  } else if (newProgress <= 95) {
    progressSteps.value[0].status = 'completed'
    progressSteps.value[1].status = 'completed'
    progressSteps.value[2].status = 'completed'
    progressSteps.value[3].status = 'completed'
    progressSteps.value[4].status = 'running'
    progressSteps.value[4].progress = ((newProgress - 85) / 10) * 100
  } else {
    progressSteps.value.forEach((step, index) => {
      if (index < 5) {
        step.status = 'completed'
        step.progress = 100
      } else if (index === 5 && newProgress < 100) {
        step.status = 'running'
        step.progress = ((newProgress - 95) / 5) * 100
      } else if (index === 6 && newProgress >= 100) {
        step.status = 'running'
        step.progress = 50
      }
    })
  }
}, { immediate: true })
</script>
