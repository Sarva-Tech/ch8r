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
        <Card>
          <CardHeader>
            <CardTitle>Configure Models</CardTitle>
            <CardDescription>
              Configure models to be used with response generation.
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-3">
            <C8Select
              v-model="selectedTextModel"
              :options="textModels"
              label="Text Model"
            />
            <C8Select
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
      </TabsContent>
      <TabsContent value="project_management">
        <Card>
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
      </TabsContent>
      <TabsContent value="notifications">
        <Card>
          <CardHeader>
            <CardTitle>Password</CardTitle>
            <CardDescription>
              Change your password here. After saving, you'll be logged out.
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-2">
            <div class="space-y-1">
              <Label for="current">Current password</Label>
              <Input id="current" type="password" />
            </div>
            <div class="space-y-1">
              <Label for="new">New password</Label>
              <Input id="new" type="password" />
            </div>
          </CardContent>
          <CardFooter>
            <Button>Save password</Button>
          </CardFooter>
        </Card>
      </TabsContent>
    </Tabs>
  </div>
</template>
<script lang="ts" setup>
import { computed, ref } from 'vue'
import C8Select from '~/components/C8Select.vue'
import { toast } from 'vue-sonner'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import PMSGitHubTools from '~/components/Integration/PMSGitHubTools.vue'
import { usePMSGitHubToolStore } from '~/stores/PMSGitHubTool'

const appConfigStore = useAppConfigurationStore()
const PMSGitHubToolStore = usePMSGitHubToolStore()

PMSGitHubToolStore.initForm()
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
    value: integration.uuid
  })),
)

const selectedTextModel = computed({
  get: () => {
    const m = appConfigStore.selectedTextModel
    return m ? { label: m.name, value: m.uuid } : null
  },
  set: (val) => {
    appConfigStore.selectedTextModel = appConfigStore.textModels?.find(
      (m) => m.uuid === val?.value,
    ) || null
  },
})

const selectedEmbeddingModel = computed({
  get: () => {
    const m = appConfigStore.selectedEmbeddingModel
    return m ? { label: m.name, value: m.uuid } : null
  },
  set: (val) => {
    appConfigStore.selectedEmbeddingModel = appConfigStore.embeddingModels?.find(
      (m) => m.uuid === val?.value,
    ) || null
  },
})

const selectedPMS = computed({
  get: () => {
    const m = appConfigStore.selectedPMS
    return m ? { label: m.name, value: m.uuid } : null
  },
  set: (val) => {
    appConfigStore.selectedPMS = appConfigStore.PMSProfiles?.find(
      (m) => m.uuid === val?.value,
    ) || null
  },
})

const dynamicToolsComponent = computed(() => {
  if (!appConfigStore.selectedPMS) return null

  const { type, provider } = appConfigStore.selectedPMS
  if (type === 'pms' && provider === 'github') return PMSGitHubTools

  return null
})


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
</script>
