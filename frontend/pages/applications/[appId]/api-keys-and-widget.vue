<script setup lang="ts">
import {createColumnHelper, getCoreRowModel, useVueTable,} from '@tanstack/vue-table'
import {computed, onMounted, ref} from 'vue'
import {Button} from '@/components/ui/button'
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow,} from '@/components/ui/table'
import {MoreVertical, Trash} from 'lucide-vue-next'
import {DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,} from '@/components/ui/dropdown-menu'
import type {APIKeyTableRow} from '~/lib/types'
import NewApiKey from "~/components/ApiKey/NewApiKey.vue";
import type {APIKeyItem} from "~/stores/apiKey";

const apiKeyStore = useAPIKeyStore()

const apiKeys = computed(() => apiKeyStore.apiKeys)
const isLoading = ref(false)

const data = computed<APIKeyTableRow[]>(() => {
  return (apiKeys.value || []).map((item: APIKeyItem) => {
    return {
      created: item.created,
      name: item.name,
      delete: item.permissions?.includes('delete'),
      read: item.permissions?.includes('read'),
      write: item.permissions?.includes('write')
    }
  })
})

const columnHelper = createColumnHelper<APIKeyTableRow>()
const columns = [
  columnHelper.display({id: 'expander', header: ''}),
  columnHelper.accessor('name', {header: 'Name'}),
  columnHelper.accessor('read', {header: 'Read'}),
  columnHelper.accessor('write', {header: 'Write'}),
  columnHelper.accessor('delete', {header: 'Delete'}),
  columnHelper.display({id: 'actions', header: 'Actions'}),
]

const table = useVueTable<APIKeyTableRow>({
  get data() {
    return data.value
  },
  columns,
  getCoreRowModel: getCoreRowModel(),
})

onMounted(() => {
  apiKeyStore.load()
})
</script>

<template>
  <div class="flex flex-col h-screen p-4 pt-[72px] pb-[120px] overflow-y-auto">
    <div class="w-full space-y-4">
      <div class="flex gap-2 items-center py-4">
        <div class="ml-auto">
          <NewApiKey/>
        </div>
      </div>

      <div v-if="isLoading" class="text-center py-8">Loading...</div>
      <div
          v-else-if="!table.getRowModel().rows?.length"
          class="text-center py-8"
      >
        Your API keys are empty.
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
                    v-if="cell.column.id === 'name'"
                    class="flex items-center space-x-2"
                >
                  <!--                  <component-->
                  <!--                      :is="selectedSource(row.original.sourceType)"-->
                  <!--                      class="w-4 h-4"-->
                  <!--                  />-->
                  <span class="truncate max-w-[300px]">{{
                      row.original.name
                    }}</span>
                </div>
                <div
                    v-else-if="cell.column.id === 'write'"
                    class="flex items-center"
                >
                  {{ row.original.write ? 'Allowed' : 'Denied' }}
                </div>
                <div
                    v-else-if="cell.column.id === 'delete'"
                    class="flex items-center"
                >
                  {{ row.original.delete ? 'Allowed' : 'Denied' }}
                </div>
                <div
                    v-else-if="cell.column.id === 'read'"
                    class="flex items-center"
                >
                  {{ row.original.read ? 'Allowed' : 'Denied' }}
                </div>

                <DropdownMenu v-else-if="cell.column.id === 'actions'">
                  <DropdownMenuTrigger as-child>
                    <Button variant="ghost" size="sm" class="h-8 w-8 p-0">
                      <MoreVertical class="h-4 w-4"/>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem
                        class="text-red-600"
                        @click="apiKeyStore.delete(row.original.uuid)"
                    >
                      <Trash class="mr-2 h-4 w-4"/>
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          </template>
        </TableBody>
      </Table>
    </div>
  </div>
</template>

<style>
tr[data-expanded='true'] {
  display: table-row !important;
}
</style>
