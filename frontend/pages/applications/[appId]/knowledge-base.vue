<script setup lang="ts">
import type { ColumnDef } from '@tanstack/vue-table';
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

const data = computed(() => {
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

const columns: ColumnDef<unknown, string | number>[] = [
  {
    id: 'expander',
    header: '',
    cell: () => '',
  },
  {
    accessorKey: 'path',
    header: 'File',
    cell: (info) => info.getValue(),
  },
  {
    accessorKey: 'status',
    header: 'Status',
    cell: (info) => info.getValue(),
  },
  {
    id: 'actions',
    header: 'Actions',
    cell: () => '',
  },
]

const unsubscribe = liveUpdateStore.subscribe((msg) => {
  if (msg.type === KB_UPDATE) {
    const { uuid, status } = msg.data
    kbStore.updateStatus(uuid, status)
  }
})

function openUpdateKB(kb: KBTableRow) {
  updateKBRef.value?.openSlide(kb)
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
        v-if="data.length === 0"
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
