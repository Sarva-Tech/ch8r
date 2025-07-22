<script setup lang="ts">
import {
  createColumnHelper,
  getCoreRowModel,
  useVueTable,
} from '@tanstack/vue-table'
import { ref, computed, onMounted } from 'vue'
import { $fetch } from 'ofetch'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import AppSheet from '~/components/BaseSheet.vue'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  FileText,
  File,
  Image,
  Trash,
  Pencil,
  MoreVertical,
  ChevronDown,
  ChevronRight,
} from 'lucide-vue-next'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { toast } from 'vue-sonner'
import NewKnowledgeBase from '~/components/KnowledgeBase/NewKnowledgeBase.vue'

interface FileData {
  id: string
  fileType: string
  content: string
  fileName: string
  metaDataContent?: string
  owner: { username: string; email: string }
  applicationName: string
}

const userStore = useUserStore()
const appStore = useApplicationsStore()

const selectedApp = computed(() => appStore.selectedApplication)
const appDetails = ref<any>({})
const isLoading = ref(false)
const manualExpanded = ref<Record<string, boolean>>({})

const isEditSheetOpen = ref(false)
const editingRow = ref<FileData | null>(null)

async function loadKB() {
  try {
    isLoading.value = true
    const token = userStore.getToken
    if (!token.value || !selectedApp.value?.uuid) {
      throw new Error('Missing token or application UUID')
    }
    appDetails.value = await $fetch(
      `http://localhost:8000/api/applications/${selectedApp.value.uuid}/knowledge-bases/`,
      {
        method: 'GET',
        headers: {
          Authorization: `Token ${token.value}`,
          'Content-Type': 'application/json',
        },
      }
    ).then(res => res.application || {})
  } catch (err: any) {
    console.error('Fetch error:', err)
    toast.error(`Failed to load knowledge base: ${err?.message || 'Unknown error'}`)
  } finally {
    isLoading.value = false
  }
}

onMounted(loadKB)

const data = computed<FileData[]>(() => {
  return (appDetails.value.knowledge_base || []).map((item: any) => {
    const rawContent = item.metadata?.content || item.path.split('/').pop() || item.path
    const isText = item.source_type.toLowerCase() === 'text'
    const trimmedContent =
      isText && typeof rawContent === 'string' && rawContent.length > 40
        ? `${rawContent.slice(0, 20)}...${rawContent.slice(-20)}`
        : rawContent

    return {
      id: item.uuid,
      fileType: isText
        ? 'text'
        : item.source_type.toLowerCase() === 'image'
          ? 'image'
          : item.path.endsWith('.pdf')
            ? 'pdf'
            : item.path.match(/\.(doc|docx)$/i)
              ? 'doc'
              : item.path.match(/\.(jpg|jpeg|png|gif)$/i)
                ? 'image'
                : 'file',
      fileName: item.path.split('/').pop() || '',
      content: trimmedContent,
      metaDataContent: item.metadata?.content,
      owner: {
        username: appDetails.value.owner?.username || 'N/A',
        email: appDetails.value.owner?.email || 'N/A',
      },
      applicationName: appDetails.value.name || 'N/A',
    }
  })
})

const columnHelper = createColumnHelper<FileData>()
const columns = [
  columnHelper.display({ id: 'expander', header: '' }),
  columnHelper.accessor('content', { header: 'Content' }),
  columnHelper.display({ id: 'actions', header: 'Actions' }),
]

const table = useVueTable({
  get data() {
    return data.value
  },
  columns,
  getCoreRowModel: getCoreRowModel(),
})

async function handleDelete(id: string) {
  try {
    const token = userStore.getToken
    if (!token.value || !selectedApp.value?.uuid) {
      throw new Error('Missing token or application UUID')
    }
    await $fetch(
      `http://localhost:8000/api/applications/${selectedApp.value.uuid}/knowledge-bases/${id}/`,
      {
        method: 'DELETE',
        headers: { Authorization: `Token ${token.value}` },
      }
    )
    toast.success('Knowledge base deleted successfully.')
    await loadKB()
  } catch (err: any) {
    console.error('Delete error:', err)
    toast.error(`Failed to delete knowledge base: ${err?.message || 'Unknown error'}`)
  }
}

function openEditSheet(row: FileData) {
  editingRow.value = { ...row }
  isEditSheetOpen.value = true
}

function closeEditSheet() {
  isEditSheetOpen.value = false
  editingRow.value = null
}

async function handleUpdate() {
  if (!editingRow.value || !selectedApp.value?.uuid) return
  try {
    isLoading.value = true
    const token = userStore.getToken
    await $fetch(
      `http://localhost:8000/api/applications/${selectedApp.value.uuid}/knowledge-bases/${editingRow.value.id}/`,
      {
        method: 'PUT',
        headers: {
          Authorization: `Token ${token.value}`,
          'Content-Type': 'application/json',
        },
        body: {
          metadata: { content: editingRow.value.metaDataContent },
          path: editingRow.value.fileName,
        },
      }
    )
    toast.success('Knowledge base updated successfully.')
    closeEditSheet()
    await loadKB()
  } catch (err: any) {
    console.error('Update error:', err)
    toast.error(`Failed to update: ${err?.message || 'Unknown error'}`)
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="flex flex-col h-screen p-4 pt-[72px] pb-[120px] overflow-y-auto">
    <div class="w-full space-y-4">
      <div class="flex gap-2 items-center py-4">
        <Input class="max-w-sm" placeholder="Filter content..." />
        <div class="ml-auto">
          <NewKnowledgeBase @knowledge-added="loadKB"/>
        </div>
      </div>

      <div v-if="isLoading" class="text-center py-8">Loading...</div>
      <div v-else-if="!table.getRowModel().rows?.length" class="text-center py-8">
        No results.
      </div>
      <Table v-else class="rounded-md border">
        <TableHeader>
          <TableRow v-for="headerGroup in table.getHeaderGroups()" :key="headerGroup.id">
            <TableHead
              v-for="header in headerGroup.headers"
              :key="header.id"
              class="font-bold"
              :class="{
                'w-[50px]': header.id === 'expander',
                'w-[100px] text-right': header.id === 'actions',
              }"
            >
              {{ header.column.columnDef.header }}
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <template v-for="row in table.getRowModel().rows" :key="row.id">
            <TableRow>
              <TableCell
                v-for="cell in row.getVisibleCells()"
                :key="cell.id"
                :class="{ 'text-right': cell.column.id === 'actions' }"
              >
                <div
                  v-if="cell.column.id === 'expander'"
                  class="p-1 rounded focus:outline-none"
                  :aria-label="manualExpanded[row.id] ? 'Collapse row' : 'Expand row'"
                  @click.stop.prevent="manualExpanded[row.id] = !manualExpanded[row.id]"
                >
                  <ChevronDown v-if="manualExpanded[row.id]" class="w-4 h-4" />
                  <ChevronRight v-else class="w-4 h-4" />
                </div>
                <div v-else-if="cell.column.id === 'content'" class="flex items-center">
                  <FileText v-if="row.original.fileType === 'text'" class="mr-2 w-4 h-4" />
                  <Image v-else-if="row.original.fileType === 'image'" class="mr-2 w-4 h-4" />
                  <File v-else class="mr-2 w-4 h-4" />
                  <span class="truncate max-w-[300px]">{{ row.original.content }}</span>
                </div>
                <DropdownMenu v-else-if="cell.column.id === 'actions'">
                  <DropdownMenuTrigger as-child>
                    <Button variant="ghost" size="sm" class="h-8 w-8 p-0">
                      <MoreVertical class="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem @click="openEditSheet(row.original)">
                      <Pencil class="mr-2 h-4 w-4" /> Edit
                    </DropdownMenuItem>
                    <DropdownMenuItem class="text-red-600" @click="handleDelete(row.original.id)">
                      <Trash class="mr-2 h-4 w-4" /> Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
            <TableRow v-if="manualExpanded[row.id]" data-expanded="true">
              <TableCell :colspan="columns.length">
                <div class="bg-muted rounded-xl shadow-inner border p-2 space-y-4">
                  <div class="flex gap-6">
                    <div class="text-muted-foreground font-medium w-32">Owner</div>
                    <div>{{ row.original.owner.username }} ({{ row.original.owner.email }})</div>
                  </div>
                  <div class="flex gap-6">
                    <div class="text-muted-foreground font-medium w-32">File Type</div>
                    <div class="capitalize">{{ row.original.fileType }}</div>
                  </div>
                  <div>
                    <div class="text-muted-foreground font-medium mb-1">Full Content</div>
                    <div class="whitespace-pre-wrap break-words max-h-64 overflow-y-auto p-2 rounded border text-sm leading-relaxed">
                      {{ row.original?.metaDataContent || 'No content available' }}
                    </div>
                  </div>
                </div>
              </TableCell>
            </TableRow>
          </template>
        </TableBody>
      </Table>
      <AppSheet
        v-if="editingRow"
        v-model:open="isEditSheetOpen"
        title="Edit Knowledge Base"
        submit-text="Save"
        cancel-text="Cancel"
        :on-submit="handleUpdate"
        :loading="isLoading"
      >
        <div class="flex flex-col h-full max-h-[calc(100vh-150px)] overflow-auto">
          <Label for="content" class="text-sm font-medium mb-2">Content</Label>
          <textarea
            id="content"
            v-model="editingRow.metaDataContent"
            class="min-h-[400px] resize-none w-full rounded-lg border border-gray-300 focus:border-primary focus:ring-2 focus:ring-primary/20 shadow-sm text-sm px-3 py-2 flex-1"
          />
        </div>
      </AppSheet>
    </div>
  </div>
</template>

<style>
tr[data-expanded='true'] {
  display: table-row !important;
}
</style>
