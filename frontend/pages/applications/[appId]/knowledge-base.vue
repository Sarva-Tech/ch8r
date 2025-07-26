<script setup lang="ts">
import {
  createColumnHelper,
  getCoreRowModel,
  useVueTable,
} from '@tanstack/vue-table'
import { ref, computed, onMounted } from 'vue'
import { Button } from '@/components/ui/button'
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
  MoreVertical,
  ChevronDown,
  ChevronRight, Pencil
} from 'lucide-vue-next'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import NewKnowledgeBase from '~/components/KnowledgeBase/NewKnowledgeBase.vue'
import UpdateKnowledgeBase from '~/components/KnowledgeBase/UpdateKnowledgeBase.vue'
import { DEFAULT_KB_SOURCE, KB_SOURCES, KB_UPDATE  } from '~/lib/consts'
import { getStatusLabel } from '~/lib/utils'
import type { KBTableRow } from '~/lib/types'

const updateKBRef = ref<InstanceType<typeof UpdateKnowledgeBase> | null>(null)

const sources = KB_SOURCES

const liveUpdateStore = useLiveUpdateStore()
const kbStore = useKnowledgeBaseStore()

const kbs = computed(() => kbStore.kbs)
const isLoading = ref(false)
const manualExpanded = ref<Record<string, boolean>>({})

const selectedSource = (value: string) => {
  const source = sources.find(source => source.value === value)
  return source?.icon || DEFAULT_KB_SOURCE.icon
}

const data = computed<KBTableRow[]>(() => {
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

const columnHelper = createColumnHelper<KBTableRow>()
const columns = [
  columnHelper.display({ id: 'expander', header: '' }),
  columnHelper.accessor('path', { header: 'File' }),
  columnHelper.accessor('status', { header: 'Status' }),
  columnHelper.display({ id: 'actions', header: 'Actions' }),
]

const table = useVueTable<KBTableRow>({
  get data() {
    return data.value
  },
  columns,
  getCoreRowModel: getCoreRowModel(),
})

const unsubscribe = liveUpdateStore.subscribe((msg) => {
  if (msg.type === KB_UPDATE) {
    const { uuid, status } = msg.data
    kbStore.updateStatus(uuid, status)
  }
})

function openUpdateKB(kb: KBTableRow) {
  updateKBRef.value?.openSheet(kb)
}

onMounted(() => { kbStore.load() })
onBeforeUnmount(() => {
  unsubscribe()
})
</script>

<template>
  <div class="flex flex-col h-screen p-4 pt-[72px] pb-[120px] overflow-y-auto">
    <div class="w-full space-y-4">
      <div class="flex gap-2 items-center py-4">
        <div class="ml-auto">
          <NewKnowledgeBase />
        </div>
      </div>

      <div v-if="isLoading" class="text-center py-8">Loading...</div>
      <div
        v-else-if="!table.getRowModel().rows?.length"
        class="text-center py-8"
      >
        Your knowledge base is empty.
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
                    <DropdownMenuItem @click="openUpdateKB(row.original)">
                      <Pencil class="mr-2 h-4 w-4" /> Update
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      class="text-red-600"
                      @click="kbStore.delete(row.original.uuid)"
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
    </div>
    <UpdateKnowledgeBase ref="updateKBRef" />
  </div>
</template>

<style>
tr[data-expanded='true'] {
  display: table-row !important;
}
</style>
