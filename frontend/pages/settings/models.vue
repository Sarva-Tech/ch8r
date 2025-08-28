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
      />
    </div>
    <UpdateNotificationProfiles ref="updateNotification" />
  </div>
</template>
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import UpdateNotificationProfiles from '~/components/notification/UpdateNotificationProfile.vue'
import type { ColumnDef } from '@tanstack/vue-table'
import NewModel from '~/components/Model/NewModel.vue'
import { toast } from 'vue-sonner'

const modelStore = useModelStore()
const loading = ref(false)

const models = computed(() => modelStore.models)

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
</script>
