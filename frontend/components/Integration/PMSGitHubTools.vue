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
  <CardFooter class="flex justify-end">
    <C8Button
      label="Save"
      :disabled="disabled"
      :loading="isSubmitting"
      @click="enablePMSGitHub"
    />
  </CardFooter>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { FormControl, FormItem, FormLabel, FormMessage } from '~/components/ui/form'
import RequiredLabel from '~/components/RequiredLabel.vue'
import { usePMSGitHubToolStore } from '~/stores/PMSGitHubTool'
import { toast } from 'vue-sonner'
import { CardFooter } from '~/components/ui/card'

const appConfigStore = useAppConfigurationStore()
const PMSGitHubToolStore = usePMSGitHubToolStore()

const integration = computed(() => appConfigStore.selectedPMS)
const { isSubmitting, meta, validate } = PMSGitHubToolStore.initForm()

const supportedIntegrations = computed(
  () => appConfigStore.supportedIntegrations,
)

const integrationTools = computed(() => {
  if (!integration.value) return null

  const { type, provider } = integration.value
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
  if (!integration.value) {
    toast.error('GitHub integration not found.')
    return
  }

  try {
    const newPMS = await PMSGitHubToolStore.create(integration.value.uuid, integration.value.type)
    if (newPMS) {
      appConfigStore.configuredPMS = newPMS
    }
    toast.success('GitHub Projects configured')
  } catch (e: unknown) {
    toast.error(e?.message || 'Error configuring GitHub Projects')
    PMSGitHubToolStore.setBackendErrors(e.errors)
  }
}

const disabled = computed(() =>
  !meta.value.valid
)

onMounted(() => {
  validate()
})

watch(
  () => integration.value,
  (newValue) => {
    const branchName =
      newValue?.uuid === appConfigStore?.configuredPMS?.uuid
        ? String(appConfigStore?.configuredPMS?.metadata?.branch_name ?? '')
        : ''

    PMSGitHubToolStore.form?.setValues({
      branch_name: branchName,
    })
  },
  { immediate: true }
)
</script>
