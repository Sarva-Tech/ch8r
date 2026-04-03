<template>
  <div class="flex flex-col h-screen p-4 pt-[72px] pb-[120px] overflow-y-auto">
    <div class="w-full space-y-2">
      <div class="flex gap-2 items-center py-4">
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
            </div>
            <div
              v-if="kb.metadata?.content"
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
            <Eye class="h-4 w-4 mr-2" />
            View Details
          </DropdownMenuItem>
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
        Your knowledge base is empty.
      </div>

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
      >
        <template #description>
          <div v-if="selectedKB" class="space-y-4">
            <div>
              <Label class="text-sm font-medium">Type</Label>
              <p class="text-sm capitalize">{{ selectedKB.source_type }}</p>
            </div>

            <div>
              <Label class="text-sm font-medium">Path/URL</Label>
              <p v-if="selectedKB.source_type === 'url'" class="text-sm">
                <a
                  :href="selectedKB.path"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-blue-600 hover:text-blue-800 break-all"
                >
                  {{ selectedKB.path }}
                </a>
              </p>
              <p v-else class="text-sm text-muted-foreground">{{ selectedKB.path }}</p>
            </div>

            <div v-if="selectedKB.metadata?.title">
              <Label class="text-sm font-medium">Title</Label>
              <p class="text-sm">{{ selectedKB.metadata.title }}</p>
            </div>

            <div v-if="selectedKB.metadata?.description">
              <Label class="text-sm font-medium">Description</Label>
              <p class="text-sm">{{ selectedKB.metadata.description }}</p>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <Label class="text-sm font-medium">Status</Label>
                <StatusBadge :status="selectedKB.status" />
              </div>
              <div>
                <Label class="text-sm font-medium">Content Type</Label>
                <p class="text-sm">{{ selectedKB.metadata?.content_type || 'Unknown' }}</p>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <Label class="text-sm font-medium">Content Length</Label>
                <p class="text-sm">{{ selectedKB.metadata?.content_length?.toLocaleString() || 0 }} characters</p>
              </div>
              <div v-if="selectedKB.source_type === 'url'">
                <Label class="text-sm font-medium">Links Found</Label>
                <p class="text-sm">{{ selectedKB.metadata?.links_count || 0 }} links</p>
              </div>
            </div>

            <div>
              <Label class="text-sm font-medium">Created</Label>
              <p class="text-sm">{{ formatDate(selectedKB.created_at) }}</p>
            </div>

            <div v-if="selectedKB.metadata?.extraction_timestamp">
              <Label class="text-sm font-medium">Last Extracted</Label>
              <p class="text-sm">{{ formatDate(selectedKB.metadata.extraction_timestamp) }}</p>
            </div>

            <div v-if="selectedKB.metadata?.extraction_error">
              <Label class="text-sm font-medium text-destructive">Error</Label>
              <p class="text-sm text-destructive">{{ selectedKB.metadata.extraction_error }}</p>
            </div>
          </div>
        </template>
      </C8Dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import NewKnowledgeBase from '~/components/KnowledgeBase/NewKnowledgeBase.vue'
import StatusBadge from '~/components/KnowledgeBase/StatusBadge.vue'
import C8Dialog from '~/components/C8Dialog.vue'
import { toast } from 'vue-sonner'
import C8Item from '~/components/C8Item.vue'
import { ItemDescription } from '~/components/ui/item'
import { DropdownMenuItem, DropdownMenuSeparator } from '@/components/ui/dropdown-menu'
import { Badge } from '@/components/ui/badge'
import { File, FileText, FolderGit2, LetterText, Trash, Globe, Eye } from 'lucide-vue-next'
import { KB_UPDATE, STATUS_LABELS } from '~/lib/consts'
import type { StatusType } from '~/lib/consts'

const kbStore = useKnowledgeBaseStore()
const liveUpdateStore = useLiveUpdateStore()

const isLoading = ref(false)
const isDeleteDialogOpen = ref(false)
const isDetailsDialogOpen = ref(false)
const kbToDelete = ref<KnowledgeBaseItem | null>(null)
const selectedKB = ref<KnowledgeBaseItem | null>(null)

const kbs = computed(() => kbStore.kbs)

function getKBIcon(sourceType: string) {
  switch (sourceType) {
    case 'file':
      return File
    case 'text':
      return LetterText
    case 'url':
      return Globe
    case 'github':
      return FolderGit2
    case 'version_control':
      return FolderGit2
    default:
      return File
  }
}

function getSourceTypeIcon(sourceType: string) {
  switch (sourceType) {
    case 'file':
      return File
    case 'text':
      return LetterText
    case 'url':
      return Globe
    case 'github':
      return FolderGit2
    case 'version_control':
      return FolderGit2
    default:
      return File
  }
}

function getSourceTypeLabel(sourceType: string) {
  switch (sourceType) {
    case 'file':
      return 'File'
    case 'text':
      return 'Text'
    case 'url':
      return 'URL'
    case 'github':
      return 'Version Control'
    case 'version_control':
      return 'Version Control'
    default:
      return sourceType
  }
}

function getKBTitle(kb: KnowledgeBaseItem) {
  if ((kb.source_type === 'github' || kb.source_type === 'version_control') && kb.path) {
    return kb.path
  }
  if (kb.source_type === 'url') {
    return kb.metadata?.title || kb.path
  }
  if (kb.metadata?.file_name) {
    return kb.metadata.file_name
  }
  if (kb.path) {
    return stripTextProtocol(kb.path).split('/').pop() || stripTextProtocol(kb.path)
  }
  return 'Untitled'
}

function stripTextProtocol(path: string): string {
  return path.replace(/^text:\/\//, '')
}

function getStatusVariant(status: string) {
  switch (status) {
    case 'completed':
    case 'processed':
      return 'default'
    case 'failed':
      return 'destructive'
    case 'duplicate':
      return 'destructive_text'
    case 'pending':
    case 'uploading':
    case 'extracting':
    case 'processing':
    case 'reprocessing':
      return 'secondary'
    default:
      return 'secondary'
  }
}

const unsubscribe = liveUpdateStore.subscribe((msg) => {
  if (msg.type === KB_UPDATE) {
    const { uuid, status, ingestion_status } = msg.data

    if (uuid && status) {
      kbStore.updateStatus(uuid, status)
    } else if (ingestion_status === 'failed') {
      kbStore.load()
    }
  }
})

onMounted(() => {
  isLoading.value = true
  kbStore.load().finally(() => {
    isLoading.value = false
  })
})

onBeforeUnmount(() => {
  unsubscribe()
})

function openDeleteDialog(kb: KnowledgeBaseItem) {
  kbToDelete.value = kb
  isDeleteDialogOpen.value = true
}

function confirmDelete() {
  if (kbToDelete.value) {
    deleteKB(kbToDelete.value)
  }
}

function deleteKB(kb: KnowledgeBaseItem) {
  kbStore.delete(kb.uuid).then(() => {
    toast.success('Knowledge base item deleted')
  }).catch(() => {
    toast.error('Failed to delete knowledge base item')
  })
}

function openDetailsDialog(kb: KnowledgeBaseItem) {
  selectedKB.value = kb
  isDetailsDialogOpen.value = true
}

function formatDate(dateString: string | null) {
  if (!dateString) return 'N/A'
  
  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) {
      return 'Invalid date'
    }
    return date.toLocaleString()
  } catch {
    return 'Invalid date'
  }
}
</script>
