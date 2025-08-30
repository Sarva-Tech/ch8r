<template>
  <div class="flex flex-col h-screen p-4 pt-[72px] pb-[120px] overflow-y-auto">
    <div class="w-full space-y-4">
      <div class="flex gap-2 items-center py-4">
        <div class="ml-auto">
          <NewIntegration />
        </div>
      </div>

      <C8Table
        :data="integrations"
        :columns="columns"
        :expandable="false"
        :delete-fn="deleteIntegration"
      />
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { ColumnDef } from '@tanstack/vue-table'
import { toast } from 'vue-sonner'
import NewIntegration from '~/components/Integration/NewIntegration.vue'
import { useIntegrationStore } from '~/stores/integration'

const integrationStore = useIntegrationStore()
const loading = ref(false)

const integrations = computed(() => integrationStore.integrations)

onMounted(async () => {
  loading.value = true
  try {
    await integrationStore.load()
    await integrationStore.loadSupportedIntegrations()
  } catch (e: unknown) {
    toast.error('Failed to load integrations')
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
    id: 'actions',
    header: 'Actions',
    cell: () => '',
  },
]

function deleteIntegration() {}
</script>
