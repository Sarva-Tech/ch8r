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
import { computed } from 'vue'
import type { ColumnDef } from '@tanstack/vue-table'
import NewIntegration from '~/components/Integration/NewIntegration.vue'
import { useIntegrationStore } from '~/stores/integration'

const integrationStore = useIntegrationStore()
const user = useUserStore()

await integrationStore.load()
await integrationStore.loadSupportedIntegrations()

const integrations = computed(() =>
  integrationStore.integrations.map((i) => ({
    ...i,
    canDelete: i.owner === user.authUser.id,
    canUpdate: false,
  }))
)


const columns: ColumnDef<unknown, string | number>[] = [
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

function deleteIntegration(uuid: string) {
  integrationStore.delete(uuid)
}
</script>
