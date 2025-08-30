<template>
  <div
    v-for="tool in tools"
    :key="tool.key"
    class="flex items-center space-x-4 rounded-md border p-4"
  >
    <div class="flex-1 space-y-1">
      <p class="text-sm font-medium leading-none">
        {{ getToolInfo(tool.key).label }}
      </p>
      <p class="text-sm text-muted-foreground">
        {{ getToolInfo(tool.key).description }}
      </p>
    </div>
    <Switch />
  </div>
</template>
<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  integration: Integration
}>()

const integrationStore = useIntegrationStore()

const supportedIntegrations = computed(
  () => integrationStore.supportedIntegrations,
)

const integrationTools = computed(() => {
  if (!props.integration) return null

  const { type, provider } = props.integration
  const key = `${type}_${provider}`

  return supportedIntegrations.value.integration_tools[key] || null
})

const tools = computed(() => {
  if (!integrationTools.value) return []
  return Object.entries(integrationTools.value).map(([key, value]) => ({ key, data: value }))
})

function getToolInfo(toolKey: string) {
  switch (toolKey) {
    case 'list_github_issues':
      return {
        label: 'Search GitHub Issues',
        description: 'Search and view GitHub issues for the project based on the user’s query.',
        icon: ''
      }
    case 'create_github_issue':
      return { label: 'Create GitHub Issue', icon: '', description: 'Open a GitHub issue from the user’s request or feedback.' }
    default:
      return { label: toolKey, icon: '' }
  }
}
</script>
