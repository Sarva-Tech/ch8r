<script setup lang="ts">
import type { ColumnDef } from '@tanstack/vue-table'
import { ref, computed, onMounted } from 'vue'
import { useIntegrationStore } from '~/stores/integration'
import { useApplicationStore } from '~/stores/application'
import type { Integration, AppIntegration } from '~/types/integration'

const integrationStore = useIntegrationStore()
const applicationStore = useApplicationStore()

const route = useRoute()
const appId = route.params.appId as string

const isLoading = ref(false)
const showGitHubSetup = ref(false)
const showIntegrationDetails = ref(false)
const selectedIntegration = ref<Integration | null>(null)
const selectedAppIntegration = ref<AppIntegration | null>(null)

const integrations = computed(() => integrationStore.integrations)
const appIntegrations = computed(() => integrationStore.appIntegrations)

const data = computed(() => {
  return appIntegrations.value.map((appInt: AppIntegration) => ({
    id: appInt.id,
    name: appInt.integration.name,
    provider: appInt.integration.provider,
    type: appInt.integration.type,
    status: 'connected', // TODO: Add actual status tracking
    configured: true,
    created_at: appInt.created_at
  }))
})

const columns: ColumnDef<unknown, string | number>[] = [
  {
    id: 'expander',
    header: '',
    cell: () => '',
  },
  {
    accessorKey: 'name',
    header: 'Integration Name',
    cell: (info) => info.getValue(),
  },
  {
    accessorKey: 'provider',
    header: 'Provider',
    cell: (info) => {
      const provider = info.getValue() as string
      return provider.charAt(0).toUpperCase() + provider.slice(1)
    },
  },
  {
    accessorKey: 'type',
    header: 'Type',
    cell: (info) => {
      const type = info.getValue() as string
      return type === 'pms' ? 'Project Management' : type.charAt(0).toUpperCase() + type.slice(1)
    },
  },
  {
    accessorKey: 'status',
    header: 'Status',
    cell: (info) => {
      const status = info.getValue() as string
      return status.charAt(0).toUpperCase() + status.slice(1)
    },
  },
  {
    id: 'actions',
    header: 'Actions',
    cell: ({ row }) => {
      const integration = row.original as any
      return h('div', { class: 'flex gap-2' }, [
        h('button', {
          class: 'px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700',
          onClick: () => openIntegrationDetails(integration)
        }, 'Configure'),
        h('button', {
          class: 'px-2 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700',
          onClick: () => deleteIntegration(integration.id)
        }, 'Delete')
      ])
    },
  },
]

const loadIntegrations = async () => {
  try {
    isLoading.value = true
    await Promise.all([
      integrationStore.loadIntegrations(),
      integrationStore.loadAppIntegrations(appId)
    ])
  } catch (error) {
    console.error('Failed to load integrations:', error)
  } finally {
    isLoading.value = false
  }
}

const openIntegrationDetails = (integration: any) => {
  selectedIntegration.value = integration
  selectedAppIntegration.value = appIntegrations.value.find(
    (appInt: AppIntegration) => appInt.id === integration.id
  )
  showIntegrationDetails.value = true
}

const deleteIntegration = async (id: number) => {
  if (!confirm('Are you sure you want to delete this integration?')) return

  try {
    await integrationStore.deleteAppIntegration(id)
    await loadIntegrations()

    const toast = useToast()
    toast.add({
      title: 'Integration Deleted',
      description: 'The integration has been deleted successfully.',
      color: 'green'
    })
  } catch (error) {
    const toast = useToast()
    toast.add({
      title: 'Delete Failed',
      description: 'Failed to delete the integration.',
      color: 'red'
    })
  }
}

const handleGitHubSetupSuccess = () => {
  showGitHubSetup.value = false
  loadIntegrations()
}

const handleIntegrationUpdated = () => {
  showIntegrationDetails.value = false
  loadIntegrations()
}

onMounted(() => {
  loadIntegrations()
})
</script>

<template>
  <div class="flex flex-col h-screen p-4 pt-[72px] pb-[120px] overflow-y-auto">
    <div class="w-full space-y-4">
      <!-- Header -->
      <div class="flex justify-between items-center py-4">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
            Integrations
          </h1>
          <p class="text-gray-600 dark:text-gray-300">
            Manage external integrations for your application
          </p>
        </div>

        <div class="flex gap-2">
          <UButton
            icon="i-simple-icons-github"
            @click="showGitHubSetup = true"
          >
            Add GitHub Integration
          </UButton>
        </div>
      </div>

      <div v-if="isLoading" class="text-center py-8">
        <UIcon name="i-heroicons-arrow-path-16-solid" class="animate-spin text-2xl text-blue-600" />
        <p class="mt-2 text-gray-600 dark:text-gray-300">Loading integrations...</p>
      </div>

      <div
        v-else-if="data.length === 0"
        class="text-center py-8"
      >
        <UIcon name="i-heroicons-link-16-solid" class="mx-auto text-4xl text-gray-400 mb-4" />
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
          No integrations configured
        </h3>
        <p class="text-gray-500 dark:text-gray-400 mb-4">
          Connect external services to enhance your application capabilities.
        </p>
        <UButton
          icon="i-simple-icons-github"
          @click="showGitHubSetup = true"
        >
          Add GitHub Integration
        </UButton>
      </div>

      <C8Table
        v-else
        :data="data"
        :columns="columns"
        :expandable="true"
      />
    </div>

    <UModal v-model="showGitHubSetup" :ui="{ width: 'sm:max-w-4xl' }">
      <div class="p-6">
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
            GitHub Integration Setup
          </h2>
          <UButton
            icon="i-heroicons-x-mark-20-solid"
            variant="ghost"
            color="gray"
            size="sm"
            square
            @click="showGitHubSetup = false"
          />
        </div>

        <GitHubIntegrationSetup
          :app-id="appId"
          @success="handleGitHubSetupSuccess"
          @cancel="showGitHubSetup = false"
          @integration-created="handleIntegrationUpdated"
        />
      </div>
    </UModal>

    <UModal v-model="showIntegrationDetails" :ui="{ width: 'sm:max-w-2xl' }">
      <UCard>
        <template #header>
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
              Integration Configuration
            </h3>
            <UButton
              icon="i-heroicons-x-mark-20-solid"
              variant="ghost"
              color="gray"
              size="sm"
              square
              @click="showIntegrationDetails = false"
            />
          </div>
        </template>

        <div v-if="selectedIntegration" class="space-y-6">
          <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
            <h4 class="font-medium text-gray-900 dark:text-white mb-2">
              {{ selectedIntegration.name }}
            </h4>
            <div class="space-y-1 text-sm text-gray-600 dark:text-gray-300">
              <p><strong>Provider:</strong> {{ selectedIntegration.provider }}</p>
              <p><strong>Type:</strong> {{ selectedIntegration.type }}</p>
              <p><strong>Status:</strong> {{ selectedIntegration.status }}</p>
            </div>
          </div>

          <div v-if="selectedIntegration.provider === 'github'" class="space-y-4">
            <h4 class="font-medium text-gray-900 dark:text-white">
              GitHub Configuration
            </h4>

            <div class="space-y-3">
              <div>
                <C8Label for="github-token">GitHub Token</C8Label>
                <div class="relative">
                  <C8Input
                    id="github-token"
                    type="password"
                    placeholder="Enter your GitHub token"
                    class="pr-20"
                  />
                  <UButton
                    icon="i-heroicons-arrow-top-right-on-square-16-solid"
                    variant="outline"
                    size="xs"
                    class="absolute right-2 top-1/2 transform -translate-y-1/2"
                    @click="window.open('https://github.com/settings/tokens', '_blank')"
                  >
                    Get Token
                  </UButton>
                </div>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  Your GitHub Personal Access Token will be encrypted and stored securely.
                </p>
              </div>

              <div>
                <C8Label for="github-repos">Repositories</C8Label>
                <p class="text-sm text-gray-600 dark:text-gray-300 mb-2">
                  Select repositories to ingest data from:
                </p>
                <div class="space-y-2 max-h-40 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                  <p class="text-sm text-gray-500 dark:text-gray-400">
                    Repository selection will be available after token validation.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div class="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <UButton
              variant="ghost"
              color="gray"
              @click="showIntegrationDetails = false"
            >
              Cancel
            </UButton>
            <UButton
              @click="handleIntegrationUpdated"
            >
              Save Configuration
            </UButton>
          </div>
        </div>
      </UCard>
    </UModal>
  </div>
</template>
