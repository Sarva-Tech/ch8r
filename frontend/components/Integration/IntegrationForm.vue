<template>
  <form class="space-y-5">
    <C8Select
      :options="integrationTypes"
      :model-value="selectedIntegrationType"
      label="Type"
      @update:model-value="(val) => (selectedIntegrationType = val)"
    />

    <C8Select
      :options="integrationProviders"
      :model-value="selectedIntegrationProvider"
      label="Type"
      @update:model-value="(val) => (selectedIntegrationProvider = val)"
    />

    <FormField v-slot="{ componentField }" name="name">
      <FormItem>
        <FormLabel class="flex items-center">
          <div>
            Name
            <RequiredLabel />
          </div>
        </FormLabel>
        <FormControl>
          <Input v-bind="componentField" placeholder="Ch8r PMS" />
        </FormControl>
        <FormMessage />
      </FormItem>
    </FormField>

    <component :is="dynamicIntegrationComponent" />
  </form>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

import { Field as FormField } from 'vee-validate'
import C8Select from '~/components/C8Select.vue'
import {
  FormControl,
  FormItem,
  FormLabel,
  FormMessage,
} from '~/components/ui/form'
import RequiredLabel from '~/components/RequiredLabel.vue'
import { useIntegrationStore } from '~/stores/integration'
import PMSGitHub from '~/components/Integration/PMSGitHub.vue'

const integrationStore = useIntegrationStore()

const supportedIntegrations = computed(
  () => integrationStore.supportedIntegrations,
)

const integrationTypes = computed(() =>
  supportedIntegrations.value.supported_integrations.map((type: string) => {
    switch (type) {
      case 'pms':
        return { label: 'Project Management System', value: 'pms' }
      case 'crm':
        return { label: 'Customer Relationship Management', value: 'crm' }
      default:
        return { label: type, value: type }
    }
  }),
)

const selectedIntegrationType = ref(integrationTypes.value[0])

const providerMap: Record<
  string,
  { label: string; icon?: string }
> = {
  github: { label: "GitHub", icon: "github-icon" },
  jira: { label: "Jira", icon: "jira-icon" },
}

const integrationProviders = computed(() => {
  if (!selectedIntegrationType.value) return []

  const providers =
    supportedIntegrations.value.supported_providers[selectedIntegrationType.value.value] || []

  return providers.map((p: string) => {
    const mapped = providerMap[p]
    return {
      label: mapped?.label || p,
      value: p,
      icon: mapped?.icon || undefined,
    }
  })
})

const selectedIntegrationProvider = ref(integrationProviders.value[0])

const { defineField } = integrationStore.initForm()

const [type] = defineField('type')
const [provider] = defineField('provider')

watch(
  selectedIntegrationType,
  (val) => {
    type.value = val.value
  },
  { immediate: true },
)

watch(
  selectedIntegrationProvider,
  (val) => {
    provider.value = val.value
  },
  { immediate: true },
)

const dynamicIntegrationComponent = computed(() => {
  if (
    selectedIntegrationType.value?.value === "pms" &&
    selectedIntegrationProvider.value?.value === "github"
  ) {
    return PMSGitHub
  }

  return null
})
</script>
