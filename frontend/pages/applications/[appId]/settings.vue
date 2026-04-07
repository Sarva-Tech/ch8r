<template>
  <div class="flex flex-col h-screen p-4 pt-[72px] pb-[120px] overflow-y-auto">
    <div class="w-full max-w-4xl mx-auto space-y-6">
      <div class="flex items-center gap-2">
        <h1 class="text-2xl font-semibold">
          {{ pageTitle }}
        </h1>
      </div>
      <ConfigureApp :active-tab="activeTab" />
    </div>
  </div>
</template>

<script setup lang="ts">
import ConfigureApp from '~/components/App/ConfigureApp.vue'

const route = useRoute()

const validTabs = ['models', 'integrations', 'prompt', 'notifications']

const activeTab = computed(() => {
  const tab = route.query.tab as string
  return validTabs.includes(tab) ? tab : 'models'
})

const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    models: 'AI Models',
    integrations: 'Integrations',
    prompt: 'Agent Configuration',
    notifications: 'Notifications',
  }
  return titles[activeTab.value] || 'Application Settings'
})

definePageMeta({
  layout: 'default',
})
</script>
