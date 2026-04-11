<template>
  <div class="w-full space-y-2">
    <C8Loader
      v-if="loading"
      container-class="flex justify-center items-center py-12"
    />

    <C8Empty
      v-else-if="AIProviders.length === 0"
      :icon="Cpu"
      title="No AI providers configured"
      description="Add an AI provider to start configuring AI models for your application"
    >
      <template #action>
        <NewAIProvider />
      </template>
    </C8Empty>

    <template v-else>
      <div class="flex gap-2 items-center py-4">
        <div class="ml-auto">
          <NewAIProvider />
        </div>
      </div>

      <ConfigureTextResponseModels />
      <ConfigureEmbeddingModels />
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { storeToRefs } from 'pinia'
import { Cpu } from 'lucide-vue-next'
import ConfigureTextResponseModels from './ConfigureTextResponseModels.vue'
import ConfigureEmbeddingModels from './ConfigureEmbeddingModels.vue'
import NewAIProvider from '~/components/AIProvider/NewAIProvider.vue'
import C8Empty from '~/components/C8Empty.vue'
import C8Loader from '~/components/C8Loader.vue'

const AIProviderStore = useAIProviderStore()
const { AIProviders } = storeToRefs(AIProviderStore)

const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    await AIProviderStore.load()
  }
  catch (e: unknown) {
    console.error(e)
  }
  finally {
    loading.value = false
  }
})
</script>
