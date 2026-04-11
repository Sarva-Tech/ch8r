<template>
  <C8Loader
    v-if="isLoading"
    container-class="flex justify-center items-center"
  />
  <C8Empty
    v-else-if="integrations.length === 0"
    title="No integrations connected"
    description="Connect an integration to configure version control and project management tools"
  >
    <template #action>
      <ConnectIntegration />
    </template>
  </C8Empty>
  <div
    v-else
    class="space-y-4"
  >
    <div class="flex justify-end">
      <ConnectIntegration />
    </div>
    <ConfigureIntegration
      v-for="type in INTEGRATION_TYPES"
      :key="type.id"
      :config="type"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import ConfigureIntegration from './ConfigureIntegration.vue'
import ConnectIntegration from '~/components/Integration/ConnectIntegration.vue'
import C8Empty from '~/components/C8Empty.vue'
import C8Loader from '~/components/C8Loader.vue'
import { useIntegrationStore } from '~/stores/integration'

const integrationStore = useIntegrationStore()
const { integrations } = storeToRefs(integrationStore)

const isLoading = ref(false)

onMounted(async () => {
  isLoading.value = true
  try {
    await integrationStore.load()
  }
  catch (e: unknown) {
    console.error(e)
  }
  finally {
    isLoading.value = false
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
