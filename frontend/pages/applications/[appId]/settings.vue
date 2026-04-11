<template>
  <div class="flex flex-col h-screen p-4 pt-[72px] pb-[120px] overflow-y-auto">
    <div class="w-full max-w-4xl mx-auto space-y-6">
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

definePageMeta({
  layout: 'default',
})
</script>
