<script setup lang="ts">
import {
  createColumnHelper,
  getCoreRowModel,
  useVueTable,
} from '@tanstack/vue-table'
import { computed, onMounted, ref } from 'vue'
import type { APIKeyTableRow } from '~/lib/types'
import NewApiKey from '~/components/ApiKey/NewApiKey.vue'
import type { APIKeyItem } from '~/stores/apiKey'

const apiKeyStore = useAPIKeyStore()

const apiKeys = computed(() => apiKeyStore.apiKeys)

const data = computed<APIKeyTableRow[]>(() => {
  return (apiKeys.value || []).map((item: APIKeyItem) => {
    return {
      id: item.id,
      created: item.created,
      name: item.name,
      permissions: item.permissions?.map(p => p.toUpperCase()).join(", "),
    }
  })
})

const columnHelper = createColumnHelper<APIKeyTableRow>()
const columns = [
  columnHelper.display({ id: 'expander', header: '' }),
  columnHelper.accessor('name', { header: 'Name' }),
  columnHelper.accessor('permissions', { header: 'Permissions' }),
  columnHelper.display({ id: 'actions', header: 'Actions' }),
]

function deleteRow(id: number) {
  apiKeyStore.delete(id)
}

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
          <NewApiKey />
        </div>
      </div>

      <div v-if="apiKeyStore.loading" class="text-center py-8">Loading...</div>
      <div
        v-else-if="!table.getRowModel().rows?.length"
        class="text-center py-8"
      >
        Your API keys are empty.
      </div>
      <Ch8rTable
        v-else
        :data="data"
        :columns="columns"
        :delete-fn="deleteRow"
        :expandable="false"
      />
    </div>
  </div>
</template>
