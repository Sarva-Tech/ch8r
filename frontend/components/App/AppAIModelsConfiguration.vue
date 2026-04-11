<template>
  <C8Loader
    v-if="isLoading"
    container-class="flex justify-center items-center"
  />
  <C8Empty
    v-else-if="AIProviders.length === 0"
    title="No AI providers configured"
    description="Add an AI provider to start configuring AI models for your application"
  >
    <template #action>
      <NewAIProvider />
    </template>
  </C8Empty>
  <div
    v-else
    class="space-y-4"
  >
    <div class="flex justify-end">
      <NewAIProvider />
    </div>
    <ConfigureTextResponseModels />
    <ConfigureEmbeddingModels />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { storeToRefs } from 'pinia'
import ConfigureTextResponseModels from './ConfigureTextResponseModels.vue'
import ConfigureEmbeddingModels from './ConfigureEmbeddingModels.vue'
import NewAIProvider from '~/components/AIProvider/NewAIProvider.vue'
import C8Empty from '~/components/C8Empty.vue'

const AIProviderStore = useAIProviderStore()
const { AIProviders } = storeToRefs(AIProviderStore)

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
