<template>
  <div class="space-y-4">
    <div class="border rounded-lg p-4 bg-card">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-lg font-semibold flex items-center gap-2">
          <Globe class="w-5 h-5 text-blue-500" />
          Web Crawling Progress
        </h3>
        <Badge :variant="getStatusVariant(crawlingStatus)">
          {{ getStatusText(crawlingStatus) }}
        </Badge>
      </div>

      <div class="space-y-2">
        <div class="flex justify-between text-sm">
          <span>Pages Crawled</span>
          <span>{{ crawledPages }} / {{ totalPages }}</span>
        </div>
        <Progress
          :value="progressPercentage"
          class="w-full"
          :class="getProgressVariant(crawlingStatus)"
        />
      </div>

      <div class="grid grid-cols-3 gap-4 mt-4">
        <div class="text-center">
          <div class="text-2xl font-bold text-blue-600">{{ crawledPages }}</div>
          <div class="text-xs text-muted-foreground">Pages</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-green-600">{{ successRate }}%</div>
          <div class="text-xs text-muted-foreground">Success</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-purple-600">{{ maxDepthReached }}</div>
          <div class="text-xs text-muted-foreground">Max Depth</div>
        </div>
      </div>
    </div>

    <div v-if="showDetails && crawlStats" class="border rounded-lg p-4 bg-card">
      <h4 class="text-md font-semibold mb-3 flex items-center gap-2">
        <BarChart3 class="w-4 h-4" />
        Detailed Statistics
      </h4>

      <div class="grid grid-cols-2 gap-6">
        <div class="space-y-3">
          <h5 class="text-sm font-medium text-muted-foreground">URL Discovery</h5>
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span>Total URLs Encountered</span>
              <span class="font-mono">{{ crawlStats.total_urls_encountered }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span>URLs Visited</span>
              <span class="font-mono">{{ crawlStats.total_urls_visited }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span>Duplicates Found</span>
              <span class="font-mono">{{ crawlStats.deduplication_stats.duplicates_found }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span>Deduplication Rate</span>
              <span class="font-mono">{{ formatPercentage(crawlStats.deduplication_stats.deduplication_rate) }}</span>
            </div>
          </div>
        </div>

        <div class="space-y-3">
          <h5 class="text-sm font-medium text-muted-foreground">Content Analysis</h5>
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span>Total Content Length</span>
              <span class="font-mono">{{ formatBytes(crawlStats.total_content_length) }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span>Avg Content Length</span>
              <span class="font-mono">{{ formatBytes(crawlStats.average_content_length) }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span>Parent URLs</span>
              <span class="font-mono">{{ crawlStats.relationship_stats.parent_urls }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span>Avg Children per Parent</span>
              <span class="font-mono">{{ crawlStats.relationship_stats.avg_children_per_parent.toFixed(1) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="Object.keys(crawlStats.depth_distribution).length > 0" class="mt-4">
        <h5 class="text-sm font-medium text-muted-foreground mb-2">Depth Distribution</h5>
        <div class="space-y-1">
          <div
            v-for="(count, depth) in crawlStats.depth_distribution"
            :key="depth"
            class="flex items-center gap-2"
          >
            <span class="text-sm w-12">Depth {{ depth }}:</span>
            <div class="flex-1 bg-muted rounded-full h-2">
              <div
                class="bg-blue-500 h-2 rounded-full"
                :style="{ width: `${(count / crawledPages) * 100}%` }"
              />
            </div>
            <span class="text-sm font-mono w-8 text-right">{{ count }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="errorSummary && errorSummary.failed_attempts > 0" class="border rounded-lg p-4 bg-card border-red-200">
      <h4 class="text-md font-semibold mb-3 flex items-center gap-2 text-red-600">
        <AlertCircle class="w-4 h-4" />
        Error Summary
      </h4>

      <div class="space-y-2">
        <div class="flex justify-between text-sm">
          <span>Failed Attempts</span>
          <span class="font-mono text-red-600">{{ errorSummary.failed_attempts }}</span>
        </div>
        <div class="flex justify-between text-sm">
          <span>Success Rate</span>
          <span class="font-mono">{{ formatPercentage(errorSummary.success_rate) }}</span>
        </div>

        <div v-if="Object.keys(errorSummary.error_counts).length > 0" class="mt-3">
          <h5 class="text-sm font-medium text-muted-foreground mb-2">Error Types</h5>
          <div class="space-y-1">
            <div
              v-for="(count, errorType) in errorSummary.error_counts"
              :key="errorType"
              class="flex justify-between text-sm"
            >
              <span class="text-red-600">{{ errorType }}</span>
              <span class="font-mono">{{ count }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="flex gap-2">
      <Button
        v-if="crawlingStatus === 'completed' && showRetryButton"
        variant="outline"
        @click="$emit('retry-crawling')"
      >
        <RefreshCw class="w-4 h-4 mr-2" />
        Retry Crawling
      </Button>

      <Button
        variant="outline"
        @click="$emit('toggle-details')"
      >
        <Eye class="w-4 h-4 mr-2" />
        {{ showDetails ? 'Hide' : 'Show' }} Details
      </Button>

      <Button
        v-if="crawlingStatus === 'completed'"
        variant="outline"
        @click="$emit('view-crawled-pages')"
      >
        <FileText class="w-4 h-4 mr-2" />
        View Pages
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Globe, BarChart3, AlertCircle, RefreshCw, Eye, FileText } from 'lucide-vue-next'

interface CrawlStats {
  total_pages: number
  total_urls_visited: number
  total_urls_encountered: number
  success_rate: number
  max_depth_reached: number
  total_content_length: number
  average_content_length: number
  deduplication_stats: {
    duplicates_found: number
    deduplication_rate: number
  }
  relationship_stats: {
    parent_urls: number
    total_child_links: number
    avg_children_per_parent: number
  }
  depth_distribution: Record<number, number>
}

interface ErrorSummary {
  total_attempts: number
  successful_attempts: number
  failed_attempts: number
  success_rate: number
  error_counts: Record<string, number>
  error_urls: Record<string, string[]>
}

const props = withDefaults(defineProps<{
  crawlingStatus?: string
  crawledPages?: number
  totalPages?: number
  crawlStats?: CrawlStats
  errorSummary?: ErrorSummary
  showDetails?: boolean
  showRetryButton?: boolean
}>(), {
  crawlingStatus: 'not_started',
  crawledPages: 0,
  totalPages: 0,
  showDetails: false,
  showRetryButton: true
})

const emit = defineEmits<{
  'retry-crawling': []
  'toggle-details': []
  'view-crawled-pages': []
}>()

const progressPercentage = computed(() => {
  if (props.totalPages === 0) return 0
  return Math.min((props.crawledPages / props.totalPages) * 100, 100)
})

const successRate = computed(() => {
  if (props.crawlStats) {
    return Math.round(props.crawlStats.success_rate * 100)
  }
  if (props.errorSummary) {
    return Math.round(props.errorSummary.success_rate * 100)
  }
  return 0
})

const maxDepthReached = computed(() => {
  return props.crawlStats?.max_depth_reached || 0
})

function getStatusVariant(status: string) {
  switch (status) {
    case 'completed': return 'default'
    case 'failed': return 'destructive'
    case 'in_progress': return 'secondary'
    default: return 'outline'
  }
}

function getStatusText(status: string) {
  switch (status) {
    case 'completed': return 'Completed'
    case 'failed': return 'Failed'
    case 'in_progress': return 'In Progress'
    case 'not_started': return 'Not Started'
    default: return 'Unknown'
  }
}

function getProgressVariant(status: string) {
  switch (status) {
    case 'completed': return '[&>div]:bg-green-500'
    case 'failed': return '[&>div]:bg-red-500'
    case 'in_progress': return '[&>div]:bg-blue-500'
    default: return '[&>div]:bg-gray-500'
  }
}

function formatPercentage(value: number) {
  return `${(value * 100).toFixed(1)}%`
}

function formatBytes(bytes: number) {
  if (bytes === 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
}
</script>
