<template>
  <div>
    <Card v-if="PMSProfiles.length > 0">
      <CardHeader>
        <CardTitle>Configure Project Management</CardTitle>
        <CardDescription>
          Configure project management tools to be used with response
          generation.
        </CardDescription>
      </CardHeader>
      <CardContent class="space-y-3">
        <div class="space-y-3">
          <C8Select
            v-model="selectedPMS"
            :options="PMSProfiles"
            label="Project Management System"
          />
          <CardDescription>
            Manage tools for the project management integration.
          </CardDescription>
          <component
            :is="dynamicToolsComponent"
            v-if="selectedPMS"
          />
        </div>
      </CardContent>
    </Card>
    <Card v-else>
      <CardHeader>
        <CardDescription>
          No project management profiles are available.
        </CardDescription>
      </CardHeader>
    </Card>
  </div>
</template>

<script lang="ts" setup>
import { computed, ref } from 'vue'
import { toast } from 'vue-sonner'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import PMSGitHubTools from '~/components/Integration/PMSGitHubTools.vue'

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

const PMSProfiles = computed(() =>
  appConfigStore.PMSProfiles.map(integration => ({
    label: integration.name,
    value: integration.uuid,
  })),
)

const selectedPMS = computed({
  get: () => {
    const m = appConfigStore.selectedPMS
    return m ? { label: m.name, value: m.uuid } : null
  },
  set: (val) => {
    appConfigStore.selectedPMS
      = appConfigStore.PMSProfiles?.find(m => m.uuid === val?.value) || null
  },
})

const dynamicToolsComponent = computed(() => {
  if (!appConfigStore.selectedPMS) return null

  const { type, provider } = appConfigStore.selectedPMS
  if (type === 'pms' && provider === 'github') return PMSGitHubTools

  return null
})
</script>
