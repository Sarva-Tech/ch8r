<template>
  <div class="flex flex-col h-screen p-4 pt-[72px] pb-[120px] overflow-y-auto">
    <div class="w-full space-y-2">
      <div class="flex gap-2 items-center py-4">
        <div class="ml-auto">
          <NewKnowledgeBase />
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import NewKnowledgeBase from '~/components/KnowledgeBase/NewKnowledgeBase.vue'
import C8Dialog from '~/components/C8Dialog.vue'
import { toast } from 'vue-sonner'
import C8Item from '~/components/C8Item.vue'
import { ItemDescription } from '~/components/ui/item'
import { DropdownMenuItem } from '@/components/ui/dropdown-menu'
import { Badge } from '@/components/ui/badge'
import { File, FileText, FolderGit2, LetterText, Trash } from 'lucide-vue-next'
import { KB_UPDATE, STATUS_LABELS } from '~/lib/consts'
import type { StatusType } from '~/lib/consts'

const kbStore = useKnowledgeBaseStore()
const liveUpdateStore = useLiveUpdateStore()

const isLoading = ref(false)
const isDeleteDialogOpen = ref(false)
const kbToDelete = ref<KnowledgeBaseItem | null>(null)

const kbs = computed(() => kbStore.kbs)

function getKBIcon(sourceType: string) {
  switch (sourceType) {
    case 'file':
      return File
    case 'text':
      return LetterText
    case 'github':
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
    case 'github':
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
    case 'github':
      return 'Version Control'
    default:
      return sourceType
  }
}

function getKBTitle(kb: KnowledgeBaseItem) {
  if (kb.source_type === 'github' && kb.path) {
    return kb.path
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
</script>
