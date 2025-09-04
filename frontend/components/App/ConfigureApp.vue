<template>
  <div v-if="loading" class="space-y-5">
    Loading...
  </div>
  <div
    v-else
    class="space-y-5"
  >
    <C8Select
      :options="textModels"
      :model-value="selectedTextModel"
      label="Text Model"
      @update:model-value="(val) => selectTextModel(val)"
    />
    <C8Select
      :options="embeddingModels"
      :model-value="selectedEmbeddingModel"
      label="Embedding Model"
      @update:model-value="(val) => selectEmbeddingModel(val)"
    />
    <div class="space-y-3">
      <C8Select
        :options="pmsProfileOptions"
        :model-value="selectedPMSProfile"
        label="Project Management System"
        @update:model-value="(val) => selectedPMSProfile = val"
      />
      <CardDescription>
        Manage tools for the project management integration.
      </CardDescription>
      <component
        :is="dynamicToolsComponent"
        v-if="selectedPMS"
        :integration="selectedPMS"
      />
    </div>
  </div>
</template>
<script lang="ts" setup>
import { computed, ref } from 'vue'
import C8Select from '~/components/C8Select.vue'
import type { NullableSelectOption } from '~/lib/types'
import { toast } from 'vue-sonner'
import PMSGitHubTools from '~/components/Integration/PMSGitHubTools.vue'

const appStore = useApplicationsStore()
const modelStore = useModelStore()
const appModelStore = useAppModelStore()
const integrationStore = useIntegrationStore()
const notificationProfiles = useNotificationProfileStore()

const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    await modelStore.load()
    await integrationStore.load()
    await integrationStore.loadSupportedIntegrations()
    await notificationProfiles.load()
  } catch (e: unknown) {
    toast.error('Failed to load app configuration')
  } finally {
    loading.value = false
  }
})

const models = computed(() => modelStore.models)
const integrations = computed(() => integrationStore.integrations)

const textModels = computed(() =>
  models.value
    .filter((model) => model.model_type === 'text')
    .map((model) => ({
      label: model.name,
      value: model.uuid,
    })),
)

const embeddingModels = computed(() =>
  models.value
    .filter((model) => model.model_type === 'embedding')
    .map((model) => ({
      label: model.name,
      value: model.uuid,
    })),
)

const availablePMSProfiles = computed(() =>
  integrations.value.filter((i) => i.type === 'pms'),
)

const pmsProfileOptions = computed(() => {
  return availablePMSProfiles.value.map((p: Integration) => {
    return {
      label: p.name,
      value: p.uuid,
      icon: '',
    }
  })
})

const dynamicToolsComponent = computed(() => {
  if (!selectedPMS.value) return null

  const { type, provider } = selectedPMS.value

  if (type === 'pms' && provider === 'github') return PMSGitHubTools

  return null
})

const selectedTextModel = ref<NullableSelectOption>(null)
const selectedEmbeddingModel = ref<NullableSelectOption>(null)
const selectedPMSProfile = ref<NullableSelectOption>(null)
const selectedPMS = ref<Integration | null>(null)

function selectTextModel(val: NullableSelectOption) {
  selectedTextModel.value = val
  const modelId = val?.value

  if (!modelId) return

  appModelStore.setModel(modelId, 'text')
}

function selectEmbeddingModel(val: NullableSelectOption) {
  selectedEmbeddingModel.value = val
  const modelId = val?.value

  if (!modelId) return

  appModelStore.setModel(modelId, 'embedding')
}

watch(textModels, (val) => {
  selectedTextModel.value =
    val.find((model) => model.value === appStore.selectedTextModel?.uuid) ||
    null
})

watch(embeddingModels, (val) => {
  selectedEmbeddingModel.value =
    val.find(
      (model) => model.value === appStore.selectedEmbeddingModel?.uuid,
    ) || null
})

watch(selectedPMSProfile, (val) => {
  selectedPMS.value =
    availablePMSProfiles.value.find(
      (profile) => profile.uuid === val?.value,
    ) || null
})

watch(pmsProfileOptions, (val) => {
  selectedPMSProfile.value = val[0]
})
</script>
