<template>
  <div v-if="initialLoading" class="space-y-5">Loading...</div>
  <div v-else class="space-y-5">
    <Tabs default-value="models" class="w-full">
      <TabsList class="grid w-full grid-cols-3">
        <TabsTrigger value="models"> Models </TabsTrigger>
        <TabsTrigger value="project_management">
          Project Management
        </TabsTrigger>
        <TabsTrigger value="notifications"> Notifications </TabsTrigger>
      </TabsList>
      <TabsContent value="models">
        <Card v-if="textModels.length > 0 || embeddingModels.length > 0">
          <CardHeader>
            <CardTitle>Configure Models</CardTitle>
            <CardDescription>
              Configure models to be used with response generation.
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-3">
            <C8Select
              v-if="textModels.length > 0"
              v-model="selectedTextModel"
              :options="textModels"
              label="Text Model"
            />
            <C8Select
              v-if="embeddingModels.length > 0"
              v-model="selectedEmbeddingModel"
              :options="embeddingModels"
              label="Embedding Model"
            />
          </CardContent>
          <CardFooter class="flex justify-end">
            <C8Button
              label="Save"
              :disabled="processing"
              :loading="processing"
              @click="configureModel"
            />
          </CardFooter>
        </Card>
        <Card v-else>
          <CardHeader>
            <CardDescription> No models available. </CardDescription>
          </CardHeader>
        </Card>
      </TabsContent>
      <TabsContent value="project_management">
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
              <component :is="dynamicToolsComponent" v-if="selectedPMS" />
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
      </TabsContent>
      <TabsContent value="notifications">
        <Card v-if="notifications.length > 0">
          <CardHeader>
            <CardTitle>Notifications</CardTitle>
            <CardDescription>
              Configure your notifications here so that you can receive alerts
              during smart escalation.
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-2">
            <C8Multiselect
              v-model="selectedNotifications"
              :options="notifications"
              :multiple="true"
              :preselect-first="false"
              label="Select notification profiles"
              placeholder="Select notification profiles"
            />
          </CardContent>
          <CardFooter class="flex justify-end">
            <C8Button
              label="Save"
              :disabled="processing"
              :loading="processing"
              @click="configureNotifications"
            />
          </CardFooter>
        </Card>
        <Card v-else>
          <CardHeader>
            <CardDescription>
              No notification profiles available.
            </CardDescription>
          </CardHeader>
        </Card>
      </TabsContent>
    </Tabs>
  </div>
</template>
<script lang="ts" setup>
import { computed, ref } from 'vue'
import C8Select from '~/components/C8Select.vue'
import { toast } from 'vue-sonner'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import PMSGitHubTools from '~/components/Integration/PMSGitHubTools.vue'
import type { SelectOption } from '~/lib/types'

const appConfigStore = useAppConfigurationStore()

const initialLoading = ref(false)
const processing = ref(false)

onMounted(async () => {
  initialLoading.value = true
  try {
    await appConfigStore.initialize()
  } catch (e: unknown) {
    toast.error('Failed to load app configuration')
  } finally {
    initialLoading.value = false
  }
})

const textModels = computed(() =>
  appConfigStore.textModels.map((model) => ({
    label: model.name,
    value: model.uuid,
  })),
)
const embeddingModels = computed(() =>
  appConfigStore.embeddingModels.map((model) => ({
    label: model.name,
    value: model.uuid,
  })),
)
const PMSProfiles = computed(() =>
  appConfigStore.PMSProfiles.map((integration) => ({
    label: integration.name,
    value: integration.uuid,
  })),
)

const selectedTextModel = computed({
  get: () => {
    const m = appConfigStore.selectedTextModel
    return m ? { label: m.name, value: m.uuid } : null
  },
  set: (val) => {
    appConfigStore.selectedTextModel =
      appConfigStore.textModels?.find((m) => m.uuid === val?.value) || null
  },
})

const selectedEmbeddingModel = computed({
  get: () => {
    const m = appConfigStore.selectedEmbeddingModel
    return m ? { label: m.name, value: m.uuid } : null
  },
  set: (val) => {
    appConfigStore.selectedEmbeddingModel =
      appConfigStore.embeddingModels?.find((m) => m.uuid === val?.value) || null
  },
})

const selectedPMS = computed({
  get: () => {
    const m = appConfigStore.selectedPMS
    return m ? { label: m.name, value: m.uuid } : null
  },
  set: (val) => {
    appConfigStore.selectedPMS =
      appConfigStore.PMSProfiles?.find((m) => m.uuid === val?.value) || null
  },
})

const dynamicToolsComponent = computed(() => {
  if (!appConfigStore.selectedPMS) return null

  const { type, provider } = appConfigStore.selectedPMS
  if (type === 'pms' && provider === 'github') return PMSGitHubTools

  return null
})

const notifications = computed(() =>
  appConfigStore.notifications.map((n) => ({
    label: n.name ?? '',
    value: n.uuid ?? '',
    selected: n.is_enabled ?? false,
  })),
)

const selectedNotifications = ref<SelectOption[]>([])
watch(
  notifications,
  (newNotifications) => {
    selectedNotifications.value = newNotifications.filter((n) => n.selected)
  },
  { immediate: true },
)

async function configureModel() {
  processing.value = true

  try {
    await appConfigStore.saveModels()
    toast.success('Models configured')
  } catch (e: unknown) {
    toast.error(e?.message || 'Error configuring models')
    console.error(e)
  } finally {
    processing.value = false
  }
}

async function configureNotifications() {
  processing.value = true

  try {
    await appConfigStore.saveNotifications(selectedNotifications.value)
    toast.success('Notifications configured')
  } catch (e: unknown) {
    toast.error(e?.message || 'Error configuring notifications')
    console.error(e)
  } finally {
    processing.value = false
  }
}
</script>
