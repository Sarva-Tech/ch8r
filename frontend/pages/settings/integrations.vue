<template>
  <div class="flex flex-col min-h-0 flex-1 p-4 pt-[72px] pb-[120px] overflow-y-auto">
    <div class="w-full space-y-2">
      <div class="flex gap-2 items-center py-4">
        <div class="ml-auto">
          <ConnectIntegration @connected="integrationStore.load()" />
        </div>
      </div>

      <div
        v-for="supported in integrationStore.supportedIntegrations"
        :key="supported.id"
        class="space-y-2"
      >
        <template v-if="getConnectedAll(supported.id).length > 0">
          <C8Item
            v-for="integration in getConnectedAll(supported.id)"
            :key="integration.uuid"
            :icon="getIntegrationIcon(supported.id)"
            container-class="w-full"
            item-class="w-full"
          >
            <template #title>
              <div class="flex items-center gap-2">
                {{ integration.name }}
              </div>
            </template>
            <template #details>
              <ItemDescription>
                <div class="inline-flex space-x-3">
                  <div class="flex items-center space-x-1">
                    <ServerCog class="w-4 h-4" />
                    <div>{{ integrationProviderDetails(integration.provider) }}</div>
                  </div>
                  <div
                    v-if="integration.supported_types?.includes('version_control')"
                    class="flex items-center space-x-1"
                  >
                    <FolderGit class="w-4 h-4" />
                    <div>Version Control</div>
                  </div>
                  <div
                    v-if="integration.supported_types?.includes('project_management')"
                    class="flex items-center space-x-1"
                  >
                    <SquareKanban class="w-4 h-4" />
                    <div>Project Management</div>
                  </div>
                  <div
                    v-if="(integration.metadata as any)?.account?.login"
                    class="flex items-center space-x-1"
                  >
                    <Link class="w-4 h-4" />
                    <a
                      :href="(integration.metadata as any).account.html_url"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="hover:underline"
                    >
                      {{ (integration.metadata as any).account.login }}
                    </a>
                  </div>
                </div>
              </ItemDescription>
            </template>
            <template #dropdown>
              <DropdownMenuItem @click="updateIntegration(integration)">
                <PencilLine class="h-4 w-4" />
                Update
              </DropdownMenuItem>
              <DropdownMenuItem
                class="text-destructive"
                @click="openDeleteDialog(integration)"
              >
                <Trash class="h-4 w-4 text-destructive" />
                Delete
              </DropdownMenuItem>
            </template>
          </C8Item>
        </template>
      </div>

      <div
        v-if="integrationStore.integrations.length === 0"
        class="text-center py-12 text-sm text-muted-foreground"
      >
        No integrations connected yet. Click "Add New Integration" to get started.
      </div>

      <UpdateIntegration ref="updateSlide" />

      <C8Dialog
        v-model:open="isDeleteDialogOpen"
        :title="`Delete ${integrationToDelete?.name}`"
        confirm-text="Delete"
        :destructive="true"
        @confirm="confirmDelete"
      >
        <template #description>
          Are you sure you want to delete
          <span class="font-bold">{{ integrationToDelete?.name }}</span>?
          Any applications using this integration will lose access.
        </template>
      </C8Dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useIntegrationStore } from '~/stores/integration'
import ConnectIntegration from '~/components/Integration/ConnectIntegration.vue'
import UpdateIntegration from '~/components/Integration/UpdateIntegration.vue'
import { useIntegrationIcon } from '~/composables/useIntegrationIcon'
import C8Dialog from '~/components/C8Dialog.vue'
import C8Item from '~/components/C8Item.vue'
import { ItemDescription } from '~/components/ui/item'
import { DropdownMenuItem } from '@/components/ui/dropdown-menu'
import { PencilLine, Trash, Link, ServerCog, FolderGit, SquareKanban } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import type { Integration } from '~/stores/integration'

const integrationStore = useIntegrationStore()
const updateSlide = ref<InstanceType<typeof UpdateIntegration> | null>(null)
const isDeleteDialogOpen = ref(false)
const integrationToDelete = ref<Integration | null>(null)

onMounted(async () => {
  try {
    await integrationStore.load()
  }
  catch (e) {
    toast.error('Failed to load integrations')
  }
})

function getIntegrationIcon(provider: string) {
  return useIntegrationIcon(provider).value
}

function integrationProviderDetails(provider: string): string {
  switch (provider.toLowerCase()) {
    case 'github':
      return 'GitHub'
    default:
      return provider.charAt(0).toUpperCase() + provider.slice(1)
  }
}

function getConnectedAll(providerId: string): Integration[] {
  return integrationStore.integrations.filter(i => i.provider === providerId)
}

function updateIntegration(integration: Integration) {
  updateSlide.value?.open(integration)
}

function openDeleteDialog(integration: Integration) {
  integrationToDelete.value = integration
  isDeleteDialogOpen.value = true
}

function confirmDelete() {
  if (!integrationToDelete.value) return
  integrationStore.delete(integrationToDelete.value.uuid).then((response) => {
    if (response?.detail === 'deleted') {
      toast.success('Integration deleted')
    }
  })
}
</script>
