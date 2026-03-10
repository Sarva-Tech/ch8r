<template>
  <C8Loader
    v-if="isLoading"
    container-class="flex justify-center items-center"
  />
  <div class="space-y-4">
    <ConfigureTextResponseModels />
    <ConfigureEmbeddingModels />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ConfigureTextResponseModels from './ConfigureTextResponseModels.vue'
import ConfigureEmbeddingModels from './ConfigureEmbeddingModels.vue'

const AIProviderStore = useAIProviderStore()

const isLoading = ref(false)

onMounted(async () => {
  isLoading.value = true
  try {
    await AIProviderStore.load()
  }
  catch (e: unknown) {
    console.error(e)
  }
  finally {
    isLoading.value = false
  }
})
</script>
