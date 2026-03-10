<template>
  <div
    v-if="initialLoading"
    class="space-y-5"
  >
    Loading...
  </div>
  <div
    v-else
    class="space-y-5"
  >
    <Tabs
      default-value="models"
      class="w-full"
    >
      <TabsList class="grid w-full grid-cols-3">
        <TabsTrigger
          v-for="tab in tabs"
          :key="tab.value"
          :value="tab.value"
        >
          {{ tab.label }}
        </TabsTrigger>
      </TabsList>
      <TabsContent
        v-for="tab in tabs"
        :key="tab.value"
        :value="tab.value"
      >
        <component :is="getTabComponent(tab.value)" />
      </TabsContent>
    </Tabs>
  </div>
</template>

<script lang="ts" setup>
import { toast } from 'vue-sonner'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

import AppAIModelsConfiguration from '~/components/App/AppAIModelsConfiguration.vue'
import AppPMSConfiguration from '~/components/App/AppPMSConfiguration.vue'
import AppNotificationConfiguration from '~/components/App/AppNotificationConfiguration.vue'

const getTabComponent = (tab: string) => {
  switch (tab) {
    case 'models':
      return AppAIModelsConfiguration
    case 'project_management':
      return AppPMSConfiguration
    case 'notifications':
      return AppNotificationConfiguration
    default:
      return null
  }
}

const tabs = [
  { label: 'AI Models', value: 'models' },
  { label: 'Project Management', value: 'project_management' },
  { label: 'Notifications', value: 'notifications' }
]

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
