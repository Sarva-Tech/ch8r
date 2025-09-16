<template>
  <TooltipProvider>
    <Table class="rounded-md border">
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
                @click.stop.prevent="toggleRowExpansion(row.id)"
              >
                <div v-if="expandable">
                <ChevronDown v-if="manualExpanded[row.id]" class="w-4 h-4" />
                <ChevronRight v-else class="w-4 h-4" />
                </div>
              </div>
              <div v-else>
                <template v-if="cell.column.id !== 'expander'">
                  <div v-if="cell.column.id === 'actions'">
                    <DropdownMenu>
                      <DropdownMenuTrigger as-child>
                        <Button variant="ghost" size="sm" class="h-8 w-8 p-0">
                          <MoreVertical class="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          v-if="updateFn"
                          :disabled="!row.original?.canUpdate"
                          @click="updateFn(row.original)"
                        >
                          <Pencil class="mr-2 h-4 w-4" /> Update
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          v-if="deleteFn"
                          class="text-red-600"
                          :disabled="!row.original?.canDelete"
                          @click="deleteFn(row.original?.uuid || row.original?.id)"
                        >
                          <Trash class="mr-2 h-4 w-4" /> Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                  <span v-else class="flex">
                    <component :is="cell.getValue()?.icon" v-if="cell.getValue()?.icon" class="w-4 h-4 mr-1" />
                    <Tooltip v-if="truncatedMap[`${row.id}-${cell.column.id}`]">
                      <TooltipTrigger as-child>
                        <span
                          class="truncate block w-40 cursor-help truncatable"
                          :data-key="`${row.id}`"
                        >
                          {{ cell.getValue()?.value || cell.getValue() }}
                        </span>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>{{ cell.getValue()?.value || cell.getValue() }}</p>
                      </TooltipContent>
                    </Tooltip>
                    <span
                      v-else
                      class="truncate block w-40 truncatable"
                      :data-key="`${row.id}-${cell.column.id}`"
                    >
                      {{ cell.getValue() }}
                    </span>
                  </span>
                </template>
              </div>
            </TableCell>
          </TableRow>
          <TableRow v-if="manualExpanded[row.id]" data-expanded="true">
            <TableCell :colspan="columns.length">
              <div class="bg-muted shadow-inner border p-2 space-y-4">
                <div>
                  <div class="whitespace-pre-wrap break-words max-h-64 overflow-y-auto p-2 text-sm leading-relaxed">
                    {{ row.original?.content || 'No content' }}
                  </div>
                </div>
              </div>
            </TableCell>
          </TableRow>
        </template>
      </TableBody>
    </Table>
  </TooltipProvider>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useVueTable, getCoreRowModel } from '@tanstack/vue-table'
import type { ColumnDef } from '@tanstack/vue-table'
import { Button } from '~/components/ui/button'
import { ChevronDown, ChevronRight, MoreVertical, Pencil, Trash } from 'lucide-vue-next'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '~/components/ui/dropdown-menu'

const props = defineProps({
  data: {
    type: Array as PropType<unknown[]>,
    required: true
  },
  columns: {
    type: Array as PropType<ColumnDef<unknown, string | number>[]>,
    required: true
  },
  updateFn: {
    type: Function as PropType<(param: never) => void>,
    required: false,
    default: () => {}
  },
  deleteFn: {
    type: Function as PropType<(identifier: never) => void>,
    required: false,
    default: () => {}
  },
  expandable: {
    type: Boolean as PropType<boolean>,
    default: false
  }
})

const truncatedMap = ref<Record<string, boolean>>({})

const manualExpanded = ref<Record<string, boolean>>({})
const table = useVueTable<unknown>({
  get data() {
    return props.data
  },
  columns: props.columns,
  getCoreRowModel: getCoreRowModel(),
})

function toggleRowExpansion(rowId: string) {
  manualExpanded.value[rowId] = !manualExpanded.value[rowId]
}

function checkTruncation() {
  document.querySelectorAll('.truncatable').forEach((el) => {
    const key = el.getAttribute("data-key")
    if (key) {
      truncatedMap.value[key] = el.scrollWidth > el.clientWidth
    }
  })
}

onMounted(() => {
  nextTick(() => checkTruncation())
})

watch(
  () => props.data,
  () => {
    nextTick(() => checkTruncation())
  },
  { deep: true }
)
</script>

<style scoped>
tr[data-expanded='true'] {
  display: table-row !important;
}
</style>
