<template>
  <div class="space-y-5">
  <C8Select
    :options="textModels"
    :model-value="selectedTextModel"
    label="Text Model"
    @update:model-value="val => selectTextModel(val)"
  />
  <C8Select
    :options="embeddingModels"
    :model-value="selectedEmbeddingModel"
    label="Embedding Model"
    @update:model-value="val => selectEmbeddingModel(val)"
  />
  </div>
</template>
<script lang="ts" setup>
import { computed, ref } from 'vue'
import C8Select from '~/components/C8Select.vue'

const appStore = useApplicationsStore()
const modelStore = useModelStore()
const appModelStore = useAppModelStore()

const models = computed(
  () => modelStore.models
)

const textModels = computed(() =>
  models.value
    .filter(model => model.model_type === 'text')
    .map(model => ({
      label: model.name,
      value: model.uuid,
    }))
)

const embeddingModels = computed(() =>
  models.value
    .filter(model => model.model_type === 'embedding')
    .map(model => ({
      label: model.name,
      value: model.uuid,
    }))
)

const selectedTextModel = ref(null)
const selectedEmbeddingModel = ref(null)

onMounted(() => {
  selectedTextModel.value = textModels.value.find((model) => model.value === appStore.selectedTextModel.uuid)
  selectedEmbeddingModel.value = embeddingModels.value.find((model) => model.value === appStore.selectedEmbeddingModel.uuid)
})

function selectTextModel(val) {
  selectedTextModel.value = val
  appModelStore.setModel(selectedTextModel.value.value, 'text')
}

function selectEmbeddingModel(val) {
  selectedEmbeddingModel.value = val
  appModelStore.setModel(selectedEmbeddingModel.value.value, 'embedding')
}
</script>
