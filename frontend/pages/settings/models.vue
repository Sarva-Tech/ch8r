<template>
  <div class="flex flex-col h-screen p-4 pt-[72px] pb-[120px] overflow-y-auto">
    <div class="w-full space-y-4">
      <div class="flex gap-2 items-center py-4">
        <div class="ml-auto">
          <NewModel />
        </div>
      </div>

      <C8Table
        :data="models"
        :columns="columns"
        :expandable="false"
        :delete-fn="deleteModel"
        :update-fn="deleteModel"
      />
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import type { ColumnDef } from '@tanstack/vue-table'
import NewModel from '~/components/Model/NewModel.vue'
import { toast } from 'vue-sonner'

const modelStore = useModelStore()
const user = useUserStore()

const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    await modelStore.load()
  } catch (e: unknown) {
    toast.error('Failed to load models')
  } finally {
    loading.value = false
  }
})

// TODO: Disable model deletion and update for now
// canDelete: !model.is_default && model.owner === user.authUser.id,

const models = computed(() =>
  modelStore.models.map((model) => ({
    ...model,
    canDelete: false,
    canUpdate: false
  }))
)

const columns: ColumnDef<never>[] = [
  {
    accessorKey: 'name',
    header: 'Name',
    cell: (info) => info.getValue(),
  },
  {
    accessorKey: 'base_url',
    header: 'Base URL',
    cell: (info) => info.getValue(),
  },
  {
    accessorKey: 'model_name',
    header: 'Model',
    cell: (info) => info.getValue(),
  },
  {
    id: 'actions',
    header: 'Actions',
    cell: () => '',
  },
]

function deleteModel() {}
function updateModel() {}
</script>
