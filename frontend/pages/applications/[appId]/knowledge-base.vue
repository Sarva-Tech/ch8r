<script setup lang="ts">
import {
  createColumnHelper,
  getCoreRowModel,
  useVueTable,
} from '@tanstack/vue-table'
import { ref, computed, onMounted } from 'vue'
import NewKnowledgeBase from '~/components/KnowledgeBase/NewKnowledgeBase.vue'
import UpdateKnowledgeBase from '~/components/KnowledgeBase/UpdateKnowledgeBase.vue'
import { KB_UPDATE  } from '~/lib/consts'
import type { KBTableRow } from '~/lib/types'

const updateKBRef = ref<InstanceType<typeof UpdateKnowledgeBase> | null>(null)

const liveUpdateStore = useLiveUpdateStore()
const kbStore = useKnowledgeBaseStore()

const kbs = computed(() => kbStore.kbs)
const isLoading = ref(false)

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

function deleteRow(uuid: string) {
  kbStore.delete(uuid)
}
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
      <C8Table
        v-else
        :data="data"
        :columns="columns"
        :update-fn="openUpdateKB"
        :delete-fn="deleteRow"
        :expandable="true"
      />
    </div>
    <UpdateKnowledgeBase ref="updateKBRef" />
  </div>
</template>

<style>
tr[data-expanded='true'] {
  display: table-row !important;
}
</style>
