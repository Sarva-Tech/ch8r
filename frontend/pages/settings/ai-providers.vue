<template>
  <div class="flex flex-col h-screen p-4 pt-[72px] pb-[120px] overflow-y-auto">
    <div class="w-full space-y-4">
      <div class="flex gap-2 items-center py-4">
        <div class="ml-auto">
          <NewAIProvider />
        </div>
      </div>

      <C8Table
        :data="models"
        :columns="columns"
        :expandable="false"
        :delete-fn="deleteModel"
        :update-fn="updateModel"
      />

      <UpdateAIProvider ref="updateModelSlide" />
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ColumnDef } from '@tanstack/vue-table'
import NewAIProvider from '~/components/AIProvider/NewAIProvider.vue'
import UpdateAIProvider from '~/components/AIProvider/UpdateAIProvider.vue'
import { toast } from 'vue-sonner'

const updateModelSlide = ref<InstanceType<typeof UpdateAIProvider> | null>(null)

const AIProviderStore = useAIProviderStore()
const user = useUserStore()

const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    await AIProviderStore.load()
  } catch (e: unknown) {
    console.error(e)
    toast.error('Failed to load models')
  } finally {
    loading.value = false
  }
})

const models = computed(() =>
    AIProviderStore.AIProviders.map((model) => ({
    ...model,
    canDelete: model.owner === user.authUser.id,
    canUpdate: model.owner === user.authUser.id,
  }))
)

const columns: ColumnDef<unknown, string | number>[] = [
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

function updateModel(AIProvider: AIProvider) {
  updateModelSlide.value?.open(AIProvider)
}

function deleteModel(uuid: string) {
  AIProviderStore.delete(uuid)
}
</script>
