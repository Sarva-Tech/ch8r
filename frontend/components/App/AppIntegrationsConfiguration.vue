<template>
  <div class="flex flex-col min-h-0 flex-1 p-4 pb-[120px] overflow-y-auto">
    <div class="w-full space-y-2">
      <C8Loader
        v-if="loading"
        container-class="flex justify-center items-center py-12"
      />

      <C8Empty
        v-else-if="integrations.length === 0"
        :icon="Plug"
        title="No integrations connected"
        description="Connect an integration to configure version control and project management tools"
      >
        <template #action>
          <ConnectIntegration />
        </template>
      </C8Empty>

      <template v-else>
        <div class="flex gap-2 items-center py-4">
          <div class="ml-auto">
            <ConnectIntegration />
          </div>
        </div>

        <ConfigureIntegration
          v-for="type in INTEGRATION_TYPES"
          :key="type.id"
          :config="type"
        />
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { Plug } from 'lucide-vue-next'
import ConfigureIntegration from './ConfigureIntegration.vue'
import ConnectIntegration from '~/components/Integration/ConnectIntegration.vue'
import C8Empty from '~/components/C8Empty.vue'
import C8Loader from '~/components/C8Loader.vue'
import { useIntegrationStore } from '~/stores/integration'

const integrationStore = useIntegrationStore()
const { integrations } = storeToRefs(integrationStore)

const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    await integrationStore.load()
  }
  catch (e: unknown) {
    console.error(e)
  }
  finally {
    loading.value = false
  }
})

const INTEGRATION_TYPES = [
  {
    id: 'version_control',
    title: 'Version Control',
    description: 'Select the version control integration and repository to connect.',
    requiresRepo: true,
    successMessage: 'Version control integration configured',
  },
  {
    id: 'project_management',
    title: 'Project Management',
    description: 'Select the project management integration to connect.',
    requiresRepo: true,
    successMessage: 'Project management integration configured',
  },
]
</script>
