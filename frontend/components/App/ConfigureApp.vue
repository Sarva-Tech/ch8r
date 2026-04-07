<template>
  <div
    v-if="initialLoading"
    class="space-y-5"
  >
    Loading...
  </div>
  <div v-else>
    <component :is="getTabComponent(activeTab)" />
  </div>
</template>

<script lang="ts" setup>
import { toast } from 'vue-sonner'

import AppAIModelsConfiguration from '~/components/App/AppAIModelsConfiguration.vue'
import AppIntegrationsConfiguration from '~/components/App/AppIntegrationsConfiguration.vue'
import AppNotificationConfiguration from '~/components/App/AppNotificationConfiguration.vue'
import AppPromptConfiguration from '~/components/App/AppPromptConfiguration.vue'

const props = defineProps<{
  activeTab: string
}>()

const getTabComponent = (tab: string) => {
  switch (tab) {
    case 'models':
      return AppAIModelsConfiguration
    case 'integrations':
      return AppIntegrationsConfiguration
    case 'notifications':
      return AppNotificationConfiguration
    case 'prompt':
      return AppPromptConfiguration
    default:
      return AppAIModelsConfiguration
  }
}

const appConfigStore = useAppConfigurationStore()
const AIProviderModelsStore = useAIProviderModelsStore()

const initialLoading = ref(false)

onMounted(async () => {
  initialLoading.value = true
  try {
    await appConfigStore.initialize()
    await AIProviderModelsStore.load()
  } catch (e: unknown) {
    toast.error('Failed to load app configuration')
  } finally {
    initialLoading.value = false
  }
})
</script>
