<script setup lang="ts">
import {
  createColumnHelper,
  getCoreRowModel,
  useVueTable,
} from '@tanstack/vue-table'
import { ref, computed, onMounted } from 'vue'
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
import { useHttpClient } from '~/composables/useHttpClient'
import { DEFAULT_KB_SOURCE, KB_SOURCES, KB_UPDATE, type StatusType } from '~/lib/consts'
import { getStatusLabel } from '~/lib/utils'

const sources = KB_SOURCES

type TableRow = {
  uuid: string
  sourceType: string
  path: string
  content?: string
  status: StatusType
}

const liveUpdateStore = useLiveUpdateStore()
const appStore = useApplicationsStore()
const { httpDelete, httpPut } = useHttpClient()
const kbStore = useKnowledgeBaseStore()

const selectedApp = computed(() => appStore.selectedApplication)
const kbs = computed(() => kbStore.kbs)
const isLoading = ref(false)
const manualExpanded = ref<Record<string, boolean>>({})

const isEditSheetOpen = ref(false)
const editingRow = ref<KnowledgeBaseItem | null>(null)

const selectedSource = (value: string) => {
  const source = sources.find(source => source.value === value)
  return source?.icon || DEFAULT_KB_SOURCE.icon
}

const data = computed<TableRow[]>(() => {
  return (kbs.value || []).map((item: KnowledgeBaseItem) => {
    return {
      uuid: item.uuid,
      sourceType: item.source_type,
      path: item.path,
      content: item.metadata?.content ?? '',
      status: item.status,
    }
  })
})

const columnHelper = createColumnHelper<TableRow>()
const columns = [
  columnHelper.display({ id: 'expander', header: '' }),
  columnHelper.accessor('path', { header: 'File' }),
  columnHelper.accessor('status', { header: 'Status' }),
  columnHelper.display({ id: 'actions', header: 'Actions' }),
]

const table = useVueTable<TableRow>({
  get data() {
    return data.value
  },
  columns,
  getCoreRowModel: getCoreRowModel(),
})

async function handleDelete(id: string) {
  if (!selectedApp.value) return
  try {
    await httpDelete(
      `/applications/${selectedApp.value.uuid}/knowledge-bases/${id}/`,
    )
    toast.success('Knowledge base deleted successfully.')

    await loadKB()
  } catch (err: unknown) {
    console.error('Delete error:', err)
    toast.error(
      `Failed to delete knowledge base: ${err?.message || 'Unknown error'}`,
    )
  }
}
function openEditSheet(row: KnowledgeBaseItem) {
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

    await httpPut(
      `/applications/${selectedApp.value.uuid}/knowledge-bases/${editingRow.value.id}/`,
      {
        metadata: { content: editingRow.value.metaDataContent },
        path: editingRow.value.path,
      },
    )

    toast.success('Knowledge base updated successfully.')
    closeEditSheet()
    await loadKB()
  } catch (err: unknown) {
    console.error('Update error:', err)
    toast.error(`Failed to update: ${err?.message || 'Unknown error'}`)
  } finally {
    isLoading.value = false
  }
}

const unsubscribe = liveUpdateStore.subscribe((msg) => {
  if (msg.type === KB_UPDATE) {
    const { uuid, status, content } = msg.data
    kbStore.updateStatus(uuid, status, content)
  }
})

onMounted(() => { kbStore.load() })
onBeforeUnmount(() => {
  unsubscribe()
})
</script>

<template>
  <div class="flex flex-col h-screen p-4 pt-[72px] pb-[120px] overflow-y-auto">
    <div class="w-full space-y-4">
      <div class="flex gap-2 items-center py-4">
        <Input class="max-w-sm" placeholder="Filter content..." />
        <div class="ml-auto">
          <NewKnowledgeBase />
        </div>
      </div>

      <div v-if="isLoading" class="text-center py-8">Loading...</div>
      <div
        v-else-if="!table.getRowModel().rows?.length"
        class="text-center py-8"
      >
        No results.
      </div>
      <Table v-else class="rounded-md border">
        <TableHeader>
          <TableRow
            v-for="headerGroup in table.getHeaderGroups()"
            :key="headerGroup.id"
          >
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
                  :aria-label="
                    manualExpanded[row.id] ? 'Collapse row' : 'Expand row'
                  "
                  @click.stop.prevent="
                    manualExpanded[row.id] = !manualExpanded[row.id]
                  "
                >
                  <ChevronDown v-if="manualExpanded[row.id]" class="w-4 h-4" />
                  <ChevronRight v-else class="w-4 h-4" />
                </div>
                <div
                  v-else-if="cell.column.id === 'path'"
                  class="flex items-center space-x-2"
                >
                  <component
                    :is="selectedSource(row.original.sourceType)"
                    class="w-4 h-4"
                  />
                  <span class="truncate max-w-[300px]">{{
                    row.original.path
                  }}</span>
                </div>
                <div
                  v-else-if="cell.column.id === 'status'"
                  class="flex items-center"
                >
                  {{ getStatusLabel(row.original.status) }}
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
                    <DropdownMenuItem
                      class="text-red-600"
                      @click="handleDelete(row.original.id)"
                    >
                      <Trash class="mr-2 h-4 w-4" /> Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
            <TableRow v-if="manualExpanded[row.id]" data-expanded="true">
              <TableCell :colspan="columns.length">
                <div class="bg-muted shadow-inner border p-2 space-y-4">
                  <div>
                    <div
                      class="whitespace-pre-wrap break-words max-h-64 overflow-y-auto p-2 text-sm leading-relaxed"
                    >
                      {{
                        row.original?.content || 'No content available'
                      }}
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
        <div
          class="flex flex-col h-full max-h-[calc(100vh-150px)] overflow-auto"
        >
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
