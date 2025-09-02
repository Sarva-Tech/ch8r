<script setup lang="ts">
import {
  createColumnHelper,
  getCoreRowModel,
  useVueTable,
} from '@tanstack/vue-table'
import { computed, onMounted } from 'vue'
import type { APIKeyTableRow } from '~/lib/types'
import NewApiKey from '~/components/ApiKey/NewApiKey.vue'
import type { APIKeyItem } from '~/stores/apiKey'
import { Loader2, MessageSquareDot } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { Button } from '~/components/ui/button'

const enablingWidget = ref(false)

const apiKeyStore = useAPIKeyStore()
const widgetStore = useWidgetStore()

const apiKeys = computed(() => apiKeyStore.apiKeys)

const data = computed<APIKeyTableRow[]>(() => {
  return (apiKeys.value || []).map((item: APIKeyItem) => {
    return {
      id: item.id,
      created: item.created,
      name: item.name,
      permissions: item.permissions?.map(p => p.toUpperCase()).sort().join(", "),
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
  try {
    apiKeyStore.load()
  } catch (e) {
    toast.error('Failed to load API keys')
  }

  try {
    widgetStore.load()
  } catch (e) {
    toast.error('Failed to load widget configuration')
  }
})

async function enableWidget() {
  enablingWidget.value = true
  try {
    await widgetStore.enable()
    toast.success('Widget integration enabled')
  } catch (e: unknown) {
    toast.error('Error enabling widget integration')
  } finally {
    enablingWidget.value = false
  }
}

const widget = computed(
  () => widgetStore.widget,
)
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
      <C8Table
        v-else
        :data="data"
        :columns="columns"
        :delete-fn="deleteRow"
        :expandable="false"
      />
    </div>
    <div class="w-full space-y-4 ">
      <div v-if="!widget" class="flex justify-center">
        <Button v-if="enablingWidget" disabled>
          <Loader2 class="w-4 h-4 mr-2 animate-spin" />
        </Button>
        <Button v-else @click="enableWidget">
          <MessageSquareDot class="w-4 h-4 mr-2" /> Enable Widget Integration
        </Button>
      </div>
      <div v-else class="space-y-4">
        <CardTitle> Widget Configuration </CardTitle>
        <div
          class="flex items-center space-x-4 rounded-md border p-4"
        >
          <div class="flex-1 space-y-4">
            <p class="text-sm font-medium leading-none">
              Status
            </p>
            <p class="text-sm text-muted-foreground">
              Enabled
            </p>
            <p class="text-sm font-medium leading-none">
              Token
            </p>
            <p class="text-sm text-muted-foreground">
              {{ widget.token }}
            </p>
            <p class="text-sm font-medium leading-none">
              URL
            </p>
            <p class="text-sm text-muted-foreground">
              {{ widget.widget_url }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
