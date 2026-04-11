<template>
  <div class="flex flex-col h-screen p-4 pt-[72px] pb-[120px] overflow-y-auto">
    <div class="w-full space-y-2">
      <div
        v-if="requiredStepsIncomplete"
        class="flex flex-col items-center justify-center w-full px-6 py-12 max-w-4xl mx-auto gap-8"
      >
        <span
          v-if="currentStep <= 2"
          class="text-xs font-medium text-muted-foreground bg-muted px-3 py-1 rounded-full"
        >
          Step {{ currentStep }} of 2
        </span>

        <div
          v-if="currentStep === 1"
          class="w-full max-w-lg space-y-4"
        >
          <div class="space-y-1">
            <h2 class="text-xl font-semibold">
              Connect an AI Provider
            </h2>
            <p class="text-sm text-muted-foreground">
              To use the knowledge base, you'll need to connect at least one AI provider. This lets the app generate embeddings for your content.
            </p>
          </div>
          <NewAIProvider :inline="true" />
        </div>

        <div
          v-else-if="currentStep === 2"
          class="w-full max-w-lg space-y-4"
        >
          <div class="space-y-1">
            <h2 class="text-xl font-semibold">
              Configure an Embedding Model
            </h2>
            <p class="text-sm text-muted-foreground">
              Select the embedding model that will process and index your knowledge base content.
            </p>
          </div>
          <ConfigureAIModels :config="embeddingModelConfig" />
        </div>
      </div>

      <template v-else>
        <div
          v-if="!isLoading && kbs.length > 0"
          class="flex gap-2 items-center py-4"
        >
          <div class="ml-auto">
            <NewKnowledgeBase :application="{ uuid: $route.params.appId }" />
          </div>
        </div>

        <C8Item
          v-for="kb in kbs"
          :key="kb.uuid"
          :icon="getKBIcon(kb.source_type)"
          container-class="w-full"
          item-class="w-full"
        >
          <template #title>
            {{ getKBTitle(kb) }}
          </template>
          <template #details>
            <ItemDescription>
              <div class="inline-flex items-center space-x-3">
                <div class="flex items-center space-x-1">
                  <component
                    :is="getSourceTypeIcon(kb.source_type)"
                    class="w-4 h-4"
                  />
                  <div>{{ getSourceTypeLabel(kb.source_type) }}</div>
                </div>
                <div
                  v-if="kb.source_type === 'url' && kb.metadata?.crawling_enabled"
                  class="flex items-center space-x-1"
                >
                  <Globe class="w-4 h-4 text-blue-500" />
                  <Badge
                    :variant="getCrawlingStatusVariant(kb.metadata?.crawling_status)"
                    class="text-xs"
                  >
                    {{ getCrawlingStatusText(kb.metadata?.crawling_status) }}
                  </Badge>
                </div>
              </div>

              <div
                v-if="kb.source_type === 'url'"
                class="mt-2 space-y-1"
              >
                <div
                  v-if="kb.metadata?.title"
                  class="text-sm font-medium"
                >
                  {{ kb.metadata.title }}
                </div>
                <div
                  v-if="kb.metadata?.description"
                  class="text-sm text-muted-foreground line-clamp-2 w-full pr-12"
                >
                  {{ kb.metadata.description }}
                </div>
                <div
                  v-else-if="kb.metadata?.content"
                  class="text-sm text-muted-foreground line-clamp-2 w-full pr-12"
                >
                  {{ kb.metadata.content.substring(0, 300) }}{{ kb.metadata.content.length > 300 ? '...' : '' }}
                </div>
              </div>

              <div
                v-else-if="kb.metadata?.content"
                class="mt-2 text-sm text-muted-foreground line-clamp-2 w-full pr-12"
              >
                {{ kb.metadata.content.substring(0, 300) }}{{ kb.metadata.content.length > 300 ? '...' : '' }}
              </div>
            </ItemDescription>
          </template>

          <template #before-dropdown>
            <Badge :variant="getStatusVariant(kb.status)">
              {{ STATUS_LABELS[kb.status as StatusType] || kb.status }}
            </Badge>
          </template>

          <template #dropdown>
            <DropdownMenuItem
              @click="openDetailsDialog(kb)"
            >
              <Eye class="h-4 w-4" />
              View Details
            </DropdownMenuItem>

            <template v-if="kb.source_type === 'url' && kb.metadata?.crawling_enabled">
              <DropdownMenuSeparator />
            </template>

            <DropdownMenuSeparator />
            <DropdownMenuItem
              class="text-destructive"
              @click="openDeleteDialog(kb)"
            >
              <Trash class="h-4 w-4 text-destructive" />
              Delete
            </DropdownMenuItem>
          </template>
        </C8Item>

        <div
          v-if="isLoading"
          class="text-center py-8"
        >
          Loading...
        </div>

        <div
          v-if="!isLoading && kbs.length === 0"
          class="text-center py-8"
        >
          <C8Empty
            :icon="Layers"
            title="Your knowledge base is empty"
            description="Add files, URLs, or text..."
          >
            <template #action>
              <NewKnowledgeBase :application="{ uuid: String($route.params.appId) }" />
            </template>
          </C8Empty>
        </div>
      </template>

      <C8Dialog
        v-model:open="isDeleteDialogOpen"
        :title="`Delete Knowledge Base Item`"
        :confirm-text="'Delete'"
        :destructive="true"
        @confirm="confirmDelete"
      >
        <template #description>
          <div>
            Are you sure you want to delete <span class="font-bold">{{ kbToDelete?.metadata?.file_name || kbToDelete?.path || 'this item' }}</span>?
          </div>
        </template>
      </C8Dialog>

      <C8Dialog
        v-model:open="isDetailsDialogOpen"
        :title="'Knowledge Base Details'"
        :confirm-text="'Close'"
        :show-cancel="false"
      >
        <template #description>
          <div
            v-if="selectedKB"
            class="space-y-4"
          >
            <div>
              <Label class="text-sm font-medium">Type</Label>
              <p class="text-sm capitalize">
                {{ selectedKB.source_type }}
              </p>
            </div>

            <div>
              <Label class="text-sm font-medium">Path/URL</Label>
              <p
                v-if="selectedKB.source_type === 'url'"
                class="text-sm"
              >
                <a
                  :href="selectedKB.path"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-blue-600 hover:text-blue-800 break-all"
                >
                  {{ selectedKB.path }}
                </a>
              </p>
              <p
                v-else
                class="text-sm text-muted-foreground"
              >
                {{ selectedKB.path }}
              </p>
            </div>

            <div>
              <div>
                <div v-if="selectedKB.source_type === 'url'">
                  <div class="bg-muted/50 p-3 my-2 rounded-lg w-full max-w-md">
                    <div v-if="selectedKB.metadata?.links?.length > 0">
                      <div class="text-sm font-medium mb-2 text-green-600">
                        🔗 Found {{ selectedKB.metadata.links.length }} links:
                      </div>
                      <div class="relative">
                        <div class="space-y-2 max-h-48 overflow-y-auto pr-2">
                          <div
                            v-for="(link, index) in selectedKB.metadata.links.slice(0, 3)"
                            :key="index"
                            class="flex items-start gap-2 p-2 bg-background rounded border"
                          >
                            <div class="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium">
                              {{ index + 1 }}
                            </div>
                            <div class="flex-1 min-w-0">
                              <div
                                class="text-sm font-medium truncate"
                                :title="link.url || link"
                              >
                                {{ link.url || link }}
                              </div>
                              <div
                                v-if="link.title"
                                class="text-xs text-muted-foreground truncate"
                                :title="link.title"
                              >
                                {{ link.title }}
                              </div>
                            </div>
                          </div>
                        </div>
                        <div
                          v-if="selectedKB.metadata.links.length > 3"
                          class="text-center py-2"
                        >
                          <button
                            class="text-xs text-blue-600 hover:text-blue-700 underline"
                            @click="showAllLinks = !showAllLinks"
                          >
                            {{ showAllLinks ? 'Show less' : `Show ${selectedKB.metadata.links.length - 3} more links` }}
                          </button>
                        </div>
                        <div
                          v-if="showAllLinks"
                          class="space-y-2 max-h-48 overflow-y-auto pr-2"
                        >
                          <div
                            v-for="(link, index) in selectedKB.metadata.links.slice(3)"
                            :key="index + 3"
                            class="flex items-start gap-2 p-2 bg-background rounded border"
                          >
                            <div class="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium">
                              {{ index + 4 }}
                            </div>
                            <div class="flex-1 min-w-0">
                              <div
                                class="text-sm font-medium truncate"
                                :title="link.url || link"
                              >
                                {{ link.url || link }}
                              </div>
                              <div
                                v-if="link.title"
                                class="text-xs text-muted-foreground truncate"
                                :title="link.title"
                              >
                                {{ link.title }}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div
                      v-else
                      class="text-sm text-muted-foreground text-center py-4"
                    >
                      <div
                        v-if="selectedKB.metadata?.extraction_status === 'pending'"
                        class="text-blue-600"
                      >
                        ⏳ URL is being processed...
                      </div>
                      <div
                        v-else-if="selectedKB.metadata?.extraction_status === 'failed'"
                        class="text-red-600"
                      >
                        ❌ URL processing failed. Check the error details below.
                      </div>
                      <div
                        v-else-if="selectedKB.metadata?.extraction_status === 'completed'"
                        class="text-orange-600"
                      >
                        ⚠️ URL processed but no links were found.
                      </div>
                      <div
                        v-else
                        class="text-gray-600"
                      >
                        🔗 No links found for this URL.
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="selectedKB.metadata?.title || selectedKB.metadata?.description">
                <Label class="text-sm font-medium">Page Information</Label>
                <div class="space-y-2">
                  <div v-if="selectedKB.metadata.title">
                    <span class="text-xs text-muted-foreground">Title:</span>
                    <p class="text-sm">
                      {{ selectedKB.metadata.title }}
                    </p>
                  </div>
                  <div v-if="selectedKB.metadata.description">
                    <span class="text-xs text-muted-foreground">Description:</span>
                    <p class="text-sm">
                      {{ selectedKB.metadata.description }}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <Label class="text-sm font-medium">Content Length</Label>
                <p class="text-sm">
                  {{ selectedKB.metadata?.content_length?.toLocaleString() || 0 }} characters
                </p>
              </div>
              <div>
                <Label class="text-sm font-medium">Status</Label>
                <StatusBadge :status="selectedKB.status" />
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <Label class="text-sm font-medium">Content Type</Label>
                <p class="text-sm">
                  {{ selectedKB.metadata?.content_type || 'Unknown' }}
                </p>
              </div>
              <div v-if="selectedKB.source_type === 'url'">
                <Label class="text-sm font-medium">Links Found</Label>
                <p class="text-sm">
                  {{ selectedKB.metadata?.links_count || 0 }} links
                </p>
              </div>
            </div>

            <div>
              <Label class="text-sm font-medium">Created</Label>
              <p class="text-sm">
                {{ formatDate(selectedKB.created_at) }}
              </p>
            </div>

            <div v-if="selectedKB.metadata?.extraction_timestamp">
              <Label class="text-sm font-medium">Last Extracted</Label>
              <p class="text-sm">
                {{ formatDate(selectedKB.metadata.extraction_timestamp) }}
              </p>
            </div>

            <div v-if="selectedKB.metadata?.extraction_error">
              <Label class="text-sm font-medium text-destructive">Extraction Error</Label>
              <p class="text-sm text-destructive">
                {{ selectedKB.metadata.extraction_error }}
              </p>
            </div>
          </div>
        </template>
      </C8Dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import NewKnowledgeBase from '~/components/KnowledgeBase/NewKnowledgeBase.vue'
import NewAIProvider from '~/components/AIProvider/NewAIProvider.vue'
import ConfigureAIModels from '~/components/App/ConfigureAIModels.vue'
import StatusBadge from '~/components/KnowledgeBase/StatusBadge.vue'
import C8Dialog from '~/components/C8Dialog.vue'
import { toast } from 'vue-sonner'
import C8Item from '~/components/C8Item.vue'
import { ItemDescription } from '~/components/ui/item'
import { DropdownMenuItem, DropdownMenuSeparator } from '@/components/ui/dropdown-menu'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import {
  File, FileText, FolderGit2, LetterText, Trash, Globe, Eye,
  RefreshCw, CheckCircle, Layers
} from 'lucide-vue-next'
import { KB_UPDATE, STATUS_LABELS } from '~/lib/consts'
import type { StatusType } from '~/lib/consts'

const route = useRoute()
const router = useRouter()
const kbStore = useKnowledgeBaseStore()
const liveUpdateStore = useLiveUpdateStore()
const AIProviderStore = useAIProviderStore()
const AppAIProviderStore = useAppAIProviderStore()

const isLoading = ref(true)
const isDeleteDialogOpen = ref(false)
const isDetailsDialogOpen = ref(false)
const isCrawlingDialogOpen = ref(false)
const kbToDelete = ref(null)
const showAllLinks = ref(false)
const selectedKB = ref(null)

const kbs = computed(() => kbStore.kbs)

const hasAIProvider = computed(() => AIProviderStore.AIProviders.length > 0)
const hasEmbeddingModel = computed(() =>
  AppAIProviderStore.existingAppAIProviderConfigs.some(
    c => c.capability === 'embedding',
  ),
)

const requiredStepsIncomplete = computed(() =>
  !hasAIProvider.value || !hasEmbeddingModel.value,
)

const currentStep = computed(() => {
  if (!hasAIProvider.value) return 1
  if (!hasEmbeddingModel.value) return 2
  return 3
})

const embeddingModelConfig = {
  title: 'Embedding Model',
  description: 'Select the model that will generate embeddings for your knowledge base content.',
  modelLabel: 'Model',
  modelPlaceholder: 'Select an embedding model',
  capability: 'embedding',
  context: 'response',
  successMessage: 'Embedding model configured',
}

onMounted(async () => {
  await Promise.allSettled([
    kbStore.load(),
    AIProviderStore.load(),
    AppAIProviderStore.fetchAppAIProviderConfigs(String(route.params.appId)),
  ])
  isLoading.value = false
})

onBeforeUnmount(() => {
  liveUpdateStore.leave()
})

function getKBIcon(sourceType: string) {
  switch (sourceType) {
    case 'file': return File
    case 'text': return LetterText
    case 'url': return Globe
    case 'github': return FolderGit2
    default: return File
  }
}

function getSourceTypeIcon(sourceType: string) {
  switch (sourceType) {
    case 'file': return File
    case 'text': return LetterText
    case 'url': return Globe
    case 'github': return FolderGit2
    default: return File
  }
}

function getSourceTypeLabel(sourceType: string) {
  switch (sourceType) {
    case 'file': return 'File'
    case 'text': return 'Text'
    case 'url': return 'URL'
    case 'github': return 'GitHub'
    default: return sourceType
  }
}

function getKBTitle(kb: any) {
  if (kb.source_type === 'url') {
    return kb.metadata?.title || kb.path
  } else if (kb.source_type === 'file') {
    return kb.metadata?.file_name || kb.path
  } else {
    return kb.path
  }
}

function getStatusVariant(status: string) {
  switch (status) {
    case 'completed': return 'default'
    case 'failed': return 'destructive'
    case 'processing': return 'secondary'
    default: return 'outline'
  }
}

function getCrawlingStatusVariant(status?: string) {
  switch (status) {
    case 'completed': return 'default'
    case 'failed': return 'destructive'
    case 'in_progress': return 'secondary'
    default: return 'outline'
  }
}

function getCrawlingStatusText(status?: string) {
  switch (status) {
    case 'completed': return 'Completed'
    case 'failed': return 'Failed'
    case 'in_progress': return 'In Progress'
    case 'not_started': return 'Not Started'
    default: return 'Unknown'
  }
}

function formatBytes(bytes: number) {
  if (bytes === 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
}

function getStatusColor(statusCode: number) {
  if (statusCode >= 200 && statusCode < 300) return 'text-green-600'
  if (statusCode >= 300 && statusCode < 400) return 'text-blue-600'
  if (statusCode >= 400 && statusCode < 500) return 'text-orange-600'
  if (statusCode >= 500) return 'text-red-600'
  return 'text-muted-foreground'
}

function formatDate(dateString: string) {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString()
}

function formatPercentage(value: number) {
  return `${(value * 100).toFixed(1)}%`
}

function openDetailsDialog(kb: any) {
  selectedKB.value = kb
  isDetailsDialogOpen.value = true
}

function openDeleteDialog(kb: any) {
  kbToDelete.value = kb
  isDeleteDialogOpen.value = true
}

async function confirmDelete() {
  if (!kbToDelete.value) return

  try {
    await kbStore.delete(kbToDelete.value.uuid)
    toast.success('Knowledge base item deleted successfully')
    isDeleteDialogOpen.value = false
    kbToDelete.value = null
  } catch (error) {
    toast.error('Failed to delete knowledge base item')
  }
}
</script>
