<template>
  <div class="space-y-3">
    <FormField v-slot="{ componentField }" name="branch_name">
      <FormItem>
        <FormLabel class="flex items-center">
          <div>
            Branch Name
            <RequiredLabel />
          </div>
        </FormLabel>
        <FormControl>
          <Input
            v-bind="componentField"
            placeholder="Sarva-Tech/ch8r"
          />
        </FormControl>
        <FormMessage />
      </FormItem>
    </FormField>

    <div class="ml-auto" @click="enablePMSGitHub">
      <Button>Save</Button>
    </div>
  </div>
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
    <Switch :default-value="true" :disabled="true"/>
  </div>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { FormControl, FormItem, FormLabel, FormMessage } from '~/components/ui/form'
import RequiredLabel from '~/components/RequiredLabel.vue'
import { usePMSGitHubToolStore } from '~/stores/PMSGitHubTool'
import { Button } from '~/components/ui/button'
import { toast } from 'vue-sonner'

const props = defineProps<{
  integration: Integration
}>()

const integrationStore = useIntegrationStore()
const PMSGitHubToolStore = usePMSGitHubToolStore()

PMSGitHubToolStore.initForm()

const supportedIntegrations = computed(
  () => integrationStore.supportedIntegrations,
)

const integrationTools = computed(() => {
  if (!props.integration) return null

  const { type, provider } = props.integration
  const key = `${type}_${provider}`

  return supportedIntegrations.value?.integration_tools[key] || null
})

const tools = computed(() => {
  if (!integrationTools.value) return []
  return Object.entries(integrationTools?.value).map(([key, value]) => ({ key, data: value }))
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

async function enablePMSGitHub() {
  try {
    await PMSGitHubToolStore.create(props.integration.uuid, props.integration.type)
    toast.success('GitHub Projects enabled')
  } catch (e: unknown) {
    PMSGitHubToolStore.setBackendErrors(e.errors)
  }
}

</script>
