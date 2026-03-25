<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import NewApiKey from '~/components/ApiKey/NewApiKey.vue'
import type { APIKeyItem } from '~/stores/apiKey'
import { CircleAlert, Key, Calendar, Shield, Trash } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { Alert, AlertDescription, AlertTitle } from '~/components/ui/alert'
import Clipboard from '~/components/Clipboard.vue'
import C8Item from '~/components/C8Item.vue'
import { ItemDescription } from '~/components/ui/item'
import { DropdownMenuItem } from '@/components/ui/dropdown-menu'
import C8Dialog from '~/components/C8Dialog.vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '~/components/ui/card'
import { Label } from '~/components/ui/label'
import { Switch } from '~/components/ui/switch'
import { Input } from '~/components/ui/input'

const enablingWidget = ref(false)
const isDeleteDialogOpen = ref(false)
const apiKeyToDelete = ref<APIKeyItem | null>(null)
const loading = ref(false)

const apiKeyStore = useAPIKeyStore()
const widgetStore = useWidgetStore()
const user = useUserStore()

const apiKeys = computed(() => apiKeyStore.apiKeys)

function deleteAPIKey(apiKey: APIKeyItem) {
  apiKeyStore.delete(apiKey.id).then((response) => {
    if (response?.detail === 'deleted') {
      toast.success('API key deleted')
    }
  }).catch((error) => {
    console.error('Delete error:', error)
    toast.error('Failed to delete API key')
  })
}

function openDeleteDialog(apiKey: APIKeyItem) {
  apiKeyToDelete.value = apiKey
  isDeleteDialogOpen.value = true
}

function confirmDelete() {
  if (apiKeyToDelete.value) {
    deleteAPIKey(apiKeyToDelete.value)
  }
}

function canManageApiKey(apiKey: APIKeyItem) {
  return user.authUser?.id === apiKey.owner
}

onMounted(async () => {
  loading.value = true
  try {
    await apiKeyStore.load()
  } catch (e: unknown) {
    console.error(e)
    toast.error('Failed to load API keys')
  }

  try {
    widgetStore.widget = null
    await widgetStore.load()
  } catch (e: unknown) {
    console.error(e)
    toast.error('Failed to load widget configuration')
  } finally {
    loading.value = false
  }
})

async function toggleWidget() {
  enablingWidget.value = true
  try {
    await widgetStore.toggle()
    if (widgetEnabled.value) {
      toast.success('Widget integration enabled')
    } else {
      toast.success('Widget integration disabled')
    }
  } catch (e: unknown) {
    toast.error('Error configuring widget integration')
  } finally {
    enablingWidget.value = false
  }
}

const widget = computed(
  () => widgetStore.widget,
)

const newAPIKey = computed(() => apiKeyStore.newAPIKey)

const widgetEnabled = computed(() => ['enabled', 'active'].includes(widget.value?.status || 'disabled'))

const integrationCode = computed(() => {
  return widget.value
    ? `
    <iframe
      id="ch8r-widget-iframe"
      src=${widget.value.widget_url}
      width="88"
      height="88"
      style="border: none; position: fixed; bottom: 20px; right: 20px; z-index: 9999; background: transparent;"
    ></iframe>

    <script>
      window.addEventListener("message", (event) => {
        if (event.data?.type === "ch8r-resize") {
          const iframe = document.getElementById("ch8r-widget-iframe")
          if (iframe && event.data.height) {
            iframe.style.height = \`\${event.data.height}px\`
            if (event.data.height > 100) {
              iframe.style.width = "360px"
            } else {
              iframe.style.width = "88px"
            }
          }
        }
      })
    <\/script>
  `
    : ''
})
</script>

<template>
  <div class="flex flex-col h-screen p-4 pt-[72px] pb-[120px] overflow-y-auto space-y-4">
    <div class="w-full space-y-2">
      <div class="flex gap-2 items-center py-4">
        <div class="ml-auto">
          <NewApiKey />
        </div>
      </div>

      <Alert
        v-if="newAPIKey"
        class="py-4"
      >
        <CircleAlert class="h-4 w-4" />
        <AlertTitle>Don't forget to copy your new API Key</AlertTitle>
        <AlertDescription>
          This API Key won't be shown again for your security.
          <div class="relative w-full max-w-sm items-center flex">
            <Input
              v-model="newAPIKey.api_key"
              type="text"
              disabled
              class="pr-10"
            />
            <span
              class="absolute end-0 inset-y-0 flex items-center justify-center text-muted-foreground hover:text-foreground"
            >
              <Clipboard :text="newAPIKey.api_key" />
            </span>
          </div>
        </AlertDescription>
      </Alert>

      <div
        v-if="loading"
        class="text-center py-8"
      >
        Loading...
      </div>

      <div
        v-if="!loading && apiKeys.length === 0"
        class="text-center py-8"
      >
        Your API keys are empty.
      </div>

      <div
        v-if="!loading && apiKeys.length > 0"
        class="space-y-4"
      >
        <C8Item
          v-for="(apiKey, index) in apiKeys"
          :key="index"
          :icon="Key"
          container-class="w-full"
          item-class="w-full"
        >
          <template #title>
            {{ apiKey.name }}
          </template>
          <template #details>
            <ItemDescription>
              <div class="inline-flex space-x-3">
                <div class="flex items-center space-x-1">
                  <Shield class="w-4 h-4" />
                  <div>{{ apiKey.permissions?.map(p => p.toUpperCase()).sort().join(', ') }}</div>
                </div>
                <div class="flex items-center space-x-1">
                  <Calendar class="w-4 h-4" />
                  <div>{{ apiKey.created?.split('T')[0] }}</div>
                </div>
              </div>
            </ItemDescription>
          </template>

          <template #dropdown>
            <DropdownMenuItem
              :disabled="!canManageApiKey(apiKey)"
              class="text-destructive"
              @click="openDeleteDialog(apiKey)"
            >
              <Trash class="h-4 w-4 text-destructive" />
              Delete
            </DropdownMenuItem>
          </template>
        </C8Item>
      </div>

      <C8Dialog
        v-model:open="isDeleteDialogOpen"
        :title="`Delete API Key ${apiKeyToDelete?.name}`"
        :confirm-text="'Delete'"
        :destructive="true"
        @confirm="confirmDelete"
      >
        <template #description>
          <div>
            Are you sure you want to delete the API key <span class="font-bold">{{ apiKeyToDelete?.name }}</span>?
          </div>
        </template>
      </C8Dialog>
    </div>
    <div class="space-y-4">
      <Card class="w-full">
        <CardHeader>
          <CardTitle>Widget Integration</CardTitle>
          <CardDescription>Configure and manage widget integration settings.</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="flex items-center">
            <div class="flex-1 space-y-1">
              <p class="text-sm font-medium leading-none">
                Enable Widget Integration
              </p>
              <p class="text-sm text-muted-foreground">
                Allow widget to be embedded on external websites.
              </p>
            </div>
            <Switch
              v-model="widgetEnabled"
              @click="toggleWidget"
            />
          </div>

          <div v-if="widget && widgetEnabled">
            <div class="grid items-center w-full space-y-4">
              <div class="flex flex-col space-y-1.5">
                <Label>Widget Token</Label>
                <div class="flex justify-between items-center">
                  <Label class="text-sm text-muted-foreground"> {{ widget.token }} </Label>
                  <Clipboard :text="widget.token" />
                </div>
              </div>
              <div class="flex flex-col space-y-1.5">
                <Label>Widget URL</Label>
                <div class="flex justify-between items-center">
                  <Label class="text-sm text-muted-foreground"> {{ widget.widget_url }} </Label>
                  <Clipboard :text="widget.widget_url" />
                </div>
              </div>
              <div class="flex flex-col space-y-3">
                <Label>Integration Code</Label>
                <div class="flex justify-between items-center">
                  <pre
                    class="w-full max-w-full overflow-x-auto whitespace-pre-wrap break-words rounded-md bg-muted p-2 text-sm text-muted-foreground"
                  >
                    <code>{{ integrationCode }}</code>
                  </pre>
                  <Clipboard :text="integrationCode" />
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
